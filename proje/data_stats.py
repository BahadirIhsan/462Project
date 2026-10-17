import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from keystroke.data import load_cmu, to_arrays

OUT = os.path.join(os.path.dirname(__file__), "results")
df, cols = load_cmu()
data = to_arrays(df, cols)
H = [i for i, c in enumerate(cols) if c.startswith("H.")]
DD = [i for i, c in enumerate(cols) if c.startswith("DD.")]
UD = [i for i, c in enumerate(cols) if c.startswith("UD.")]
tot = df[[cols[i] for i in DD]].sum(axis=1) + df["H.Return"]
st = {
    "n_rows": len(df), "n_subjects": df.subject.nunique(), "n_features": len(cols),
    "n_H": len(H), "n_DD": len(DD), "n_UD": len(UD),
    "mean_H_ms": float(df[[cols[i] for i in H]].to_numpy().mean() * 1000),
    "mean_DD_ms": float(df[[cols[i] for i in DD]].to_numpy().mean() * 1000),
    "mean_UD_ms": float(df[[cols[i] for i in UD]].to_numpy().mean() * 1000),
    "median_total_s": float(tot.median()), "p99_total_s": float(tot.quantile(.99)), "max_total_s": float(tot.max()),
    "frac_total_gt_3x_median": float((tot > 3 * tot.median()).mean()),
    "n_negative_UD": int((df[[cols[i] for i in UD]].to_numpy() < 0).sum()),
    "n_missing": int(df.isna().sum().sum()),
}
subj_med = df.assign(t=tot).groupby("subject").t.median()
st["subject_median_total_min_s"] = float(subj_med.min()); st["subject_median_total_max_s"] = float(subj_med.max())
json.dump(st, open(os.path.join(OUT, "data_stats.json"), "w"), indent=1)
print(st)

fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.7))
users = ["s002", "s010", "s030"]
for u, c in zip(users, ["#1f5fbf", "#c0392b", "#1b7f3b"]):
    m = data[u].reshape(-1, len(cols)).mean(0)
    ax[0].plot(range(len(cols)), m, "-", color=c, label=u, lw=1.4)
    ax[1].plot(range(1, 9), tot.to_numpy().reshape(51, 8, 50)[sorted(data).index(u)].mean(1), "o-", color=c, label=u)
ax[0].set_yscale("log"); ax[0].set_xlabel("Özellik sırası (parola sırasıyla)"); ax[0].set_ylabel("Ortalama süre (sn)")
ax[0].set_title("(a) Üç kullanıcının 31 özellik profili"); ax[0].grid(alpha=.3, which="both"); ax[0].legend(fontsize=8)
ax[1].set_xlabel("Oturum"); ax[1].set_ylabel("Yazma süresi (sn)")
ax[1].set_title("(b) Aynı kişi günden güne değişir"); ax[1].grid(alpha=.3); ax[1].legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "rhythm.png"), dpi=170)
