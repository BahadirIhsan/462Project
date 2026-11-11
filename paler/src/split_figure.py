import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

OUT = os.path.join(os.path.dirname(__file__), "split_fig.png")
TR, TE, TU = "#1f5fbf", "#1b7f3b", "#c9a227"
fig, ax = plt.subplots(figsize=(7.2, 2.15))
rows = [("C3 / C2", "train: sessions 1–4 (200)", "test: sessions 5–8 (200)"),
        ("C1", "per session: reps 1–25 train", "reps 26–50 test"),
        ("Drift", "session 1, reps 1–25 train", "session t, reps 26–50 test")]
for r, (name, a, b) in enumerate(rows):
    y = 2 - r
    ax.text(-0.15, y + 0.35, name, ha="right", va="center", fontsize=8, weight="bold")
    for s in range(8):
        x = s
        if r == 0:
            ax.add_patch(Rectangle((x, y), 0.9, 0.7, color=TR if s < 4 else TE))
        elif r == 1:
            ax.add_patch(Rectangle((x, y), 0.45, 0.7, color=TR)); ax.add_patch(Rectangle((x + .45, y), 0.45, 0.7, color=TE))
        else:
            if s == 0:
                ax.add_patch(Rectangle((x, y), 0.45, 0.7, color=TR)); ax.add_patch(Rectangle((x + .45, y), 0.45, 0.7, color=TE))
            else:
                ax.add_patch(Rectangle((x, y), 0.45, 0.7, color="#d0d0d0")); ax.add_patch(Rectangle((x + .45, y), 0.45, 0.7, color=TE))
    ax.text(8.2, y + 0.35, f"{a}\n{b}", fontsize=6.6, va="center")
for s in range(8):
    ax.text(s + 0.45, 3.05, f"S{s+1}", ha="center", fontsize=7)
ax.set_xlim(-1.6, 13.2); ax.set_ylim(-0.1, 3.4); ax.axis("off")
ax.text(5.2, -0.05, "blue = enrolment/training, green = genuine test (impostors: other subjects, same test samples)", fontsize=6.4, ha="center", va="top")
fig.savefig(OUT, dpi=220, bbox_inches="tight")
