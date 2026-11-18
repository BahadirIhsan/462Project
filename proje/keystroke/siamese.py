"""Paylaşımlı öğrenilen gömü (Siamese / üçlü kayıp) – konu A5'teki "learned model shared across users".

Kural: model, değerlendirilen kişilerden AYRIK kişilerle eğitilir (çapraz katlama, run_all/final_experiments).
Eğitimde diğer kişiler negatif örnek olarak kullanıldığından test yabancıları da eğitimde görülmemiş kişiler olmalıdır.
"""
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.set_num_threads(4)


def transform(X, H, DD):
    """Süre özellikleri sağa çarpık: H ve DD (hep > 0) için log; UD negatif olabildiği için doğrusal kalır."""
    X = np.array(X, dtype=float, copy=True)
    X[..., H] = np.log(X[..., H])
    X[..., DD] = np.log(X[..., DD])
    return X


class Net(nn.Module):
    def __init__(self, d_in=31, hidden=128, dim=32):
        super().__init__()
        self.f = nn.Sequential(nn.Linear(d_in, hidden), nn.ReLU(), nn.Linear(hidden, hidden), nn.ReLU(), nn.Linear(hidden, dim))

    def forward(self, x):
        return F.normalize(self.f(x), dim=-1)


def batch_hard_triplet(emb, labels, margin):
    d = torch.cdist(emb, emb)
    same = labels[:, None] == labels[None, :]
    pos = (d * same).max(1).values
    neg = (d + same * 1e3).min(1).values
    return F.relu(pos - neg + margin).mean()


class Embedder:
    """Eğitim kişilerinin tüm girişleriyle (8 oturum × 50) üçlü kayıpla eğitilen ortak gömü ağı."""

    def __init__(self, H, DD, dim=32, hidden=128, steps=3000, P=16, K=16, margin=0.3, lr=1e-3, seed=0):
        self.H, self.DD = H, DD
        self.cfg = dict(dim=dim, hidden=hidden, steps=steps, P=P, K=K, margin=margin, lr=lr, seed=seed)

    def fit(self, data, train_users):
        c = self.cfg
        torch.manual_seed(c["seed"])
        rng = np.random.default_rng(c["seed"])
        X = np.stack([transform(data[u].reshape(-1, data[u].shape[-1]), self.H, self.DD) for u in train_users])
        flat = X.reshape(-1, X.shape[-1])
        self.mu, self.sd = flat.mean(0), flat.std(0) + 1e-9
        X = torch.tensor((X - self.mu) / self.sd, dtype=torch.float32)
        n_users, n_per = X.shape[0], X.shape[1]
        self.net = Net(X.shape[-1], c["hidden"], c["dim"])
        opt = torch.optim.Adam(self.net.parameters(), lr=c["lr"])
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, c["steps"])
        self.losses = []
        for step in range(c["steps"]):
            us = rng.choice(n_users, size=min(c["P"], n_users), replace=False)
            idx = rng.integers(0, n_per, size=(len(us), c["K"]))
            xb = X[torch.tensor(us)[:, None], torch.tensor(idx)].reshape(-1, X.shape[-1])
            yb = torch.tensor(np.repeat(us, c["K"]))
            loss = batch_hard_triplet(self.net(xb), yb, c["margin"])
            opt.zero_grad(); loss.backward(); opt.step(); sched.step()
            if step % 100 == 0:
                self.losses.append(float(loss.detach()))
        self.net.eval()
        return self

    @torch.no_grad()
    def embed(self, X):
        X = np.asarray(X, float)
        shp = X.shape[:-1]
        Z = (transform(X.reshape(-1, X.shape[-1]), self.H, self.DD) - self.mu) / self.sd
        return self.net(torch.tensor(Z, dtype=torch.float32)).numpy().reshape(*shp, -1)

    def state(self):
        return {"cfg": self.cfg, "mu": self.mu.tolist(), "sd": self.sd.tolist(), "H": self.H, "DD": self.DD,
                "weights": {k: v.tolist() for k, v in self.net.state_dict().items()}}

    @classmethod
    def from_state(cls, st):
        e = cls(st["H"], st["DD"], **{k: st["cfg"][k] for k in ("dim", "hidden")})
        e.mu, e.sd = np.array(st["mu"]), np.array(st["sd"])
        e.net = Net(len(e.mu), st["cfg"]["hidden"], st["cfg"]["dim"])
        e.net.load_state_dict({k: torch.tensor(v) for k, v in st["weights"].items()})
        e.net.eval()
        return e


class SiameseDetector:
    """Kullanıcıya özgü kısım: kayıt gömülerinin merkezi. Skor = gömü uzayında merkeze uzaklık
    (scoring='centroid') ya da gömü uzayında ölçekli Manhattan (scoring='scaled')."""
    name = "Siamese embedding"

    def __init__(self, embedder, scoring="centroid"):
        self.e, self.scoring = embedder, scoring

    def fit(self, X):
        Z = self.e.embed(X)
        self.mu = Z.mean(0)
        self.mad = np.abs(Z - self.mu).mean(0) + 1e-6
        return self

    def score(self, X):
        Z = self.e.embed(X)
        if self.scoring == "scaled":
            return (np.abs(Z - self.mu) / self.mad).sum(-1)
        return np.linalg.norm(Z - self.mu, axis=-1)
