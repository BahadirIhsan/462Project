"""Faz 3 (Veri ve Ön İşleme Kontrol Noktası): veri istatistikleri, ön işleme çıktıları, kalite sorunları, reddedilen örnekler.
Çıktılar: results/checkpoint.json ve results/cp_*.png  (çalıştırma: .venv/bin/python checkpoint.py)"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from keystroke.data import load_cmu, to_arrays, split_tuning_eval
from keystroke.detectors import make_detectors
from keystroke.preprocess import validate, feature_groups, total_time, enrolment_mask, EnrolmentFiltered
from keystroke.metrics import bootstrap_ci
from keystroke import experiments as ex

OUT = os.path.join(os.path.dirname(__file__), "results")
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
BLUE, RED, GREEN, GREY = "#1f5fbf", "#c0392b", "#1b7f3b", "#888888"

df, cols = load_cmu()
data = to_arrays(df, cols)
users = sorted(data)
tune_users, eval_users = split_tuning_eval(users, 10, seed=0)
H, DD, UD = feature_groups(cols)
X = df[cols].to_numpy(float)
tot = total_time(X, cols)
df["total"] = tot
keys = [c[2:].replace("period", ".").replace("five", "5").replace("Shift.r", "R").replace("Return", "Enter") for c in np.array(cols)[H]]
R = {}

# 1) Doğrulama
checks = validate(df, cols)
R["checks"] = {k: {"pass": bool(v[0]), "detail": v[1]} for k, v in checks.items()}

# 2) Veri istatistikleri
ids = sorted(int(u[1:]) for u in users)
R["dataset"] = {
    "entries": len(df), "subjects": len(users), "sessions": 8, "reps_per_session": 50, "features": len(cols),
    "subject_ids": f"s{ids[0]:03d}-s{ids[-1]:03d}, {ids[-1] - ids[0] + 1 - len(ids)} IDs absent",
    "mean_ms": {g: float(X[:, idx].mean() * 1000) for g, idx in (("H", H), ("DD", DD), ("UD", UD))},
    "sd_ms": {g: float(X[:, idx].std() * 1000) for g, idx in (("H", H), ("DD", DD), ("UD", UD))},
    "total_s": {"median": float(np.median(tot)), "p1": float(np.quantile(tot, .01)), "p99": float(np.quantile(tot, .99)), "max": float(tot.max())},
    "subject_median_total_s": {"min": float(df.groupby("subject").total.median().min()), "max": float(df.groupby("subject").total.median().max())},
    "session_median_total_s": {int(s): float(v) for s, v in df.groupby("sessionIndex").total.median().items()},
    "eval_users": len(eval_users), "tune_users": len(tune_users),
}
subj_sess = df.groupby(["subject", "sessionIndex"]).total.median().unstack()
R["dataset"]["subjects_faster_s8_than_s1"] = int((subj_sess[8] < subj_sess[1]).sum())
cv_within = df.groupby(["subject", "sessionIndex"]).total.agg(lambda t: t.std() / t.mean()).mean()
R["dataset"]["mean_within_session_cv_total"] = float(cv_within)

# 3) Kalite sorunları
negUD = X[:, UD] < 0
R["quality"] = {
    "neg_ud_values": int(negUD.sum()), "neg_ud_frac": float(negUD.mean()),
    "neg_ud_entries_frac": float(negUD.any(1).mean()),
    "neg_ud_by_pair": {cols[i][3:]: float(negUD[:, j].mean()) for j, i in enumerate(UD)},
    "neg_ud_subject_range": [float(negUD.reshape(51, 400, -1).mean((1, 2)).min()), float(negUD.reshape(51, 400, -1).mean((1, 2)).max())],
    "entries_any_dd_gt_1s": int((X[:, DD] > 1).any(1).sum()), "entries_any_dd_gt_2s": int((X[:, DD] > 2).any(1).sum()),
    "max_single_dd_s": float(X[:, DD].max()),
    "longest_entry": df.loc[int(np.argmax(tot)), ["subject", "sessionIndex", "rep"]].astype(str).to_dict(),
    "time_resolution_s": 1e-4, "mahalanobis_cov_rank": int(np.linalg.matrix_rank(np.cov(data[users[0]][:4].reshape(-1, 31), rowvar=False))),
}

# 4) Reddedilen örnekler (sadece kayıt girişleri; C2: oturum 1-4, C1: her oturumun ilk 25 tekrarı)
rej = {}
for k in (1.5, 2.0, 3.0):
    c2 = np.array([~enrolment_mask(data[u][:4].reshape(-1, 31), cols, k) for u in eval_users]).reshape(len(eval_users), 4, 50)
    c1 = np.array([[~enrolment_mask(data[u][s, :25], cols, k) for s in range(8)] for u in eval_users])
    rej[str(k)] = {"C2_rejected": int(c2.sum()), "C2_total": int(c2.size), "C2_by_session": c2.sum((0, 2)).astype(int).tolist(),
                   "C2_users_affected": int(c2.any((1, 2)).sum()), "C2_max_per_user": int(c2.sum((1, 2)).max()),
                   "C1_rejected": int(c1.sum()), "C1_total": int(c1.size)}
R["rejection"] = rej
c2mask = np.array([~enrolment_mask(data[u][:4].reshape(-1, 31), cols, 2.0) for u in eval_users]).reshape(len(eval_users), 4, 50)

# 5) Reddin etkisi (C2, oturumlar arası) - test verisi değişmez
svm = json.load(open(os.path.join(OUT, "results.json")))["svm_params"]
dets = make_detectors(svm)
R["effect_C2"] = {}
for name, f in dets.items():
    base = list(ex.per_user_eer({u: (g.ravel(), i.ravel()) for u, (g, i) in ex.cond_cross(data, eval_users, f).items()}).values())
    filt = list(ex.per_user_eer({u: (g.ravel(), i.ravel()) for u, (g, i) in
                                 ex.cond_cross(data, eval_users, lambda f=f: EnrolmentFiltered(f(), cols, 2.0)).items()}).values())
    d = np.array(filt) - np.array(base)
    R["effect_C2"][name] = {"eer_all": float(np.mean(base)), "eer_filtered": float(np.mean(filt)),
                            "diff": float(d.mean()), "diff_ci95": list(bootstrap_ci(d)[1:])}
    print(name, R["effect_C2"][name], flush=True)

json.dump(R, open(os.path.join(OUT, "checkpoint.json"), "w"), indent=1, ensure_ascii=False)

# ---------------- Şekiller ----------------
# (a) Bir girişin ham zaman çizelgesi (tuş bas/bırak) ve çıkarılan 31 özellik
u0, s0 = "s002", 0
cand = [r for r in range(50) if data[u0][s0, r, UD[7]] < 0]
r0 = cand[0] if cand else 0
v = data[u0][s0, r0]
down = np.concatenate([[0], np.cumsum(v[DD])])
up = down + v[H]
fig, ax = plt.subplots(figsize=(9, 3.1))
for i, (d0, u1) in enumerate(zip(down, up)):
    ax.barh(i, (u1 - d0) * 1000, left=d0 * 1000, color=BLUE if i < 10 else GREY, height=.6)
    ax.text(u1 * 1000 + 15, i, f"H={v[H[i]]*1000:.0f}", va="center", fontsize=7.5)
for j in range(10):
    if v[UD[j]] < 0:
        ax.annotate("overlap: next key pressed\nbefore this one is released\n(UD < 0)", xy=(down[j + 1] * 1000, j + .5), xytext=(down[j + 1] * 1000 + 350, j - 3.2),
                    fontsize=8, color=RED, arrowprops=dict(arrowstyle="->", color=RED))
        break
ax.set_yticks(range(11)); ax.set_yticklabels(keys); ax.invert_yaxis()
ax.set_xlabel("time since first key-down (ms)")
ax.set_title(f"Raw events of one entry ({u0}, session {s0+1}, rep {r0+1}): key-down → key-up", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "cp_entry.png"), dpi=200); plt.close(fig)

# (b) İstatistikler: özellik dağılımları, kişi başına hız, oturuma göre hız
fig, ax = plt.subplots(1, 3, figsize=(12, 3.4))
bins = np.linspace(-250, 800, 85)
for g, idx, c in (("Hold (H)", H, BLUE), ("Down-down (DD)", DD, GREEN), ("Up-down (UD)", UD, RED)):
    ax[0].hist(np.clip(X[:, idx].ravel() * 1000, -250, 800), bins=bins, histtype="step", lw=1.5, color=c, label=g, density=True)
ax[0].axvline(0, color="k", lw=.7); ax[0].set_xlabel("ms (clipped at 800)"); ax[0].set_title("(a) Timing feature distributions"); ax[0].legend(fontsize=8)
sm = df.groupby("subject").total.median().sort_values()
ax[1].bar(range(51), sm.values, color=[BLUE if s in eval_users else GREY for s in sm.index], width=.85)
ax[1].set_xlabel("subjects (sorted); grey = tuning group"); ax[1].set_ylabel("median entry time (s)"); ax[1].set_title("(b) Typing speed differs 3.5× across subjects")
ax[2].boxplot([subj_sess[s].values for s in range(1, 9)], showfliers=False, medianprops=dict(color=RED))
ax[2].set_xticks(range(1, 9)); ax[2].set_xlabel("session"); ax[2].set_ylabel("per-subject median time (s)"); ax[2].set_title("(c) Everyone gets faster: practice / drift")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "cp_stats.png"), dpi=200); plt.close(fig)

# (c) Ön işleme çıktısı: bir kullanıcının kayıt girişleri ham -> z-skor (SVM girdisi)
E = data[u0][:4].reshape(-1, 31)
Z = (E - E.mean(0)) / E.std(0)
fig, ax = plt.subplots(1, 2, figsize=(11, 3.2))
im0 = ax[0].imshow(E.T * 1000, aspect="auto", cmap="viridis", vmax=np.quantile(E * 1000, .98)); fig.colorbar(im0, ax=ax[0], label="ms")
im1 = ax[1].imshow(Z.T, aspect="auto", cmap="RdBu_r", vmin=-4, vmax=4); fig.colorbar(im1, ax=ax[1], label="z")
for a, t in zip(ax, ("(a) raw 31 features, 200 enrolment entries", "(b) after per-user z-scoring (one-class SVM input)")):
    a.set_title(t, fontsize=10); a.set_xlabel("enrolment entry (sessions 1-4)"); a.set_ylabel("feature #")
    for b in (50, 100, 150): a.axvline(b - .5, color="w", lw=.8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "cp_vectors.png"), dpi=200); plt.close(fig)

# (d) Kalite: toplam süre (log), tuş çifti başına UD<0
fig, ax = plt.subplots(1, 2, figsize=(11, 3.3))
ax[0].hist(tot, bins=np.logspace(np.log10(tot.min()), np.log10(tot.max()), 70), color=BLUE)
ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlabel("entry time (s, log)"); ax[0].set_ylabel("entries (log)")
ax[0].set_title(f"(a) Long tail: median {np.median(tot):.2f} s, max {tot.max():.1f} s", fontsize=10)
pairs = [f"{keys[j]}→{keys[j + 1]}".replace("Enter", "Ent") for j in range(10)]
ax[1].bar(pairs, negUD.mean(0) * 100, color=RED); ax[1].set_ylabel("% entries with UD < 0")
ax[1].set_title("(b) Key overlap depends on the key pair", fontsize=10); ax[1].tick_params(axis="x", labelsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "cp_quality.png"), dpi=200); plt.close(fig)

# (e) Ret: oturuma göre ret sayısı ve bir reddedilen girişin özellik profili
fig, ax = plt.subplots(1, 2, figsize=(11, 3.3), gridspec_kw={"width_ratios": [1, 1.6]})
for k, c in (("1.5", GREY), ("2.0", RED), ("3.0", "k")):
    ax[0].plot(range(1, 5), rej[k]["C2_by_session"], "o-", color=c, label=f"k = {k}")
ax[0].set_xticks(range(1, 5)); ax[0].set_xlabel("enrolment session"); ax[0].set_ylabel("rejected entries (41 users)")
ax[0].set_title("(a) Rejections concentrate in session 1", fontsize=10); ax[0].legend(fontsize=8)
ui, si, ri = np.argwhere(c2mask)[np.argmax([total_time(data[eval_users[a]][b, c], cols) / np.median(total_time(data[eval_users[a]][:4].reshape(-1, 31), cols))
                                            for a, b, c in np.argwhere(c2mask)])]
ue = eval_users[ui]
med = np.median(data[ue][:4].reshape(-1, 31), 0)
ax[1].plot(range(31), med * 1000, "o-", color=BLUE, ms=3, label=f"{ue} median of enrolment entries")
ax[1].plot(range(31), data[ue][si, ri] * 1000, "s-", color=RED, ms=3, label=f"rejected: session {si+1}, rep {ri+1} ({total_time(data[ue][si, ri], cols):.1f} s)")
ax[1].set_yscale("symlog", linthresh=100); ax[1].set_xlabel("feature # (H, DD, UD interleaved)"); ax[1].set_ylabel("ms (symlog)")
ax[1].set_title("(b) A rejected entry: long pauses inflate DD/UD, holds unchanged", fontsize=10); ax[1].legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "cp_reject.png"), dpi=200); plt.close(fig)
R["rejected_example"] = {"subject": ue, "session": int(si + 1), "rep": int(ri + 1), "total_s": float(total_time(data[ue][si, ri], cols)),
                         "user_median_s": float(np.median(total_time(data[ue][:4].reshape(-1, 31), cols))),
                         "max_dd_feature": cols[DD[int(np.argmax(data[ue][si, ri][DD]))]], "max_dd_s": float(data[ue][si, ri][DD].max())}
R["entry_example"] = {"subject": u0, "session": s0 + 1, "rep": r0 + 1}
json.dump(R, open(os.path.join(OUT, "checkpoint.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: R[k] for k in ("checks", "dataset", "rejection", "rejected_example")}, indent=1, ensure_ascii=False))
