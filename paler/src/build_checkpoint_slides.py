"""Phase 3 checkpoint slides (PDF). Numbers and figures come from proje/checkpoint.py -> proje/results/checkpoint.json."""
import base64, json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "proje", "results")
C = json.load(open(os.path.join(RES, "checkpoint.json")))
D, Q, J, E = C["dataset"], C["quality"], C["rejection"], C["effect_C2"]
RX = C["rejected_example"]


def img(name, h):
    b = base64.b64encode(open(os.path.join(RES, name), "rb").read()).decode()
    return f'<img src="data:image/png;base64,{b}" style="height:{h}mm">'


def pct(x, d=1): return f"{x*100:.{d}f}%"


CSS = """
@page { size: 338.67mm 190.5mm; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; font-family: 'Helvetica Neue', Arial, sans-serif; color: #15202e; }
.s { width: 338.67mm; height: 190.5mm; padding: 11mm 15mm 9mm; page-break-after: always; position: relative; overflow: hidden; }
.s:last-child { page-break-after: auto; }
h1 { font-size: 25pt; margin: 0 0 5mm; color: #12306b; }
h2 { font-size: 21pt; margin: 0 0 4mm; color: #12306b; border-bottom: 2px solid #1f5fbf; padding-bottom: 2mm; }
p, li { font-size: 13.5pt; line-height: 1.38; } ul { margin: 1mm 0 0 6mm; padding: 0; } li { margin: 1.2mm 0; }
.ft { position: absolute; bottom: 4.5mm; left: 15mm; right: 15mm; font-size: 9pt; color: #7a8699; display: flex; justify-content: space-between; }
table { border-collapse: collapse; font-size: 12.5pt; } th { background: #eaf0fb; text-align: left; } th, td { border: 1px solid #ccd6ea; padding: 1.4mm 3mm; }
.row { display: flex; gap: 8mm; align-items: flex-start; } .c { text-align: center; }
.ok { color: #1b7f3b; font-weight: bold; } .k { color: #c0392b; font-weight: bold; } .note { font-size: 11.5pt; color: #46536a; }
.big { font-size: 30pt; font-weight: bold; color: #12306b; } .tile { border: 1px solid #ccd6ea; border-radius: 3mm; padding: 3mm 5mm; background: #f6f9ff; flex: 1; }
.tile span { display: block; font-size: 11pt; color: #46536a; }
.flow { display: flex; gap: 3mm; align-items: stretch; margin: 2mm 0 5mm; } .flow div { flex: 1; border: 1.5px solid #1f5fbf; border-radius: 2.5mm; padding: 2.5mm; font-size: 11.5pt; background: #f3f7ff; }
.flow b { display: block; color: #12306b; font-size: 12.5pt; } .flow i { align-self: center; font-style: normal; color: #1f5fbf; font-size: 16pt; }
"""
FOOT = lambda n: f'<div class="ft"><span>BİL462 · A5 Keystroke Dynamics · Phase 3 Data &amp; Preprocessing Checkpoint</span><span>Herdem · Öztürk · {n}/9</span></div>'

ck = "".join(f'<tr><td>{k}</td><td class="ok">{"pass" if v["pass"] else "FAIL"}</td><td>{v["detail"]}</td></tr>' for k, v in C["checks"].items())
rj = "".join(f'<tr><td class="c">{k}</td><td class="c">{v["C2_rejected"]} / {v["C2_total"]} ({pct(v["C2_rejected"]/v["C2_total"])})</td>'
             f'<td class="c">{v["C2_users_affected"]} / 41</td><td class="c">{v["C2_max_per_user"]}</td><td class="c">{v["C1_rejected"]} / {v["C1_total"]}</td></tr>' for k, v in J.items())
ef = "".join(f'<tr><td>{n}</td><td class="c">{pct(v["eer_all"])}</td><td class="c">{pct(v["eer_filtered"])}</td>'
             f'<td class="c">{v["diff"]*100:+.2f} pp [{v["diff_ci95"][0]*100:+.2f}, {v["diff_ci95"][1]*100:+.2f}]</td></tr>' for n, v in E.items())
sess = D["session_median_total_s"]

HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Phase 3 Checkpoint – A5</title><style>{CSS}</style></head><body>

<div class="s" style="display:flex;flex-direction:column;justify-content:center">
<div class="note" style="font-size:13pt">BİL462 Biometric Recognition · Project Phase 3 · Data &amp; Preprocessing Checkpoint · Topic A5</div>
<h1 style="font-size:31pt;margin-top:4mm">Password-Typing Verification Across Sessions<br>on the CMU Keystroke Benchmark</h1>
<p style="font-size:16pt">Bahadır İhsan Herdem (221101034) · Ömer Efe Öztürk (221101059)</p>
<p class="note" style="margin-top:8mm">Covered today: ① dataset statistics · ② sample preprocessing outputs · ③ observed quality issues · ④ samples rejected during preprocessing<br>
Data in hand: <b>DSL-StrongPasswordData.csv</b> from cs.cmu.edu/~keystroke (Killourhy &amp; Maxion, DSN 2009). Everything shown is reproduced by <code>proje/checkpoint.py</code>.</p>
{FOOT(1)}</div>

<div class="s"><h2>① Dataset statistics</h2>
<div class="row" style="margin-bottom:4mm">
<div class="tile"><div class="big">{D['subjects']}</div><span>subjects ({D['subject_ids']})</span></div>
<div class="tile"><div class="big">{D['sessions']} × {D['reps_per_session']}</div><span>sessions × repetitions, ≥ 1 day apart</span></div>
<div class="tile"><div class="big">{D['entries']:,}</div><span>password entries, 0 missing</span></div>
<div class="tile"><div class="big">{D['features']}</div><span>features: 11 hold (H), 10 down-down (DD), 10 up-down (UD)</span></div>
<div class="tile"><div class="big">{D['total_s']['median']:.2f} s</div><span>median time to type <b>.tie5Roanl</b>+Enter</span></div>
</div>
{img('cp_stats.png', 84)}
<p class="note" style="margin-top:1mm">Mean ± SD: H {D['mean_ms']['H']:.0f} ± {D['sd_ms']['H']:.0f} ms, DD {D['mean_ms']['DD']:.0f} ± {D['sd_ms']['DD']:.0f} ms, UD {D['mean_ms']['UD']:.0f} ± {D['sd_ms']['UD']:.0f} ms ·
per-subject median entry time {D['subject_median_total_s']['min']:.2f}–{D['subject_median_total_s']['max']:.2f} s · session median {sess['1']:.2f} s (S1) → {sess['8']:.2f} s (S8); {D['subjects_faster_s8_than_s1']}/51 subjects faster in S8 ·
split: {D['tune_users']} tuning subjects (grey) / {D['eval_users']} evaluation subjects.</p>
{FOOT(2)}</div>

<div class="s"><h2>Preprocessing pipeline and validation checks</h2>
<div class="flow">
<div><b>Load CSV</b>subject, session, rep + 31 timings (s)</div><i>→</i>
<div><b>Validate</b>structure, completeness, physical consistency (table)</div><i>→</i>
<div><b>Index</b>array [subject][session 1–8][rep 1–50][31]</div><i>→</i>
<div><b>Enrolment-only rejection</b>drop atypically slow training entries (slide ④)</div><i>→</i>
<div><b>Per-user normalisation</b>scaled Manhattan: ÷ MAD · SVM: z-score · fitted on enrolment only</div>
</div>
<div class="row"><div style="flex:1.35"><table><tr><th>Check</th><th>Result</th><th>Detail</th></tr>{ck}</table></div>
<div style="flex:1"><ul>
<li>No keystroke detection step exists: the CMU recorder accepted an entry only if the 10 characters were typed <b>correctly</b>; entries with typos were retyped and not stored.</li>
<li>Timestamps from an external reference clock (± 200 µs, paper §4.2); values stored with 0.1 ms resolution.</li>
<li>Test entries are <b>never</b> filtered or used to fit normalisation.</li></ul></div></div>
{FOOT(3)}</div>

<div class="s"><h2>② Sample preprocessing output: one entry → one 31-D vector</h2>
{img('cp_entry.png', 96)}
<div class="row" style="margin-top:2mm"><p style="flex:1;margin:0">From key-down / key-up events: <b>H</b> = up − down of the same key, <b>DD</b> = down(next) − down(this),
<b>UD</b> = down(next) − up(this) = DD − H. Shift+R counts as one keystroke (R), Enter is the 11th key.
The vector is stored in key order: H.period, DD.period.t, UD.period.t, H.t, … , H.Return.</p></div>
{FOOT(4)}</div>

<div class="s"><h2>② Sample preprocessing output: one user's enrolment template</h2>
{img('cp_vectors.png', 96)}
<p style="margin-top:2mm">s002, condition C2 (cross-session): 200 enrolment entries = sessions 1–4 (white lines). Raw features differ by an order of magnitude (hold ≈ 90 ms, pauses before <b>5</b> and <b>R</b> ≥ 600 ms),
so raw Manhattan distance is dominated by a few long latencies. After per-user z-scoring every feature has equal weight; the early entries (left) are visibly slower, the drift we measure later.</p>
{FOOT(5)}</div>

<div class="s"><h2>③ Observed quality issues</h2>
<div class="row"><div style="flex:1.2">{img('cp_quality.png', 80)}</div></div>
<ul style="columns:2;column-gap:10mm">
<li><b>Key overlap:</b> {pct(Q['neg_ud_frac'])} of UD values are negative ({pct(Q['neg_ud_entries_frac'],0)} of entries have ≥1); per subject {pct(Q['neg_ud_subject_range'][0],0)}–{pct(Q['neg_ud_subject_range'][1],0)}. Real typing behaviour, <b>kept</b>.</li>
<li><b>Long pauses:</b> {Q['entries_any_dd_gt_2s']} entries contain a latency &gt; 2 s; longest entry {D['total_s']['max']:.1f} s ({Q['longest_entry']['subject']}, S{Q['longest_entry']['sessionIndex']}, one pause of {Q['max_single_dd_s']:.1f} s).</li>
<li><b>Practice effect / drift:</b> median entry time falls {sess['1']:.2f} → {sess['8']:.2f} s; within-session variation is also large (mean CV {D['mean_within_session_cv_total']:.2f}).</li>
<li><b>Redundant features:</b> DD = H + UD exactly, so a user's 31×31 covariance has rank {Q['mahalanobis_cov_rank']} → Mahalanobis needs a ridge term.</li>
<li><b>Lab conditions:</b> one laptop + external keyboard, 50 entries in a row; browser timing in our demo will differ, so demo accuracy is not evidence.</li>
<li><b>Ground truth limits:</b> subject IDs have gaps (5 absent IDs, as released); typo behaviour is not recorded.</li></ul>
{FOOT(6)}</div>

<div class="s"><h2>④ Samples rejected during preprocessing</h2>
<p style="margin:0 0 2mm"><b>Rule</b> (enrolment entries only): reject an entry whose total time exceeds <span class="k">k × the user's own median</span> over that user's enrolment entries. Chosen value <b>k = 2</b>; computed without any test data.</p>
<div class="row" style="align-items:center"><table style="font-size:11pt;white-space:nowrap"><tr><th>k</th><th>C2 rejected</th><th>users affected</th><th>max / user</th><th>C1 rejected</th></tr>{rj}</table>
<p class="note" style="flex:1;margin:0">C2 = 41 users × 200 enrolment entries (S1–S4); C1 = 41 × 8 sessions × 25 entries.<br>Rejections fall mostly on session 1 (first contact with the password).<br>
Largest rejected entry: {RX['subject']} S{RX['session']} rep {RX['rep']}: {RX['total_s']:.1f} s vs. user median {RX['user_median_s']:.1f} s ({RX['max_dd_feature']} = {RX['max_dd_s']:.1f} s).</p></div>
<div class="c" style="margin-top:3mm">{img('cp_reject.png', 72)}</div>
{FOOT(7)}</div>

<div class="s"><h2>④ Does rejection matter? First check on C2 (cross-session)</h2>
<table style="margin-bottom:4mm"><tr><th>Detector (41 eval. users)</th><th>mean EER, all enrolment</th><th>mean EER, k = 2 rejection</th><th>difference [95% CI, paired subject bootstrap]</th></tr>{ef}</table>
<ul><li>Removing ≈ 1% of enrolment entries lowers EER by only 0.1–0.25 percentage points; the CI includes 0 for three of four detectors.</li>
<li>The error is dominated by <b>drift between sessions</b>, not by a few bad entries; cleaning cannot fix that.</li>
<li><b>Decision:</b> headline results use all entries (same as the reference study, needed for the C3 comparison with Killourhy &amp; Maxion); k = 2 rejection is reported as a separate, labelled variant.</li></ul>
{FOOT(8)}</div>

<div class="s"><h2>Status and next steps</h2>
<ul><li><b>Done:</b> data in hand and validated; preprocessing + rejection module (<code>keystroke/preprocess.py</code>); 3 distance detectors + one-class SVM (ν = 0.05, γ = 0.03 from 10 tuning subjects); reference replication matches the paper (scaled Manhattan 9.6%, Manhattan 15.3%).</li>
<li><b>By Nov 27 (milestone):</b> score distributions and DET curves for within-session (C1) vs. cross-session (C2), per-user EER, bootstrap CIs; drift curve S1 → S8.</li>
<li><b>Then:</b> report score fusion over k = 3, 5, 10 consecutive entries (already implemented); optional Siamese embedding trained on subjects disjoint from evaluation; localhost login demo (team data only after instructor approval, never mixed into evaluation).</li>
<li><b>Open question for the instructor:</b> approval to collect the two team members' own typing data for the demo.</li></ul>
<p class="note" style="margin-top:8mm">AI use: Claude Code (Anthropic) assisted with analysis code, figures and slide layout; all numbers were regenerated from our scripts and checked against the CSV and the reference paper.</p>
{FOOT(9)}</div>
</body></html>"""

out_html = os.path.join(HERE, "checkpoint_slides.html")
open(out_html, "w").write(HTML)
pdf = os.path.join(HERE, "..", "PA3_Checkpoint_Slides_221101034_221101059.pdf")
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", "file://" + out_html], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(os.path.abspath(pdf))
