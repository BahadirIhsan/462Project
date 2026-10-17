import numpy as np


def _fmr_fnmr(genuine, impostor):
    """Eşik taraması: skor <= t ise kabul. FMR = kabul edilen yabancı, FNMR = reddedilen gerçek kullanıcı."""
    g = np.sort(np.asarray(genuine))
    i = np.sort(np.asarray(impostor))
    th = np.unique(np.concatenate([g, i]))
    th = np.concatenate([[th[0] - 1e-9], th])
    fnmr = 1 - np.searchsorted(g, th, side="right") / len(g)
    fmr = np.searchsorted(i, th, side="right") / len(i)
    return th, fmr, fnmr


def eer(genuine, impostor):
    _, fmr, fnmr = _fmr_fnmr(genuine, impostor)
    d = fnmr - fmr
    k = np.argmax(d <= 0)
    if k == 0:
        return float((fmr[0] + fnmr[0]) / 2)
    d0, d1 = d[k - 1], d[k]
    w = d0 / (d0 - d1) if d0 != d1 else 0.5
    return float(fnmr[k - 1] + w * (fnmr[k] - fnmr[k - 1]))


def fnmr_at_fmr(genuine, impostor, target):
    _, fmr, fnmr = _fmr_fnmr(genuine, impostor)
    ok = fmr <= target
    return float(fnmr[ok].min()) if ok.any() else 1.0


def det_curve_grid(genuine, impostor, grid):
    """Kullanıcı başına DET: sabit FMR ızgarasında FNMR."""
    _, fmr, fnmr = _fmr_fnmr(genuine, impostor)
    out = []
    for f in grid:
        ok = fmr <= f
        out.append(fnmr[ok].min() if ok.any() else 1.0)
    return np.array(out)


def bootstrap_ci(per_user_values, n_boot=2000, seed=0, alpha=0.05):
    """Denekleri (kullanıcıları) yeniden örnekleyerek ortalamanın güven aralığı."""
    v = np.asarray(per_user_values, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(v), size=(n_boot, len(v)))
    means = v[idx].mean(1)
    return float(v.mean()), float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))
