"""SQLite storage for the localhost demo (file: demo/instance/keystroke_demo.db, created on first run).

What is stored and why:
  users     - username, password HASH (scrypt via werkzeug; the plain password is never stored), consent time,
              security level, and whether the password is the public CMU password (then the Siamese model applies).
  samples   - enrolment timing vectors only (seconds; 3n+1 numbers per entry). Raw key events and the typed text are
              not stored. These are biometric data: they stay on this machine and can be deleted by the user.
  attempts  - each verification attempt: claimed user, self-declared role (genuine / impostor test), per-detector
              z-scores, fused score, threshold and decision. Analysed only on the demo site ("Demo analysis"), never used
              for the CMU evaluation or in the report.
"""
import json, os, sqlite3, time

PATH = os.environ.get("KEYSTROKE_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "keystroke_demo.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  pw_hash TEXT NOT NULL,
  pw_length INTEGER NOT NULL,
  cmu_layout INTEGER NOT NULL DEFAULT 0,
  level TEXT NOT NULL DEFAULT 'balanced',
  consent_at REAL NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_no INTEGER NOT NULL,
  features TEXT NOT NULL,
  total_s REAL NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('genuine', 'impostor')),
  n_entries INTEGER NOT NULL,
  password_ok INTEGER NOT NULL,
  scores TEXT,
  fused REAL,
  threshold REAL,
  accepted INTEGER NOT NULL,
  created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_samples_user ON samples(user_id);
CREATE INDEX IF NOT EXISTS ix_attempts_user ON attempts(user_id);
"""


def connect():
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    c = sqlite3.connect(PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.executescript(SCHEMA)
    return c


def now():
    return time.time()


def add_user(c, username, pw_hash, pw_length, cmu_layout):
    cur = c.execute("INSERT INTO users(username, pw_hash, pw_length, cmu_layout, consent_at, created_at) VALUES (?,?,?,?,?,?)",
                    (username, pw_hash, pw_length, int(cmu_layout), now(), now()))
    c.commit()
    return cur.lastrowid


def user_by_name(c, username):
    return c.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def user_by_id(c, uid):
    return c.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()


def add_sample(c, uid, session_no, feats, total):
    c.execute("INSERT INTO samples(user_id, session_no, features, total_s, created_at) VALUES (?,?,?,?,?)",
              (uid, session_no, json.dumps(feats), total, now()))
    c.commit()


def samples(c, uid):
    rows = c.execute("SELECT session_no, features FROM samples WHERE user_id = ? ORDER BY id", (uid,)).fetchall()
    return [json.loads(r["features"]) for r in rows], [r["session_no"] for r in rows]


def session_counts(c, uid):
    return [dict(r) for r in c.execute("SELECT session_no, COUNT(*) n, MIN(created_at) t FROM samples WHERE user_id = ? GROUP BY session_no ORDER BY session_no", (uid,))]


def add_attempt(c, uid, role, n, pw_ok, scores, fused, th, acc):
    c.execute("INSERT INTO attempts(user_id, role, n_entries, password_ok, scores, fused, threshold, accepted, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
              (uid, role, n, int(pw_ok), json.dumps(scores) if scores is not None else None, fused, th, int(acc), now()))
    c.commit()


def attempts(c, uid=None, limit=200):
    q = "SELECT a.*, u.username FROM attempts a JOIN users u ON u.id = a.user_id"
    args = ()
    if uid is not None:
        q += " WHERE a.user_id = ?"
        args = (uid,)
    return [dict(r) for r in c.execute(q + " ORDER BY a.id DESC LIMIT ?", args + (limit,))]


def set_level(c, uid, level):
    c.execute("UPDATE users SET level = ? WHERE id = ?", (level, uid))
    c.commit()


def delete_user(c, uid):
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    c.commit()


def all_users(c):
    return [dict(r) for r in c.execute("SELECT u.id, u.username, u.cmu_layout, u.level, (SELECT COUNT(*) FROM samples s WHERE s.user_id = u.id) n_samples, "
                                       "(SELECT COUNT(DISTINCT session_no) FROM samples s WHERE s.user_id = u.id) n_sessions FROM users u ORDER BY u.id")]
