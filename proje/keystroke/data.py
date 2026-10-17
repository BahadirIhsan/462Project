import os
import numpy as np
import pandas as pd

DEFAULT_CSV = os.path.join(os.path.dirname(__file__), "..", "..", "eğitim için dökümanlar", "DSL-StrongPasswordData.csv")


def load_cmu(path=DEFAULT_CSV):
    df = pd.read_csv(path)
    feat_cols = [c for c in df.columns if c not in ("subject", "sessionIndex", "rep")]
    return df, feat_cols


def to_arrays(df, feat_cols):
    """{subject: dizi[oturum(1..8), tekrar(1..50), 31]} sözlüğü döndürür."""
    out = {}
    for s, g in df.groupby("subject"):
        g = g.sort_values(["sessionIndex", "rep"])
        out[s] = g[feat_cols].to_numpy(float).reshape(8, 50, len(feat_cols))
    return out


def split_tuning_eval(subjects, n_tune=10, seed=0):
    """Hiperparametre ayarı için ayrık bir kişi grubu; değerlendirme kişileri hiç görülmez."""
    rng = np.random.default_rng(seed)
    subs = sorted(subjects)
    tune = sorted(rng.choice(subs, size=n_tune, replace=False).tolist())
    ev = [s for s in subs if s not in tune]
    return tune, ev
