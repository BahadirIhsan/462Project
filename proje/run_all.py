import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from keystroke.data import load_cmu, to_arrays, split_tuning_eval
from keystroke.detectors import make_detectors
from keystroke.metrics import fnmr_at_fmr, bootstrap_ci
from keystroke import experiments as ex

OUT = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT, exist_ok=True)
COL = {"Manhattan": "#888", "Scaled Manhattan": "#1b7f3b", "Mahalanobis": "#c0392b", "One-class SVM": "#1f5fbf"}

df, cols = load_cmu()
data = to_arrays(df, cols)
all_users = sorted(data)
tune_users, eval_users = split_tuning_eval(all_users, 10, seed=0)
print("ayar kişileri:", tune_users)
svm_params, grid = ex.tune_svm(data, tune_users)
print("SVM seçilen:", svm_params, "ayar EER:", round(grid[(svm_params['nu'], svm_params['gamma'])], 4))
dets = make_detectors(svm_params)
R = {"svm_params": svm_params, "tune_users": tune_users, "eval_users": eval_users,
     "svm_grid": {f"nu={k[0]},gamma={k[1]}": v for k, v in grid.items()}}

fgrid = np.logspace(-3, 0, 60)
c1, c2, c2f, c3, c3e, drift = {}, {}, {}, {}, {}, {}
for name, f in dets.items():
    print("koşuluyor:", name, flush=True)
    c1[name] = ex.cond_within(data, eval_users, f)
    c2[name] = ex.cond_cross(data, eval_users, f)
    c2f[name] = {u: (g.reshape(-1), imp.reshape(-1)) for u, (g, imp) in c2[name].items()}
    drift[name] = ex.cond_drift(data, eval_users, f)
    c3[name] = ex.cond_replicate(data, all_users if name != "One-class SVM" else eval_users, f)
    c3e[name] = ex.cond_replicate(data, eval_users, f)

summary = {}
for name in dets:
    row = {}
    for cname, res in (("C1_oturum_ici", c1[name]), ("C2_oturumlar_arasi", c2f[name]), ("C3_makale_protokolu", c3[name])):
        e = list(ex.per_user_eer(res).values())
        m, lo, hi = bootstrap_ci(e)
        row[cname] = {"eer_mean": m, "ci95": [lo, hi], "n_users": len(e), "per_user": e,
                      "fnmr@fmr1%": float(np.mean([fnmr_at_fmr(g, i, 0.01) for g, i in res.values()])),
                      "fnmr@fmr0.1%": float(np.mean([fnmr_at_fmr(g, i, 0.001) for g, i in res.values()])) if cname == "C2_oturumlar_arasi" else None,
                      "n_genuine_per_user": int(np.mean([len(g) for g, _ in res.values()])),
                      "n_impostor_per_user": int(np.mean([len(i) for _, i in res.values()]))}
    e41 = list(ex.per_user_eer(c3e[name]).values())
    row["C3_eval41"] = {"eer_mean": float(np.mean(e41)), "ci95": list(bootstrap_ci(e41)[1:])}
    row["drift_eer"] = [float(np.mean(list(ex.per_user_eer(drift[name][t]).values()))) for t in range(8)]
    row["fusion"] = {}
    for k in (1, 3, 5, 10):
        e = ex.fused_eer(c2[name], k)
        m, lo, hi = bootstrap_ci(e)
        row["fusion"][k] = {"eer_mean": m, "ci95": [lo, hi]}
    summary[name] = row
    print(name, {k: round(v["eer_mean"], 3) for k, v in row.items() if isinstance(v, dict) and "eer_mean" in v}, flush=True)
R["summary"] = summary

R["operational"] = {}
for name, f in dets.items():
    op = ex.operational_point(data, eval_users, f)
    R["operational"][name] = {str(q): {"fnmr": float(np.mean(v["fnmr"])), "fmr": float(np.mean(v["fmr"]))} for q, v in op.items()}

R["c2_minus_c1"] = {}
for name in dets:
    a = np.array(summary[name]["C1_oturum_ici"]["per_user"])
    b = np.array(summary[name]["C2_oturumlar_arasi"]["per_user"])
    R["c2_minus_c1"][name] = bootstrap_ci(b - a)
json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=1, ensure_ascii=False)

plt.rcParams.update({"font.size": 10})
def det_plot(resdict, title, fname, lo):
    g = fgrid[fgrid >= lo]
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    for name in dets:
        y = ex.mean_det(resdict[name], g)
        ax.plot(g * 100, np.clip(y, 1e-3, 1) * 100, label=name, color=COL[name], lw=2)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("FMR (%)  [yabancı kabul]"); ax.set_ylabel("FNMR (%)  [gerçek kullanıcı red]")
    ax.set_title(title); ax.grid(alpha=.3, which="both"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, fname), dpi=170); plt.close(fig)
det_plot(c1, "C1: oturum içi (DET)", "det_c1.png", 1e-2)
det_plot(c2f, "C2: oturumlar arası (DET)", "det_c2.png", 1e-3)

fig, ax = plt.subplots(figsize=(5.6, 4.0))
for name in dets:
    ax.plot(range(1, 9), np.array(summary[name]["drift_eer"]) * 100, "o-", color=COL[name], label=name)
ax.set_xlabel("Test oturumu (eğitim: oturum 1, ilk 25 tekrar)"); ax.set_ylabel("Ortalama EER (%)")
ax.set_title("Zamanla bozulma"); ax.grid(alpha=.3); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "drift.png"), dpi=170); plt.close(fig)

fig, ax = plt.subplots(figsize=(7.4, 4.0))
pos = 0; ticks = []; labels = []
for name in dets:
    for cn, lab in (("C1_oturum_ici", "içi"), ("C2_oturumlar_arasi", "arası")):
        ax.boxplot(np.array(summary[name][cn]["per_user"]) * 100, positions=[pos], widths=.7,
                   boxprops=dict(color=COL[name]), medianprops=dict(color="k"))
        ticks.append(pos); labels.append(f"{name.replace(' ', chr(10))}\n{lab}"); pos += 1
    pos += .6
ax.set_xticks(ticks); ax.set_xticklabels(labels, fontsize=6.5); ax.set_ylabel("Kullanıcı başına EER (%)")
ax.set_title("Kullanıcı başına EER dağılımı"); ax.grid(alpha=.3, axis="y")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "per_user_eer.png"), dpi=170); plt.close(fig)

fig, ax = plt.subplots(figsize=(5.2, 4.0))
ks = (1, 3, 5, 10)
for name in dets:
    ax.plot(ks, [summary[name]["fusion"][k]["eer_mean"] * 100 for k in ks], "o-", color=COL[name], label=name)
ax.set_xlabel("Birleştirilen ardışık giriş sayısı k"); ax.set_ylabel("Ortalama EER (%)")
ax.set_title("Skor birleştirme (C2)"); ax.grid(alpha=.3); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fusion.png"), dpi=170); plt.close(fig)
print("bitti")
