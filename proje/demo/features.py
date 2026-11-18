"""Browser key events -> CMU-style timing vector.

The CMU benchmark records, for a password of n characters followed by Return, the vector
H.k1, DD.k1.k2, UD.k1.k2, H.k2, ..., H.Return   (n+1 hold, n down-down, n up-down = 3n+1 values, seconds).
For ".tie5Roanl" (n=10) this gives the same 31 columns as DSL-StrongPasswordData.csv. Modifier keys (Shift etc.)
are not separate keys: like CMU's "Shift.r", a shifted character is one keystroke.
"""
MODIFIERS = {"Shift", "Control", "Alt", "Meta", "CapsLock", "AltGraph", "Fn", "Tab"}


class EntryError(ValueError):
    pass


def events_to_features(events):
    """events: [{"k": key, "d": down_ms, "u": up_ms}, ...] in key-down order, last one = Enter.
    Returns (typed_text, feature_list, column_names)."""
    ev = [e for e in events if e.get("k") not in MODIFIERS]
    if len(ev) < 2 or ev[-1].get("k") != "Enter":
        raise EntryError("entry must end with Enter")
    for e in ev:
        if not isinstance(e.get("d"), (int, float)) or not isinstance(e.get("u"), (int, float)) or e["u"] < e["d"]:
            raise EntryError("incomplete key event (key still held or missing key-up)")
        if e["k"] == "Enter":
            continue
        if len(e["k"]) != 1:
            raise EntryError(f"editing key '{e['k']}' used: please retype the whole password")
    if any(e["k"] == "Enter" for e in ev[:-1]):
        raise EntryError("Enter pressed early")
    if any(ev[i + 1]["d"] < ev[i]["d"] for i in range(len(ev) - 1)):
        raise EntryError("events out of order")
    text = "".join(e["k"] for e in ev[:-1])
    feats, names = [], []
    name = lambda k: "Return" if k == "Enter" else k
    for i, e in enumerate(ev):
        feats.append((e["u"] - e["d"]) / 1000.0)
        names.append(f"H.{name(e['k'])}")
        if i + 1 < len(ev):
            nx = ev[i + 1]
            feats.append((nx["d"] - e["d"]) / 1000.0)
            names.append(f"DD.{name(e['k'])}.{name(nx['k'])}")
            feats.append((nx["d"] - e["u"]) / 1000.0)
            names.append(f"UD.{name(e['k'])}.{name(nx['k'])}")
    total = (ev[-1]["u"] - ev[0]["d"]) / 1000.0
    if total > 30:
        raise EntryError("entry took longer than 30 s, please type it again in one go")
    return text, feats, names
