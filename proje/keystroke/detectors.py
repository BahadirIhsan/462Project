import numpy as np
from sklearn.svm import OneClassSVM

# Tüm dedektörler: fit(X_egitim) ; score(X) -> anomali skoru (büyük = daha çok yabancı)


class Manhattan:
    name = "Manhattan"

    def fit(self, X):
        self.mu = X.mean(0)
        return self

    def score(self, X):
        return np.abs(X - self.mu).sum(1)


class ScaledManhattan:
    name = "Scaled Manhattan"

    def fit(self, X):
        self.mu = X.mean(0)
        self.mad = np.abs(X - self.mu).mean(0) + 1e-9
        return self

    def score(self, X):
        return (np.abs(X - self.mu) / self.mad).sum(1)


class Mahalanobis:
    name = "Mahalanobis"

    def __init__(self, ridge=1e-3):
        self.ridge = ridge

    def fit(self, X):
        self.mu = X.mean(0)
        cov = np.cov(X, rowvar=False)
        cov = cov + self.ridge * np.trace(cov) / cov.shape[0] * np.eye(cov.shape[0])
        self.P = np.linalg.pinv(cov)
        return self

    def score(self, X):
        d = X - self.mu
        return np.einsum("ij,jk,ik->i", d, self.P, d)


class OCSVM:
    name = "One-class SVM"

    def __init__(self, nu=0.1, gamma=0.03):
        self.nu, self.gamma = nu, gamma

    def fit(self, X):
        self.m = X.mean(0)
        self.s = X.std(0) + 1e-9
        self.svm = OneClassSVM(kernel="rbf", nu=self.nu, gamma=self.gamma).fit((X - self.m) / self.s)
        return self

    def score(self, X):
        return -self.svm.decision_function((X - self.m) / self.s)


def make_detectors(svm_params):
    return {
        "Manhattan": lambda: Manhattan(),
        "Scaled Manhattan": lambda: ScaledManhattan(),
        "Mahalanobis": lambda: Mahalanobis(),
        "One-class SVM": lambda: OCSVM(**svm_params),
    }
