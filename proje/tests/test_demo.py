"""End-to-end check of the demo with CMU entries replayed as browser key events (no browser needed).
Run: .venv/bin/python tests/test_demo.py"""
import os, sys, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["KEYSTROKE_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "demo"))
from keystroke.data import load_cmu, to_arrays
from features import events_to_features
import app as demo

df, cols = load_cmu()
data = to_arrays(df, cols)
KEYS = list(".tie5Roanl") + ["Enter"]


def to_events(x, t0=1000.0):
    ev, d = [], t0
    for i, k in enumerate(KEYS):
        h = x[3 * i]
        ev.append({"k": k, "d": d, "u": d + h * 1000})
        if i < len(KEYS) - 1:
            d += x[3 * i + 1] * 1000
    return ev


# 1) feature extraction reproduces the CMU vector and column order
x = data["s040"][0, 0]
text, f, names = events_to_features(to_events(x))
assert text == ".tie5Roanl"
assert np.allclose(f, x, atol=1e-9), "feature mismatch"
assert [n.replace(".", "", 0) for n in names][0] == "H.." and len(names) == 31
print("features: OK (31 values identical to the CSV row)")

# 2) register / enrol / verify through the HTTP API
c = demo.app.test_client()
r = c.post("/api/register", json={"username": "s040demo", "password": ".tie5Roanl", "password2": ".tie5Roanl", "consent": True}).get_json()
assert r["ok"], r
for s in range(2):
    if s:
        assert c.post("/api/enroll/new-session", json={}).get_json()["session"] == 2
    for rep in range(15):
        r = c.post("/api/enroll", json={"events": to_events(data["s040"][s, rep])}).get_json()
        assert r["ok"], r
assert r["n"] == 30
bad = c.post("/api/enroll", json={"events": to_events(data["s040"][0, 0])[:-3] + to_events(data["s040"][0, 0])[-1:]}).get_json()
assert not bad["ok"]
print("enrolment: OK (30 entries in 2 sessions, wrong text rejected)")


def acc_rate(subject, role, k=1):
    out = []
    for rep in range(0, 20, k):
        ents = [to_events(data[subject][6, rep + j]) for j in range(k)]
        j = c.post("/api/verify", json={"username": "s040demo", "role": role, "entries": ents}).get_json()
        assert j["ok"] and j["password_ok"], j
        out.append(j["accepted"])
    return np.mean(out), j


g, j = acc_rate("s040", "genuine")
print(f"genuine s040 session 7 accepted {g:.0%}; detectors used: {list(j['scores'])}, threshold {j['threshold']:.2f}")
imps = [acc_rate(s, "impostor")[0] for s in ("s041", "s042", "s043", "s044", "s046")]
print(f"impostors accepted: {np.mean(imps):.0%} (per impostor {[f'{v:.0%}' for v in imps]})")
g3, _ = acc_rate("s040", "genuine", k=3)
print(f"genuine with k=3 entries accepted {g3:.0%}")
w = c.post("/api/verify", json={"username": "s040demo", "role": "genuine", "entries": [to_events(data["s040"][6, 0])[:5] + to_events(data["s040"][6, 0])[-1:]]}).get_json()
assert w["ok"] and not w["password_ok"] and not w["accepted"]
for page in ("/", "/login", "/lab", "/results", "/account", "/enroll", "/register"):
    assert c.get(page).status_code == 200, page
assert c.post("/api/delete", json={}).get_json()["ok"]
assert c.get("/account").status_code == 302
print("pages, wrong password, delete: OK")
