import numpy as np

# Ön işleme: (1) veri doğrulama kontrolleri, (2) yalnızca KAYIT (eğitim) girişlerine uygulanan ret kuralı.
# Test girişleri hiçbir zaman filtrelenmez; aksi hâlde test verisine bakılarak sistem ayarlanmış olur.

EXPECTED = {"subjects": 51, "sessions": 8, "reps": 50, "features": 31}


def feature_groups(cols):
    H = [i for i, c in enumerate(cols) if c.startswith("H.")]
    DD = [i for i, c in enumerate(cols) if c.startswith("DD.")]
    UD = [i for i, c in enumerate(cols) if c.startswith("UD.")]
    return H, DD, UD


def total_time(X, cols):
    """Bir girişin toplam yazma süresi (sn): ilk tuşa basıştan Enter bırakılana kadar = ΣDD + H.Return."""
    H, DD, _ = feature_groups(cols)
    X = np.asarray(X)
    return X[..., DD].sum(-1) + X[..., H[-1]]


def validate(df, cols, tol=1e-6):
    """Yapısal ve fiziksel tutarlılık kontrolleri. Her kontrol: (geçti mi, sayı/açıklama)."""
    H, DD, UD = feature_groups(cols)
    X = df[cols].to_numpy(float)
    checks = {}
    checks["columns: 3 index + 31 timing"] = (len(cols) == EXPECTED["features"] and len(H) == 11 and len(DD) == 10 and len(UD) == 10,
                                              f"{len(H)} H, {len(DD)} DD, {len(UD)} UD")
    checks["missing / non-numeric values"] = (bool(np.isfinite(X).all()), int((~np.isfinite(X)).sum()))
    checks["duplicate (subject, session, rep)"] = (not df.duplicated(["subject", "sessionIndex", "rep"]).any(),
                                                  int(df.duplicated(["subject", "sessionIndex", "rep"]).sum()))
    per_sess = df.groupby(["subject", "sessionIndex"]).size()
    complete = df.subject.nunique() == EXPECTED["subjects"] and per_sess.nunique() == 1 and per_sess.iloc[0] == EXPECTED["reps"] \
        and df.groupby("subject").sessionIndex.nunique().eq(EXPECTED["sessions"]).all()
    checks["complete grid 51 x 8 x 50"] = (bool(complete), f"{df.subject.nunique()} x {df.sessionIndex.nunique()} x {per_sess.iloc[0]}")
    checks["hold times > 0"] = (bool((X[:, H] > 0).all()), f"min {X[:, H].min()*1000:.1f} ms")
    checks["down-down latencies > 0"] = (bool((X[:, DD] > 0).all()), f"min {X[:, DD].min()*1000:.1f} ms")
    dev = np.abs(X[:, DD] - (X[:, H[:-1]] + X[:, UD])).max()
    checks["identity DD = H + UD"] = (bool(dev < tol), f"max deviation {dev:.1e} s")
    neg = int((X[:, UD] < 0).sum())
    checks["negative up-down (key overlap)"] = (True, f"{neg} values ({neg / X[:, UD].size:.1%}), valid, kept")
    return checks


def enrolment_mask(X, cols, k=2.0):
    """Kayıt girişi reddedilir: toplam süre > k × (kullanıcının KENDİ kayıt girişlerinin medyanı).
    Duraksama / dikkat dağılması gibi ritim dışı girişleri şablondan çıkarır. Sadece eğitim verisiyle hesaplanır."""
    t = total_time(X, cols)
    return t <= k * np.median(t)


class EnrolmentFiltered:
    """Herhangi bir dedektörü sarar: fit() öncesi kayıt girişlerine ret kuralını uygular; score() değişmez."""

    def __init__(self, inner, cols, k=2.0):
        self.inner, self.cols, self.k = inner, cols, k

    def fit(self, X):
        keep = enrolment_mask(X, self.cols, self.k)
        self.n_rejected = int((~keep).sum())
        self.inner.fit(X[keep])
        return self

    def score(self, X):
        return self.inner.score(X)
