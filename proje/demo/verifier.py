"""Per-user keystroke verifier for the demo. Uses the SAME detector code as the evaluation (keystroke/).

Decision rule (identical in spirit to the report's operational point):
  * every detector is fitted on the user's enrolment entries only;
  * genuine "held-out" scores are obtained without any impostor data: leave-one-enrolment-session-out when the user
    has >= 2 enrolment sessions, otherwise 5-fold cross-validation over the enrolment entries;
  * each detector's score is z-normalised with the mean/SD of those held-out genuine scores; the fused score is the
    mean z over detectors (Scaled Manhattan + One-class SVM, + Siamese embedding when the password is the CMU one);
  * threshold = quantile q of the held-out fused genuine scores (q set by the security level).
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from keystroke.detectors import ScaledManhattan, OCSVM  # noqa: E402

CMU_PASSWORD = ".tie5Roanl"
SVM_PARAMS = {"nu": 0.05, "gamma": 0.03}  # chosen on the 10 CMU tuning subjects (results/results.json)
LEVELS = {"relaxed": 0.99, "balanced": 0.95, "strict": 0.90}
MIN_ENROL = 15
_EMB = None


def embedder():
    global _EMB
    if _EMB is None:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "siamese_demo.json")
        if os.path.exists(p):
            from keystroke.siamese import Embedder
            _EMB = Embedder.from_state(json.load(open(p)))
        else:
            _EMB = False
    return _EMB or None


def factories(cmu_layout):
    f = {"Scaled Manhattan": ScaledManhattan, "One-class SVM": lambda: OCSVM(**SVM_PARAMS)}
    if cmu_layout and embedder() is not None:
        from keystroke.siamese import SiameseDetector
        f["Siamese embedding"] = lambda: SiameseDetector(embedder())
    return f


def _heldout(factory, X, sess):
    s = np.full(len(X), np.nan)
    groups = np.unique(sess)
    if len(groups) >= 2:
        parts = [sess == g for g in groups]
    else:
        idx = np.arange(len(X))
        parts = [idx % 5 == k for k in range(5)]
    for m in parts:
        s[m] = factory().fit(X[~m]).score(X[m])
    return s


class UserModel:
    def __init__(self, X, sessions, cmu_layout, level="balanced"):
        self.X, self.sess = np.asarray(X, float), np.asarray(sessions)
        self.fac = factories(cmu_layout)
        self.det, self.norm, held = {}, {}, []
        for n, f in self.fac.items():
            h = _heldout(f, self.X, self.sess)
            self.norm[n] = (float(h.mean()), float(h.std() + 1e-9))
            held.append((h - self.norm[n][0]) / self.norm[n][1])
            self.det[n] = f().fit(self.X)
        self.held = np.mean(held, 0)
        self.level = level
        self.threshold = float(np.quantile(self.held, LEVELS[level]))

    def score(self, x):
        x = np.atleast_2d(np.asarray(x, float))
        z = {n: float(((d.score(x) - self.norm[n][0]) / self.norm[n][1]).mean()) for n, d in self.det.items()}
        return z, float(np.mean(list(z.values())))

    def profile(self):
        return {"mean": self.X.mean(0).tolist(), "sd": self.X.std(0).tolist()}
