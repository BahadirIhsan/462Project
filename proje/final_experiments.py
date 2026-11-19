"""Phase 4/5 final experiments (English figures for the final report and slides).

1. Siamese embedding hyper-parameters: chosen on the 10 TUNING subjects only (net trained on the 41 evaluation
   subjects, validated with protocol C2 on the tuning subjects; the evaluated people are never in training).
2. Cross-fitting: the 41 evaluation subjects are split into 5 folds. For fold f the embedding is trained on the
   tuning subjects + the other 4 folds; fold f is evaluated with impostors taken from fold f only (impostors seen in
   training must not be reused as test impostors). All detectors are also run under this fold protocol (fair table).
3. Score-level fusion of detectors (per-user z-normalisation from enrolment-only leave-one-session-out scores).
4. Score distributions, English DET curves, error analysis (worst users, wolves, feature drift vs. EER).
Outputs: results/final.json, results/fin_*.png, results/siamese_demo.json (embedding trained on all 51 CMU subjects
for the localhost demo; demo users are never CMU subjects).
Run: .venv/bin/python final_experiments.py   (~3-5 min on a laptop CPU)
"""
import json, os, itertools
import numpy as np
from scipy.stats import spearmanr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from keystroke.data import load_cmu, to_arrays, split_tuning_eval
from keystroke.detectors import make_detectors
from keystroke.preprocess import feature_groups
from keystroke.metrics import eer, fnmr_at_fmr, bootstrap_ci, det_curve_grid
from keystroke.siamese import Embedder, SiameseDetector
from keystroke import experiments as ex

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
COL = {"Manhattan": "#8a8f98", "Scaled Manhattan": "#1b7f3b", "Mahalanobis": "#c0392b", "One-class SVM": "#1f5fbf",
       "Siamese embedding": "#8e44ad", "Fusion (SM+SVM+Siamese)": "#e67e22"}

df, cols = load_cmu()
data = to_arrays(df, cols)
H, DD, UD = feature_groups(cols)
users = sorted(data)
tune_users, eval_users = split_tuning_eval(users, 10, seed=0)
prev = json.load(open(os.path.join(OUT, "results.json")))
svm_params = prev["svm_params"]
base = make_detectors(svm_params)
F = {}

# ---------------------------------------------------------------- 1. Siamese tuning (tuning subjects only)
def c2_mean_eer(res):
    return float(np.mean([eer(g.ravel(), i.ravel()) for g, i in res.values()]))

grid = {}
for (dim, hidden, steps) in itertools.product((32, 64, 128), (128, 256), (300, 600, 1500)):
    e = Embedder(H, DD, dim=dim, hidden=hidden, steps=steps).fit(data, eval_users)
    grid[f"dim={dim},hidden={hidden},steps={steps}"] = c2_mean_eer(ex.cond_cross(data, tune_users, lambda: SiameseDetector(e)))
    print("tune", dim, hidden, steps, round(grid[f"dim={dim},hidden={hidden},steps={steps}"], 4), flush=True)
best = min(grid, key=grid.get)
SIAM = {k: int(v) for k, v in (kv.split("=") for kv in best.split(","))}
sm_tune = c2_mean_eer(ex.cond_cross(data, tune_users, base["Scaled Manhattan"]))
F["siamese_tuning"] = {"grid": grid, "best": SIAM, "best_tune_eer": grid[best], "scaled_manhattan_tune_eer": sm_tune}
print("Siamese chosen:", SIAM, flush=True)

# ---------------------------------------------------------------- 2. Cross-fitting over 5 folds
rng = np.random.default_rng(0)
perm = rng.permutation(eval_users)
folds = [sorted(perm[i::5].tolist()) for i in range(5)]
F["folds"] = folds
names = list(base) + ["Siamese embedding"]
C1, C2, DR, LOSO, LOSS = {n: {} for n in names}, {n: {} for n in names}, {n: {t: {} for t in range(8)} for n in names}, {n: {} for n in names}, []


def loso_stats(factory, X4):
    """Enrolment-only genuine statistics: leave-one-enrolment-session-out scores (no impostor, no test data)."""
    s = np.concatenate([factory().fit(np.delete(X4, k, 0).reshape(-1, X4.shape[-1])).score(X4[k]) for k in range(4)])
    return s.mean(), s.std() + 1e-9, s


for fi, fold in enumerate(folds):
    train_u = tune_users + [u for u in eval_users if u not in fold]
    emb = Embedder(H, DD, **SIAM).fit(data, train_u)
    LOSS.append(emb.losses)
    facs = dict(base)
    facs["Siamese embedding"] = lambda emb=emb: SiameseDetector(emb)
    for n, f in facs.items():
        C1[n].update(ex.cond_within(data, fold, f))
        C2[n].update(ex.cond_cross(data, fold, f))
        d = ex.cond_drift(data, fold, f)
        for t in range(8):
            DR[n][t].update(d[t])
        for u in fold:
            LOSO[n][u] = loso_stats(f, data[u][:4])
    print("fold", fi + 1, "done", flush=True)

flat = lambda res: {u: (g.reshape(-1), i.reshape(-1)) for u, (g, i) in res.items()}


def summarise(res):
    e = [eer(g, i) for g, i in res.values()]
    m, lo, hi = bootstrap_ci(e)
    return {"eer_mean": m, "ci95": [lo, hi], "per_user": e,
            "fnmr@fmr1%": float(np.mean([fnmr_at_fmr(g, i, 0.01) for g, i in res.values()])),
            "fnmr@fmr5%": float(np.mean([fnmr_at_fmr(g, i, 0.05) for g, i in res.values()])),
            "n_genuine_per_user": int(np.mean([len(g) for g, _ in res.values()])),
            "n_impostor_per_user": int(np.mean([len(i) for _, i in res.values()]))}


# ---------------------------------------------------------------- 3. Detector fusion (z-norm from enrolment only)
FUSE = ["Scaled Manhattan", "One-class SVM", "Siamese embedding"]
fname = "Fusion (SM+SVM+Siamese)"
C2[fname] = {}
for u in eval_users:
    gz = np.mean([(C2[n][u][0] - LOSO[n][u][0]) / LOSO[n][u][1] for n in FUSE], 0)
    iz = np.mean([(C2[n][u][1] - LOSO[n][u][0]) / LOSO[n][u][1] for n in FUSE], 0)
    C2[fname][u] = (gz, iz)
allnames = names + [fname]

fold_tab = {}
for n in allnames:
    row = {"C2": summarise(flat(C2[n]))}
    if n in C1:
        row["C1"] = summarise(C1[n])
        row["drift_eer"] = [float(np.mean([eer(g, i) for g, i in DR[n][t].values()])) for t in range(8)]
        d = np.array(row["C2"]["per_user"]) - np.array(row["C1"]["per_user"])
        row["C2_minus_C1"] = list(bootstrap_ci(d))
    row["fusion_k"] = {}
    for k in (1, 3, 5, 10):
        m, lo, hi = bootstrap_ci(ex.fused_eer(C2[n], k))
        row["fusion_k"][k] = {"eer_mean": m, "ci95": [lo, hi]}
    # operating point: threshold from enrolment-only LOSO genuine scores (quantile), applied to test sessions
    if n in LOSO:
        row["operational"] = {}
        for q in (0.9, 0.95, 0.99):
            fn, fm = [], []
            for u, (g, i) in flat(C2[n]).items():
                t = np.quantile(LOSO[n][u][2], q)
                fn.append(float((g > t).mean())); fm.append(float((i <= t).mean()))
            row["operational"][str(q)] = {"fnmr": float(np.mean(fn)), "fmr": float(np.mean(fm))}
    fold_tab[n] = row
    print(f"{n:28s} C2 {row['C2']['eer_mean']:.4f} {[round(x, 4) for x in row['C2']['ci95']]}",
          f"C1 {row['C1']['eer_mean']:.4f}" if "C1" in row else "", flush=True)
F["fold_protocol"] = fold_tab
for a, b in (("Siamese embedding", "Scaled Manhattan"), ("Siamese embedding", "One-class SVM"), (fname, "Scaled Manhattan")):
    d = np.array(fold_tab[a]["C2"]["per_user"]) - np.array(fold_tab[b]["C2"]["per_user"])
    F.setdefault("paired_C2", {})[f"{a} - {b}"] = list(bootstrap_ci(d))

# ---------------------------------------------------------------- 4. Full-protocol (40 impostors) baselines for DET
full_c1 = {n: ex.cond_within(data, eval_users, f) for n, f in base.items()}
full_c2 = {n: flat(ex.cond_cross(data, eval_users, f)) for n, f in base.items()}
fgrid = np.logspace(-3, 0, 80)


def det_fig(resd, title, fname_, lo, order):
    g = fgrid[fgrid >= lo]
    fig, ax = plt.subplots(figsize=(5.4, 4.3))
    for n in order:
        y = np.mean([det_curve_grid(a, b, g) for a, b in resd[n].values()], 0)
        e = np.mean([eer(a, b) for a, b in resd[n].values()])
        ax.plot(g * 100, np.clip(y, 1e-3, 1) * 100, label=f"{n} (EER {e*100:.1f}%)", color=COL[n], lw=2)
    ax.plot([lo * 100, 100], [lo * 100, 100], ls=":", color="#bbb", lw=1)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lo * 100, 100); ax.set_ylim(1, 100)
    ax.set_xlabel("False match rate FMR (%)"); ax.set_ylabel("False non-match rate FNMR (%)")
    ax.set_title(title); ax.grid(alpha=.3, which="both"); ax.legend(fontsize=7.5, loc="lower left")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, fname_), dpi=180); plt.close(fig)


det_fig(full_c1, "C1 within-session (41 subjects, 40 impostors)", "fin_det_c1.png", 1e-2, list(base))
det_fig(full_c2, "C2 cross-session (41 subjects, 40 impostors)", "fin_det_c2.png", 1e-3, list(base))
det_fig({n: flat(C2[n]) for n in allnames}, "C2 cross-session, fold protocol (impostors unseen)", "fin_det_c2_fold.png", 1e-2, allnames)
gdet = fgrid[fgrid >= 1e-2]
F["det_c2_fold_curve"] = {"fmr": gdet.tolist(), "fnmr": {n: np.mean([det_curve_grid(a, b, gdet) for a, b in flat(C2[n]).values()], 0).tolist() for n in allnames}}
F["full_protocol_check"] = {n: {"C1": float(np.mean([eer(a, b) for a, b in full_c1[n].values()])),
                                "C2": float(np.mean([eer(a, b) for a, b in full_c2[n].values()]))} for n in base}

# score distributions (per-user z-normalised with enrolment LOSO statistics so users can be pooled)
fig, axs = plt.subplots(1, 3, figsize=(11, 3.3))
for ax, n in zip(axs, ["Scaled Manhattan", "One-class SVM", "Siamese embedding"]):
    gz = np.concatenate([(C2[n][u][0].ravel() - LOSO[n][u][0]) / LOSO[n][u][1] for u in eval_users])
    iz = np.concatenate([(C2[n][u][1].ravel() - LOSO[n][u][0]) / LOSO[n][u][1] for u in eval_users])
    bins = np.linspace(-3, 15, 90)
    ax.hist(np.clip(gz, -3, 15), bins, density=True, alpha=.6, color="#1b7f3b", label="genuine (sessions 5-8)")
    ax.hist(np.clip(iz, -3, 15), bins, density=True, alpha=.5, color="#c0392b", label="impostor")
    ax.set_title(n); ax.set_xlabel("anomaly score (z vs. enrolment)")
axs[0].set_ylabel("density"); axs[0].legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fin_scores.png"), dpi=180); plt.close(fig)

# C1 vs C2 per-user and drift
fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.8))
for n in names:
    axs[0].plot(range(1, 9), np.array(fold_tab[n]["drift_eer"]) * 100, "o-", color=COL[n], label=n, ms=4)
axs[0].set_xlabel("test session (enrolment: session 1, reps 1-25)"); axs[0].set_ylabel("mean EER (%)")
axs[0].set_title("Template ageing (fixed 25 enrolment samples)"); axs[0].grid(alpha=.3); axs[0].legend(fontsize=7.5)
for n in allnames:
    ks = (1, 3, 5, 10)
    axs[1].plot(ks, [fold_tab[n]["fusion_k"][k]["eer_mean"] * 100 for k in ks], "o-", color=COL[n], label=n, ms=4)
axs[1].set_xlabel("consecutive entries averaged (k)"); axs[1].set_ylabel("mean EER (%)"); axs[1].set_xticks(ks)
axs[1].set_title("Multi-entry score fusion (C2)"); axs[1].grid(alpha=.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fin_drift_fusion.png"), dpi=180); plt.close(fig)

fig, ax = plt.subplots(figsize=(8.6, 3.6))
pos, ticks, labs = 0, [], []
for n in allnames:
    for cn, lab in (("C1", "within"), ("C2", "cross")):
        if cn not in fold_tab[n]:
            continue
        ax.boxplot(np.array(fold_tab[n][cn]["per_user"]) * 100, positions=[pos], widths=.7,
                   boxprops=dict(color=COL[n]), whiskerprops=dict(color=COL[n]), medianprops=dict(color="k"), flierprops=dict(ms=3))
        ticks.append(pos); labs.append(f"{n.split(' (')[0].replace(' ', chr(10), 1)}\n{lab}"); pos += 1
    pos += .5
ax.set_xticks(ticks); ax.set_xticklabels(labs, fontsize=6.5); ax.set_ylabel("per-user EER (%)")
ax.set_title("Per-user EER distribution (fold protocol, 41 subjects)"); ax.grid(alpha=.3, axis="y")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fin_per_user.png"), dpi=180); plt.close(fig)

# ---------------------------------------------------------------- 5. Error analysis
sm = "Scaled Manhattan"
pu = dict(zip(eval_users, [eer(*flat(C2[sm])[u]) for u in eval_users]))
order = sorted(pu, key=pu.get)
# feature drift between enrolment (S1-4) and test (S5-8), in units of the user's enrolment spread
shift = np.array([np.abs(data[u][4:].reshape(-1, 31).mean(0) - data[u][:4].reshape(-1, 31).mean(0)) /
                  (data[u][:4].reshape(-1, 31).std(0) + 1e-9) for u in eval_users])
speed = np.array([(data[u][4:, :, DD].sum(-1).mean() / data[u][:4, :, DD].sum(-1).mean()) for u in eval_users])
rho, p = spearmanr(shift.mean(1), [pu[u] for u in eval_users])
# wolves: impostor subjects most often accepted at each target's EER threshold
wolf = {u: [] for u in eval_users}
for t in eval_users:
    g, imp = C2[sm][t]
    gg = g.ravel()
    others = [o for o in next(f for f in folds if t in f) if o != t]
    th = np.quantile(gg, 1 - pu[t])  # threshold that rejects ~EER of genuine entries
    for o, s in zip(others, imp):
        wolf[o].append(float((s.ravel() <= th).mean()))
wolf_m = {u: float(np.mean(v)) for u, v in wolf.items()}
corr = {f"{a} vs {b}": float(spearmanr(fold_tab[a]["C2"]["per_user"], fold_tab[b]["C2"]["per_user"])[0])
        for a, b in (("Scaled Manhattan", "One-class SVM"), ("Scaled Manhattan", "Siamese embedding"), ("Mahalanobis", "Siamese embedding"))}
F["error_analysis"] = {
    "best_users": [(u, pu[u]) for u in order[:5]], "worst_users": [(u, pu[u]) for u in order[-5:]],
    "users_eer_below_5pct": int(sum(v < .05 for v in pu.values())), "users_eer_above_25pct": int(sum(v > .25 for v in pu.values())),
    "share_of_error_from_worst5": float(sum(pu[u] for u in order[-5:]) / sum(pu.values())),
    "feature_shift_by_group": {"H": float(shift[:, H].mean()), "DD": float(shift[:, DD].mean()), "UD": float(shift[:, UD].mean())},
    "top_shift_features": sorted(((cols[j], float(shift[:, j].mean())) for j in range(31)), key=lambda x: -x[1])[:5],
    "spearman_shift_vs_eer": [float(rho), float(p)],
    "speed_ratio_test_over_enrol": {"median": float(np.median(speed)), "faster_users": int((speed < 1).sum())},
    "top_wolves": sorted(wolf_m.items(), key=lambda x: -x[1])[:5], "median_wolf_rate": float(np.median(list(wolf_m.values()))),
    "per_user_eer_rank_corr": corr,
}
fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.6))
axs[0].scatter(shift.mean(1), np.array([pu[u] for u in eval_users]) * 100, s=18, color="#1b7f3b")
for u in order[-3:]:
    axs[0].annotate(u, (shift[eval_users.index(u)].mean(), pu[u] * 100), fontsize=7)
axs[0].set_xlabel("mean |feature shift| S1-4 → S5-8 (in enrolment SDs)"); axs[0].set_ylabel("C2 EER, scaled Manhattan (%)")
axs[0].set_title(f"Feature drift vs. C2 EER (Spearman ρ={rho:.2f}, p={p:.2f})"); axs[0].grid(alpha=.3)
fs = shift.mean(0)
cl = ["#1f5fbf" if j in H else "#1b7f3b" if j in DD else "#c0392b" for j in range(31)]
axs[1].bar(range(31), fs, color=cl)
axs[1].set_xticks(range(31)); axs[1].set_xticklabels([c.replace("Shift.r", "R").replace("period", ".").replace("five", "5").replace("Return", "Ent") for c in cols], rotation=90, fontsize=5.5)
axs[1].set_ylabel("mean |shift| (SD units)"); axs[1].set_title("Which features drift (blue H, green DD, red UD)")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fin_error.png"), dpi=180); plt.close(fig)

fig, ax = plt.subplots(figsize=(5, 3))
for i, l in enumerate(LOSS):
    ax.plot(np.arange(len(l)) * 100, l, label=f"fold {i+1}")
ax.set_xlabel("training step"); ax.set_ylabel("batch-hard triplet loss"); ax.legend(fontsize=7); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fin_loss.png"), dpi=170); plt.close(fig)

# ---------------------------------------------------------------- 6. Demo embedding (all 51 CMU subjects)
demo = Embedder(H, DD, **SIAM).fit(data, users)
json.dump(demo.state(), open(os.path.join(OUT, "siamese_demo.json"), "w"))
json.dump(F, open(os.path.join(OUT, "final.json"), "w"), indent=1, ensure_ascii=False,
          default=lambda o: o.item() if hasattr(o, "item") else str(o))
print("done ->", os.path.join(OUT, "final.json"))
