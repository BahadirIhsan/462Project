// Captures key-down / key-up times (event.timeStamp, ms) for one password entry ending with Enter.
// Like the CMU study, an entry with an editing key (Backspace, arrows...) is discarded and must be retyped.
const MODS = new Set(["Shift", "Control", "Alt", "Meta", "CapsLock", "AltGraph", "Fn", "Tab"]);

function keyCapture(input, { onEntry, onReset, onKey }) {
  let events = [], pending = {};
  const reset = (why) => {
    events = []; pending = {}; input.value = "";
    if (why && onReset) onReset(why);
  };
  input.addEventListener("keydown", (e) => {
    if (e.isComposing || MODS.has(e.key)) return;
    if (e.repeat) { e.preventDefault(); return; }
    if (e.key === "Enter") {
      e.preventDefault();
      if (!events.length) return;
      const ev = { k: "Enter", d: e.timeStamp, u: null };
      events.push(ev); pending[e.code] = ev;
      return;
    }
    if (e.key.length !== 1) { e.preventDefault(); reset(`"${e.key}" pressed: entry discarded, type the whole password again`); return; }
    if (events.length && events[events.length - 1].k === "Enter") { e.preventDefault(); return; }
    const ev = { k: e.key, d: e.timeStamp, u: null };
    events.push(ev); pending[e.code] = ev;
    if (onKey) onKey(events.length);
  });
  input.addEventListener("keyup", (e) => {
    const ev = pending[e.code];
    if (ev && ev.u === null) { ev.u = e.timeStamp; delete pending[e.code]; }
    if (ev && ev.k === "Enter") finish();
  });
  const finish = () => {
    const typed = input.value;
    const done = () => {
      if (events.some((x) => x.u === null)) { reset("a key was still held down when Enter was released, please retype"); return; }
      const text = events.filter((x) => x.k !== "Enter").map((x) => x.k).join("");
      if (text !== typed) { reset("the text field was edited during typing, please retype"); return; }
      const out = events.map((x) => ({ k: x.k, d: +x.d.toFixed(3), u: +x.u.toFixed(3) }));
      reset(null);
      onEntry(out);
    };
    if (events.some((x) => x.u === null)) setTimeout(done, 250); else done();
  };
  for (const t of ["paste", "drop", "cut"]) input.addEventListener(t, (e) => { e.preventDefault(); reset("paste is not allowed: the rhythm must be typed"); });
  input.addEventListener("blur", () => { if (events.length) reset("focus lost, entry discarded"); });
  return { reset };
}

async function post(url, body) {
  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  let j; try { j = await r.json(); } catch { j = { ok: false, error: `server error ${r.status}` }; }
  return j;
}

// ---------- charts (inline SVG, no external libraries) ----------
const NS = "http://www.w3.org/2000/svg";
function el(tag, attrs, parent, text) {
  const n = document.createElementNS(NS, tag);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  if (text !== undefined) n.textContent = text;
  if (parent) parent.appendChild(n);
  return n;
}
// Template mean ± 1 SD (band) vs. this entry (dot) for hold (H) and down-down (DD) times.
// Keys are labelled by position (1, 2, ..., ⏎), never by character, so the chart does not reveal the password.
// Feature layout (CMU): for key i -> H at 3i, DD(i→i+1) at 3i+1, UD at 3i+2; last value = H.Enter.
function rhythmChart(box, mean, sd, entry) {
  box.innerHTML = "";
  const nk = (mean.length + 2) / 3;
  const lab = (i) => (i === nk - 1 ? "⏎" : String(i + 1));
  const groups = [
    ["H", "hold time, key down → up", [...Array(nk).keys()].map((i) => [lab(i), 3 * i])],
    ["DD", "down-down latency, key → next key", [...Array(nk - 1).keys()].map((i) => [`${lab(i)}→${lab(i + 1)}`, 3 * i + 1])],
  ];
  for (const [g, label, idx] of groups) {
    const W = Math.max(600, idx.length * 46), Hh = 150, padL = 34, padB = 26, padT = 20;
    const vals = idx.flatMap(([, i]) => [mean[i] + sd[i], entry ? entry[i] : 0]);
    const ymax = Math.max(0.05, ...vals) * 1.1;
    const y = (v) => padT + (Hh - padT - padB) * (1 - Math.max(0, v) / ymax);
    const svg = el("svg", { viewBox: `0 0 ${W} ${Hh}`, width: W, height: Hh, role: "img" });
    el("text", { x: 2, y: 11 }, svg, `${g}: ${label} (ms) · band = your template mean ± 1 SD` + (entry ? " · dot = this entry (red if > 2 SD off)" : ""));
    for (const t of [0, ymax / 2, ymax]) {
      el("line", { x1: padL, x2: W, y1: y(t), y2: y(t), class: "axis" }, svg);
      el("text", { x: 2, y: y(t) + 3 }, svg, Math.round(t * 1000));
    }
    const step = (W - padL) / idx.length;
    idx.forEach(([name, i], j) => {
      const cx = padL + step * (j + 0.5);
      const lo = Math.max(0, mean[i] - sd[i]), hi = mean[i] + sd[i];
      el("rect", { x: cx - step * 0.3, width: step * 0.6, y: y(hi), height: Math.max(1, y(lo) - y(hi)), rx: 3, class: "band" }, svg);
      el("line", { x1: cx - step * 0.3, x2: cx + step * 0.3, y1: y(mean[i]), y2: y(mean[i]), stroke: "currentColor", "stroke-opacity": 0.5 }, svg);
      if (entry) {
        const off = Math.abs(entry[i] - mean[i]) > 2 * sd[i];
        const c = el("circle", { cx, cy: y(entry[i]), r: 4.5, class: off ? "off" : "ok" }, svg);
        el("title", {}, c, `${g} ${name}: ${(entry[i] * 1000).toFixed(0)} ms (template ${(mean[i] * 1000).toFixed(0)} ± ${(sd[i] * 1000).toFixed(0)})`);
      }
      el("text", { x: cx, y: Hh - 8, "text-anchor": "middle" }, svg, name);
    });
    const wrap = document.createElement("div"); wrap.className = "chart"; wrap.appendChild(svg); box.appendChild(wrap);
  }
}

// Held-out genuine fused scores (histogram), threshold (dashed) and this attempt (marker).
function scoreStrip(box, held, fused, th) {
  box.innerHTML = "";
  const W = 560, H = 120, padL = 10, padR = 10, padB = 28;
  const lo = Math.min(-3, ...held, Math.max(fused, -6)), hi = Math.max(th + 1.5, ...held) + 0.5;
  const fx = Math.min(Math.max(fused, lo), hi), clipped = fx !== fused;
  const x = (v) => padL + (W - padL - padR) * (v - lo) / (hi - lo);
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", role: "img" });
  const nb = 30, bins = new Array(nb).fill(0);
  held.forEach((v) => bins[Math.min(nb - 1, Math.floor((v - lo) / (hi - lo) * nb))]++);
  const bm = Math.max(...bins);
  bins.forEach((b, i) => {
    const h = (H - padB - 14) * b / bm;
    el("rect", { x: x(lo + (hi - lo) * i / nb) + 1, width: (W - padL - padR) / nb - 2, y: H - padB - h, height: h, class: "hist" }, svg);
  });
  el("line", { x1: padL, x2: W - padR, y1: H - padB, y2: H - padB, class: "axis" }, svg);
  el("line", { x1: x(th), x2: x(th), y1: 8, y2: H - padB + 4, class: "th" }, svg);
  el("text", { x: x(th) + 4, y: 30 }, svg, `threshold ${th.toFixed(2)}`);
  el("path", { d: `M${x(fx)},${H - padB + 2} l-7,12 h14 z`, class: fused <= th ? "ok" : "off" }, svg);
  el("text", { x: Math.min(Math.max(x(fx), 70), W - 95), y: H - 2, "text-anchor": "middle" }, svg, `this attempt ${fused.toFixed(2)}${clipped ? " (off scale →)" : ""}`);
  el("text", { x: padL, y: 12 }, svg, "your own held-out entries (green) · lower = more like you");
  box.appendChild(svg);
}
