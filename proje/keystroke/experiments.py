import itertools
import numpy as np
from .detectors import make_detectors, OCSVM
from .metrics import eer, fnmr_at_fmr, det_curve_grid


def tune_svm(data, tune_users, nus=(0.01, 0.05, 0.1, 0.2, 0.5), gammas=(0.003, 0.01, 0.03, 0.1, 0.3)):
    """Yalnızca ayar kişilerinin ilk 4 oturumu: oturum 1-3 eğitim, oturum 4 doğrulama."""
    res = {}
    for nu, gamma in itertools.product(nus, gammas):
        eers = []
        for u in tune_users:
            others = [o for o in tune_users if o != u]
            det = OCSVM(nu, gamma).fit(data[u][:3].reshape(-1, data[u].shape[-1]))
            g = det.score(data[u][3])
            imp = np.concatenate([det.score(data[o][3]) for o in others])
            eers.append(eer(g, imp))
        res[(nu, gamma)] = float(np.mean(eers))
    best = min(res, key=res.get)
    return {"nu": best[0], "gamma": best[1]}, res


def cond_within(data, users, factory, n_train=25):
    """C1: her oturumda ilk n_train tekrarla eğit, aynı oturumun kalanıyla test et."""
    out = {}
    for u in users:
        gs, ims = [], []
        for s in range(8):
            det = factory().fit(data[u][s, :n_train])
            gs.append(det.score(data[u][s, n_train:]))
            ims.append(np.concatenate([det.score(data[o][s, n_train:]) for o in users if o != u]))
        out[u] = (np.concatenate(gs), np.concatenate(ims))
    return out


def cond_cross(data, users, factory):
    """C2: oturum 1-4 ile eğit, oturum 5-8 ile test et. Skorlar (4,50) biçiminde saklanır."""
    out = {}
    for u in users:
        det = factory().fit(data[u][:4].reshape(-1, data[u].shape[-1]))
        g = det.score(data[u][4:].reshape(-1, data[u].shape[-1])).reshape(4, 50)
        imp = np.stack([det.score(data[o][4:].reshape(-1, data[o].shape[-1])).reshape(4, 50) for o in users if o != u])
        out[u] = (g, imp)
    return out


def cond_drift(data, users, factory, n_train=25):
    """Oturum 1'in ilk n_train tekrarıyla eğit; oturum t'nin son 25 tekrarıyla test et (t=1..8)."""
    out = {t: {} for t in range(8)}
    for u in users:
        det = factory().fit(data[u][0, :n_train])
        for t in range(8):
            g = det.score(data[u][t, n_train:])
            imp = np.concatenate([det.score(data[o][t, n_train:]) for o in users if o != u])
            out[t][u] = (g, imp)
    return out


def cond_replicate(data, users, factory):
    """C3: Killourhy & Maxion protokolü. İlk 200 ile eğit, kalan 200 test; yabancı: her kişinin ilk 5 tekrarı."""
    out = {}
    for u in users:
        det = factory().fit(data[u][:4].reshape(-1, data[u].shape[-1]))
        g = det.score(data[u][4:].reshape(-1, data[u].shape[-1]))
        imp = np.concatenate([det.score(data[o][0, :5]) for o in users if o != u])
        out[u] = (g, imp)
    return out


def per_user_eer(res):
    return {u: eer(g, i) for u, (g, i) in res.items()}


def mean_det(res, grid):
    return np.mean([det_curve_grid(g, i, grid) for g, i in res.values()], axis=0)


def fused_eer(cross_res, k):
    """Ardışık k girişin skor ortalaması (oturum içi, örtüşmeyen pencereler)."""
    eers = []
    for u, (g, imp) in cross_res.items():
        def win(a):
            n = (a.shape[-1] // k) * k
            return a[..., :n].reshape(*a.shape[:-1], -1, k).mean(-1).reshape(-1)
        gw = win(g)
        iw = np.concatenate([win(x) for x in imp])
        eers.append(eer(gw, iw))
    return eers


def operational_point(data, users, factory, quantiles=(0.8, 0.9, 0.95)):
    """Eşik yalnızca eğitim döneminden: oturum-bırakmalı çapraz doğrulamayla gerçek kullanıcının skor nicelleri."""
    rows = {q: {"fnmr": [], "fmr": []} for q in quantiles}
    for u in users:
        X = data[u][:4]
        held = np.concatenate([factory().fit(np.delete(X, s, 0).reshape(-1, X.shape[-1])).score(X[s]) for s in range(4)])
        det = factory().fit(X.reshape(-1, X.shape[-1]))
        g = det.score(data[u][4:].reshape(-1, X.shape[-1]))
        imp = np.concatenate([det.score(data[o][4:].reshape(-1, X.shape[-1])) for o in users if o != u])
        for q in quantiles:
            t = np.quantile(held, q)
            rows[q]["fnmr"].append(float((g > t).mean()))
            rows[q]["fmr"].append(float((imp <= t).mean()))
    return rows
