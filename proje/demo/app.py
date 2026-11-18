"""Localhost demo: password + typing-rhythm login (BİL462 project A5).

Run:  cd proje && .venv/bin/python demo/app.py   ->  http://127.0.0.1:5000
Demo data (team members only) are stored in demo/instance/keystroke_demo.db and are NEVER used in the CMU evaluation.
"""
import json, os, secrets, sys
import numpy as np
from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, session, url_for, abort
from werkzeug.security import check_password_hash, generate_password_hash

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import db  # noqa: E402
from features import EntryError, events_to_features  # noqa: E402
from verifier import CMU_PASSWORD, LEVELS, MIN_ENROL, UserModel  # noqa: E402

RESULTS = os.path.join(HERE, "..", "results")
app = Flask(__name__)


def _secret():
    p = os.path.join(HERE, "instance", "secret_key")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if not os.path.exists(p):
        with open(p, "w") as f:
            f.write(secrets.token_hex(32))
    return open(p).read().strip()


app.secret_key = _secret()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict")


def current_user(c):
    uid = session.get("uid")
    return db.user_by_id(c, uid) if uid else None


def bad(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code


@app.get("/")
def home():
    c = db.connect()
    return render_template("home.html", user=current_user(c), users=db.all_users(c), min_enrol=MIN_ENROL)


@app.get("/register")
def register_page():
    return render_template("register.html", user=None, cmu_password=CMU_PASSWORD)


@app.post("/api/register")
def register():
    d = request.get_json(force=True)
    name, pw, pw2 = (d.get("username") or "").strip(), d.get("password") or "", d.get("password2") or ""
    if not (3 <= len(name) <= 32) or not name.replace("_", "").replace(".", "").isalnum():
        return bad("Username: 3-32 letters, digits, '_' or '.'")
    if pw != pw2:
        return bad("The two passwords differ.")
    if not (6 <= len(pw) <= 32) or any(ch.isspace() for ch in pw):
        return bad("Password: 6-32 characters, no spaces.")
    if not d.get("consent"):
        return bad("Consent is required to store your typing-rhythm template.")
    c = db.connect()
    if db.user_by_name(c, name):
        return bad("This username already exists.")
    uid = db.add_user(c, name, generate_password_hash(pw), len(pw), pw == CMU_PASSWORD)
    session.clear()
    session.update(uid=uid, enrol_session=1)
    return jsonify({"ok": True, "next": url_for("enroll_page")})


@app.get("/enroll")
def enroll_page():
    c = db.connect()
    u = current_user(c)
    if not u:
        return redirect(url_for("login_page", next="enroll"))
    counts = db.session_counts(c, u["id"])
    if "enrol_session" not in session:
        session["enrol_session"] = (max([r["session_no"] for r in counts]) + 1) if counts else 1
    return render_template("enroll.html", user=u, counts=counts, sess=session["enrol_session"], min_enrol=MIN_ENROL)


@app.post("/api/enroll")
def enroll():
    c = db.connect()
    u = current_user(c)
    if not u:
        return bad("Not signed in.", 401)
    try:
        text, feats, _ = events_to_features(request.get_json(force=True).get("events", []))
    except EntryError as e:
        return bad(str(e))
    if len(text) != u["pw_length"] or not check_password_hash(u["pw_hash"], text):
        return bad("Typed text does not match your password. Entries with typos are discarded (as in the CMU study).")
    db.add_sample(c, u["id"], session["enrol_session"], feats, sum(feats[1::3]) + feats[-1])
    X, s = db.samples(c, u["id"])
    X = np.array(X)
    return jsonify({"ok": True, "n": len(X), "n_session": int(sum(1 for v in s if v == session["enrol_session"])),
                    "last": feats, "mean": X.mean(0).tolist(), "sd": X.std(0).tolist()})


@app.post("/api/enroll/new-session")
def new_session():
    c = db.connect()
    u = current_user(c)
    if not u:
        return bad("Not signed in.", 401)
    counts = db.session_counts(c, u["id"])
    session["enrol_session"] = (max([r["session_no"] for r in counts]) + 1) if counts else 1
    return jsonify({"ok": True, "session": session["enrol_session"]})


@app.get("/login")
def login_page():
    c = db.connect()
    return render_template("login.html", user=current_user(c), users=db.all_users(c), levels=LEVELS)


@app.post("/api/verify")
def verify():
    d = request.get_json(force=True)
    role = d.get("role", "genuine")
    if role not in ("genuine", "impostor"):
        return bad("bad role")
    c = db.connect()
    u = db.user_by_name(c, (d.get("username") or "").strip())
    if not u:
        return bad("Unknown user.")
    entries = d.get("entries") or []
    if not 1 <= len(entries) <= 5:
        return bad("Send 1-5 entries.")
    feats = []
    for ev in entries:
        try:
            text, f, _ = events_to_features(ev)
        except EntryError as e:
            return bad(str(e))
        if len(text) != u["pw_length"] or not check_password_hash(u["pw_hash"], text):
            db.add_attempt(c, u["id"], role, len(entries), False, None, None, None, False)
            return jsonify({"ok": True, "password_ok": False, "accepted": False,
                            "message": "Wrong password: rejected before the rhythm check."})
        feats.append(f)
    X, s = db.samples(c, u["id"])
    if len(X) < MIN_ENROL:
        return bad(f"{u['username']} has only {len(X)} enrolment entries (minimum {MIN_ENROL}).")
    m = UserModel(X, s, bool(u["cmu_layout"]), u["level"])
    z, fused = m.score(feats)
    acc = fused <= m.threshold
    db.add_attempt(c, u["id"], role, len(entries), True, z, fused, m.threshold, acc)
    if acc and role == "genuine":
        session.clear()
        session["uid"] = u["id"]
    prof = m.profile()
    return jsonify({"ok": True, "password_ok": True, "accepted": bool(acc), "role": role, "fused": fused,
                    "threshold": m.threshold, "level": u["level"], "q": LEVELS[u["level"]], "scores": z,
                    "held": np.sort(m.held).tolist(), "attempt": np.mean(feats, 0).tolist(),
                    "mean": prof["mean"], "sd": prof["sd"], "n_enrol": len(X), "n_sessions": len(set(s))})


@app.get("/account")
def account():
    c = db.connect()
    u = current_user(c)
    if not u:
        return redirect(url_for("login_page"))
    return render_template("account.html", user=u, counts=db.session_counts(c, u["id"]), attempts=db.attempts(c, u["id"], 50),
                           levels=LEVELS, min_enrol=MIN_ENROL)


@app.post("/api/level")
def set_level():
    c = db.connect()
    u = current_user(c)
    lv = request.get_json(force=True).get("level")
    if not u or lv not in LEVELS:
        return bad("bad request")
    db.set_level(c, u["id"], lv)
    return jsonify({"ok": True})


@app.post("/api/delete")
def delete():
    c = db.connect()
    u = current_user(c)
    if not u:
        return bad("Not signed in.", 401)
    db.delete_user(c, u["id"])
    session.clear()
    return jsonify({"ok": True, "next": url_for("home")})


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.get("/lab")
def lab():
    c = db.connect()
    at = db.attempts(c, None, 500)
    stats = {}
    for role in ("genuine", "impostor"):
        a = [x for x in at if x["role"] == role and x["password_ok"]]
        stats[role] = {"n": len(a), "accepted": sum(x["accepted"] for x in a)}
    return render_template("lab.html", user=current_user(c), users=db.all_users(c), attempts=at[:60], stats=stats)


@app.get("/results")
def results():
    c = db.connect()
    R = json.load(open(os.path.join(RESULTS, "results.json")))
    F = json.load(open(os.path.join(RESULTS, "final.json")))
    return render_template("results.html", user=current_user(c), R=R, F=F)


@app.get("/results/img/<path:name>")
def result_img(name):
    if not name.endswith(".png"):
        abort(404)
    return send_from_directory(RESULTS, name)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
