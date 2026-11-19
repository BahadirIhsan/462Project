"""Demo verisinin analizi: yalnızca demo sitesindeki "Demo analizi" sayfasında gösterilir.

Girdi: SQLite'taki gönüllü katılımcıların kayıt girişleri (samples) ve doğrulama denemeleri (attempts).
Parolası yanlış yazılan denemeler ritim kararına ulaşmadığı için hata oranlarına katılmaz (ayrı sayılır).
Her denemenin "pay"ı = birleşik skor − o anki kullanıcı eşiği; ≤ 0 ise kabul. Eşiksiz özet (EER) için bu
paylar tüm katılımcılarda havuzlanır. Bu sayılar CMU değerlendirmesine karıştırılmaz ve raporda kullanılmaz.
"""
import json
import numpy as np


def _rate(x):
    return None if not x["n"] else x["k"] / x["n"]


def eer_curve(gen, imp):
    """Havuzlanmış paylar için FMR/FNMR eğrisi ve EER (eşik t: pay ≤ t kabul)."""
    g, i = np.asarray(gen, float), np.asarray(imp, float)
    if len(g) == 0 or len(i) == 0:
        return None
    ts = np.unique(np.concatenate([g, i, [-np.inf, np.inf]]))
    fnmr = np.array([(g > t).mean() for t in ts])
    fmr = np.array([(i <= t).mean() for t in ts])
    j = int(np.argmin(np.abs(fnmr - fmr)))
    return {"eer": float((fnmr[j] + fmr[j]) / 2), "fmr": fmr.tolist(), "fnmr": fnmr.tolist()}


def analyse(c):
    users = {r["id"]: dict(r) for r in c.execute("SELECT id, username, created_at FROM users ORDER BY id")}
    samp = c.execute("SELECT user_id, session_no, total_s, created_at FROM samples ORDER BY id").fetchall()
    att = [dict(r) for r in c.execute("SELECT * FROM attempts ORDER BY id")]

    per = {uid: {"username": u["username"], "n_enrol": 0, "sessions": {}, "gen": {"n": 0, "k": 0}, "imp": {"n": 0, "k": 0},
                 "gm": [], "im": [], "wrong_pw": 0} for uid, u in users.items()}
    for s in samp:
        p = per[s["user_id"]]
        p["n_enrol"] += 1
        p["sessions"].setdefault(s["session_no"], []).append(s["total_s"])

    tot = {k: {"gen": {"n": 0, "k": 0}, "imp": {"n": 0, "k": 0}} for k in ("all", "1", "3")}
    gm, im, timeline, wrong = [], [], [], {"genuine": 0, "impostor": 0}
    det_scores = {}
    for a in att:
        p = per.get(a["user_id"])
        if not a["password_ok"] or a["fused"] is None:
            wrong[a["role"]] += 1
            if p:
                p["wrong_pw"] += 1
            continue
        m = a["fused"] - a["threshold"]
        key = "gen" if a["role"] == "genuine" else "imp"
        # hata sayacı: hesap sahibi için ret (FNMR), sahtekâr için kabul (FMR)
        err = (not a["accepted"]) if key == "gen" else bool(a["accepted"])
        for k in ("all", str(a["n_entries"])):
            if k in tot:
                tot[k][key]["n"] += 1
                tot[k][key]["k"] += int(err)
        p[key]["n"] += 1
        p[key]["k"] += int(err)
        (gm if key == "gen" else im).append(m)
        p["gm" if key == "gen" else "im"].append(m)
        timeline.append({"t": a["created_at"], "m": m, "role": a["role"], "acc": bool(a["accepted"]), "user": p["username"]})
        for n, z in (json.loads(a["scores"]) if a["scores"] else {}).items():
            det_scores.setdefault(n, {"gen": [], "imp": []})[key].append(z)

    rows = []
    for uid, p in per.items():
        sess = [{"no": s, "n": len(v), "median_s": float(np.median(v))} for s, v in sorted(p["sessions"].items())]
        ec = eer_curve(p["gm"], p["im"])
        rows.append({"username": p["username"], "n_enrol": p["n_enrol"], "n_sessions": len(sess), "sessions": sess,
                     "speed": float(np.median([x for v in p["sessions"].values() for x in v])) if p["n_enrol"] else None,
                     "gen_n": p["gen"]["n"], "fnmr": _rate(p["gen"]), "imp_n": p["imp"]["n"], "fmr": _rate(p["imp"]),
                     "eer": ec["eer"] if ec else None, "wrong_pw": p["wrong_pw"]})

    overall = eer_curve(gm, im)
    dets = {n: (eer_curve(v["gen"], v["imp"]) or {}).get("eer") for n, v in det_scores.items()}
    return {
        "n_users": len(users), "n_enrol": len(samp), "n_attempts": len(att), "wrong_pw": wrong,
        "rates": {k: {"gen_n": v["gen"]["n"], "fnmr": _rate(v["gen"]), "imp_n": v["imp"]["n"], "fmr": _rate(v["imp"])} for k, v in tot.items()},
        "eer": overall["eer"] if overall else None,
        "curve": {"fmr": overall["fmr"], "fnmr": overall["fnmr"]} if overall else None,
        "det_eer": dets, "users": rows, "gen_margins": gm, "imp_margins": im, "timeline": timeline,
    }
