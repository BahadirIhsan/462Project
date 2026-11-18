"""Final presentation slides (PDF, 16:9, 10 minutes). Numbers come from proje/results/*.json (proje/reproduce.py)."""
import base64, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "proje", "results")
R = json.load(open(os.path.join(RES, "results.json")))
F = json.load(open(os.path.join(RES, "final.json")))
C = json.load(open(os.path.join(RES, "checkpoint.json")))
S, FP, EA, D = R["summary"], F["fold_protocol"], F["error_analysis"], C["dataset"]
BASE = ["Manhattan", "Scaled Manhattan", "Mahalanobis", "One-class SVM"]
SIA, FUS = "Siamese embedding", "Fusion (SM+SVM+Siamese)"
REF = {"Manhattan": .153, "Scaled Manhattan": .096, "Mahalanobis": .110, "One-class SVM": .102}
N = 14


def p(x, d=1): return f"{x * 100:.{d}f}"
def ci(c): return f"[{p(c[0])}, {p(c[1])}]"


def img(name, h, folder=RES, extra=""):
    b = base64.b64encode(open(os.path.join(folder, name), "rb").read()).decode()
    return f'<img src="data:image/png;base64,{b}" style="height:{h}mm;{extra}">'


CSS = """
@page { size: 338.67mm 190.5mm; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; font-family: 'Helvetica Neue', Arial, sans-serif; color: #15202e; }
.s { width: 338.67mm; height: 190.5mm; padding: 11mm 15mm 9mm; page-break-after: always; position: relative; overflow: hidden; }
.s:last-child { page-break-after: auto; }
h1 { font-size: 27pt; margin: 0 0 5mm; color: #12306b; }
h2 { font-size: 21pt; margin: 0 0 4mm; color: #12306b; border-bottom: 2px solid #1f5fbf; padding-bottom: 2mm; }
p, li { font-size: 13.5pt; line-height: 1.38; } ul { margin: 1mm 0 0 6mm; padding: 0; } li { margin: 1.4mm 0; }
.ft { position: absolute; bottom: 4.5mm; left: 15mm; right: 15mm; font-size: 9pt; color: #7a8699; display: flex; justify-content: space-between; }
table { border-collapse: collapse; font-size: 12.5pt; } th { background: #eaf0fb; text-align: center; } th, td { border: 1px solid #ccd6ea; padding: 1.5mm 3mm; }
td { text-align: center; } td:first-child { text-align: left; }
.row { display: flex; gap: 8mm; align-items: flex-start; } .c { text-align: center; }
.note { font-size: 11.5pt; color: #46536a; } .k { color: #c0392b; font-weight: bold; } .g { color: #1b7f3b; font-weight: bold; }
.big { font-size: 30pt; font-weight: bold; color: #12306b; } .tile { border: 1px solid #ccd6ea; border-radius: 3mm; padding: 3mm 5mm; background: #f6f9ff; flex: 1; }
.tile span { display: block; font-size: 11.5pt; color: #46536a; }
.take { border-left: 5px solid #1f5fbf; background: #f3f7ff; padding: 3mm 5mm; font-size: 14pt; margin-top: 4mm; }
.flow { display: flex; gap: 3mm; align-items: stretch; margin: 2mm 0 5mm; } .flow div { flex: 1; border: 1.5px solid #1f5fbf; border-radius: 2.5mm; padding: 2.5mm; font-size: 11.5pt; background: #f3f7ff; }
.flow b { display: block; color: #12306b; font-size: 12.5pt; } .flow i { align-self: center; font-style: normal; color: #1f5fbf; font-size: 16pt; }
tr.hl td { background: #fff7e6; font-weight: bold; }
"""
FOOT = lambda n: f'<div class="ft"><span>BİL462 · A5 Keystroke Dynamics · Final presentation</span><span>Herdem · Öztürk · {n}/{N}</span></div>'

t_ref = "".join(f"<tr><td>{n}</td><td>{p(REF[n])}</td><td><b>{p(S[n]['C3_makale_protokolu']['eer_mean'])}</b></td><td>{ci(S[n]['C3_makale_protokolu']['ci95'])}</td></tr>" for n in BASE)
t_main = "".join(
    f"<tr{' class=hl' if n == FUS else ''}><td>{n}</td><td>{p(FP[n]['C1']['eer_mean']) if 'C1' in FP[n] else '–'}</td><td><b>{p(FP[n]['C2']['eer_mean'])}</b> {ci(FP[n]['C2']['ci95'])}</td>"
    f"<td>{(('+' if FP[n]['C2_minus_C1'][0] >= 0 else '') + p(FP[n]['C2_minus_C1'][0])) if 'C2_minus_C1' in FP[n] else '–'}</td><td>{p(FP[n]['fusion_k']['5']['eer_mean'])}</td></tr>"
    for n in BASE + [SIA, FUS])
op = FP["Scaled Manhattan"]["operational"]
sm, sv, si = FP["Scaled Manhattan"], FP["One-class SVM"], FP[SIA]

HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Final – A5</title><style>{CSS}</style></head><body>

<div class="s" style="display:flex;flex-direction:column;justify-content:center">
<div class="note" style="font-size:13pt">BİL462 Biometric Recognition · Project Phase 5 · Final Presentation · Topic A5</div>
<h1 style="font-size:32pt;margin-top:4mm">Password-Typing Verification Across Sessions<br>Distance detectors, a one-class SVM and a Siamese embedding</h1>
<p style="font-size:16pt">Bahadır İhsan Herdem (221101034) · Ömer Efe Öztürk (221101059)</p>
<p class="note" style="margin-top:8mm">CMU Keystroke Dynamics Benchmark (Killourhy &amp; Maxion, DSN 2009) · all numbers reproduced by <code>python reproduce.py</code> · live demo at the end</p>
{FOOT(1)}</div>

<div class="s"><h2>Problem and question</h2>
<div class="row"><div style="flex:1.2"><ul>
<li>A password can be stolen; <b>how</b> it is typed (hold times, latencies) is harder to copy → a free second factor, no extra hardware.</li>
<li>Static verification: everyone types the same password <code>.tie5Roanl</code>; a per-user detector accepts or rejects one entry.</li>
<li>Typing rhythm <b>drifts</b> from day to day → within-session results can be optimistic.</li>
<li><b>Question (A5):</b> how well do simple and learned detectors separate users, and how much do they lose across sessions?</li></ul></div>
<div style="flex:1.1">{img('cp_entry.png', 0, extra='height:auto;width:100%')}</div></div>
<div class="take">Since the checkpoint: C1/C2 results with CIs · template-ageing curve · Siamese embedding (cross-fitted) · detector and multi-entry fusion · error analysis · login demo.</div>
{FOOT(2)}</div>

<div class="s"><h2>Data and evaluation protocol</h2>
<div class="row" style="margin-bottom:3mm">
<div class="tile"><div class="big">{D['subjects']}</div><span>subjects · 8 sessions × 50 entries</span></div>
<div class="tile"><div class="big">31</div><span>features: 11 H, 10 DD, 10 UD</span></div>
<div class="tile"><div class="big">10 / 41</div><span>tuning subjects / evaluation subjects (fixed seed)</span></div>
<div class="tile"><div class="big">{p(1 - D['session_median_total_s']['8'] / D['session_median_total_s']['1'], 0)}%</div><span>faster in session 8 than in session 1 (median)</span></div></div>
<table style="width:100%"><tr><th>Condition</th><th>Enrolment</th><th>Genuine test</th><th>Impostors</th><th>Comparisons</th></tr>
<tr><td><b>C1</b> within-session</td><td>reps 1–25 of a session</td><td>reps 26–50, same session</td><td>40 others, same session</td><td>8,200 / 328,000</td></tr>
<tr><td><b>C2</b> cross-session</td><td>sessions 1–4 (200)</td><td>sessions 5–8</td><td>40 others, sessions 5–8</td><td>8,200 / 328,000</td></tr>
<tr><td>Ageing</td><td>session 1, 25 entries</td><td>session t = 1…8</td><td>others, session t</td><td>per t: 1,025 / 41,000</td></tr>
<tr><td>Fold (for Siamese)</td><td>as C1/C2</td><td>as C1/C2</td><td>only same fold → unseen</td><td>≈ 59,000 imp. in C2</td></tr>
<tr><td>C3 replication</td><td>first 200</td><td>last 200</td><td>first 5 of each other</td><td>10,200 / 12,750</td></tr></table>
<p class="note">Metrics: DET (main curve), mean per-user EER, FNMR at fixed FMR (≥ 0.1%, the resolution 8,000 impostor scores per user support), 95% CI by bootstrapping <b>subjects</b> (2,000×).
Nothing is tuned on evaluation subjects; thresholds come from enrolment data only.</p>
{FOOT(3)}</div>

<div class="s"><h2>System: one pipeline for evaluation and demo</h2>
<div class="flow"><div><b>Key events</b>down / up times</div><i>→</i><div><b>31 features</b>H, DD, UD (s)</div><i>→</i><div><b>Enrolment</b>user's earlier entries only</div><i>→</i>
<div><b>Detector</b>anomaly score (higher = less like you)</div><i>→</i><div><b>Fusion</b>z-norm from enrolment; mean of detectors / k entries</div><i>→</i><div><b>Decision</b>score ≤ threshold</div></div>
<div class="row"><div style="flex:1"><table style="width:100%"><tr><th>Detector</th><th>What it learns</th></tr>
<tr><td>Manhattan</td><td>mean vector; L1 distance</td></tr>
<tr><td>Scaled Manhattan</td><td>mean + mean abs. deviation per feature</td></tr>
<tr><td>Mahalanobis</td><td>mean + covariance (ridge: rank 21)</td></tr>
<tr><td>One-class SVM</td><td>RBF boundary around genuine entries; ν={R['svm_params']['nu']}, γ={R['svm_params']['gamma']} from tuning subjects</td></tr>
<tr><td>Siamese embedding</td><td>shared MLP 31→128→128→128, batch-hard triplet loss; template = mean embedding</td></tr></table></div>
<div style="flex:.9"><ul><li><b>Shared model rule:</b> the Siamese net is trained on people who are <b>not</b> evaluated → 5-fold cross-fitting; test impostors also unseen.</li>
<li>Siamese size/steps chosen on the 10 tuning subjects (18 configs); longer training over-fits.</li>
<li>Distance detectors + metrics + bootstrap written by us (numpy); sklearn SVM solver; PyTorch.</li></ul></div></div>
{FOOT(4)}</div>

<div class="s"><h2>Sanity check: we reproduce the reference result</h2>
<div class="row"><div style="flex:1"><table style="width:100%"><tr><th>Detector</th><th>Killourhy &amp; Maxion 2009</th><th>Ours (C3)</th><th>95% CI</th></tr>{t_ref}</table>
<p class="note">Same protocol: train first 200 entries, test last 200, impostors = first 5 entries of the other 50 subjects. SVM on the 41 evaluation subjects only (tuned on the other 10).</p></div>
<div style="flex:.8"><ul><li>Distance detectors match to <b>≤ 0.1 pp</b> → features, detectors and EER code are right.</li>
<li>Our SVM is 1.4 pp worse; the reference value is inside our CI.</li>
<li>Same ranking everywhere: scaled Manhattan &lt; Mahalanobis &lt; Manhattan → <b>scaling by variability matters most</b>.</li></ul></div></div>
<div class="take">But C3 tests impostors on their first, unpractised entries. Our C1/C2 use practised impostors from the same sessions → harder and more realistic.</div>
{FOOT(5)}</div>

<div class="s"><h2>Main result: within vs. across sessions</h2>
<div class="row"><div style="flex:1.05"><table style="width:100%"><tr><th>Detector</th><th>C1 EER %</th><th>C2 EER % [95% CI]</th><th>C2 − C1 pp</th><th>C2, k=5</th></tr>{t_main}</table>
<p class="note">Fold protocol (same data for all detectors, impostors unseen). 41 subjects.</p></div>
<div style="flex:.95">{img('fin_det_c2_fold.png', 120)}</div></div>
{FOOT(6)}</div>

<div class="s"><h2>Learned models: best today, worst tomorrow</h2>
<div class="row"><div style="flex:1"><ul>
<li><b>Siamese</b> is the best detector <i>within</i> a session: <span class="g">{p(si['C1']['eer_mean'])}%</span> vs. {p(sm['C1']['eer_mean'])}% (scaled Manhattan).</li>
<li>Across sessions it falls to <span class="k">{p(si['C2']['eer_mean'])}%</span>: the largest loss of all detectors (+{p(si['C2_minus_C1'][0])} pp, CI {ci(si['C2_minus_C1'][1:])}).</li>
<li>Scaled Manhattan also loses (+{p(sm['C2_minus_C1'][0])} pp) <b>although it has 8× more enrolment data</b> in C2.</li>
<li>Mahalanobis improves C1→C2: with 25 entries its covariance is the bottleneck, not drift.</li>
<li>C2: scaled Manhattan, Mahalanobis, SVM and Siamese are <b>statistically tied</b> (~14–16%).</li></ul>
<div class="take">Within-session numbers are optimistic, most of all for the learned embedding.</div></div>
<div style="flex:1.25">{img('fin_scores.png', 0, extra='height:auto;width:100%')}<p class="note">Genuine scores of later sessions move right of the enrolment mean (0): that is drift. Overlap with impostors is large.</p></div></div>
{FOOT(7)}</div>

<div class="s"><h2>Template ageing and real thresholds</h2>
<div class="row"><div style="flex:1.15">{img('fin_ageing_only.png', 112, HERE)}</div>
<div style="flex:1"><ul><li>Enrolment fixed at 25 entries of session 1: EER grows with the gap, e.g. scaled Manhattan {p(sm['drift_eer'][0])}% → {p(sm['drift_eer'][7])}%, Siamese {p(si['drift_eer'][0])}% → {p(si['drift_eer'][7])}%.</li>
<li>Threshold from enrolment only (95th percentile of own held-out scores), applied to sessions 5–8, scaled Manhattan: FNMR {p(op['0.95']['fnmr'])}% but FMR <span class="k">{p(op['0.95']['fmr'])}%</span>.</li>
<li>At FMR 1% about half of genuine entries are rejected.</li></ul>
<div class="take">A deployed system must re-enrol / update the template, or accept many false matches.</div></div></div>
{FOOT(8)}</div>

<div class="s"><h2>What helps: more evidence, not more model</h2>
<div class="row"><div style="flex:1">{img('fin_kfusion_only.png', 112, HERE)}<p class="note">Colours: <span style="color:#8a8f98">■ Manhattan</span> <span style="color:#1b7f3b">■ scaled Manhattan</span> <span style="color:#c0392b">■ Mahalanobis</span> <span style="color:#1f5fbf">■ one-class SVM</span> <span style="color:#8e44ad">■ Siamese</span> <span style="color:#e67e22">■ fusion SM+SVM+Siamese</span></p></div>
<div style="flex:1"><ul><li><b>Detector fusion</b> (SM + SVM + Siamese, z-norm from enrolment): C2 {p(FP[FUS]['C2']['eer_mean'])}% (vs. 15.0%; CI of the gain includes 0). Detectors fail on the <b>same users</b> (Spearman {EA['per_user_eer_rank_corr']['Scaled Manhattan vs One-class SVM']:.2f}).</li>
<li><b>Multi-entry fusion</b> (average k consecutive entries): k=5 → {p(FP[FUS]['fusion_k']['5']['eer_mean'])}%, k=10 → {p(FP[FUS]['fusion_k']['10']['eer_mean'])}%.</li>
<li><b>Multi-session enrolment</b>: C2 with sessions 1–4 beats the 25-entry ageing curve at every later session.</li></ul>
<div class="take">Practical design: one entry normally, ask for another only when the score is borderline (step-up).</div></div></div>
{FOOT(9)}</div>

<div class="s"><h2>Error analysis</h2>
<div class="row"><div style="flex:1"><ul>
<li><b>Few users dominate:</b> {EA['users_eer_below_5pct']}/41 below 5% EER, {EA['users_eer_above_25pct']}/41 above 25%; the 5 worst give {p(EA['share_of_error_from_worst5'], 0)}% of the total error (hard for every detector, "goats").</li>
<li><b>Wolves:</b> median impostor accepted {p(EA['median_wolf_rate'], 0)}% at the EER threshold, but {EA['top_wolves'][0][0]} {p(EA['top_wolves'][0][1], 0)}% and {EA['top_wolves'][1][0]} {p(EA['top_wolves'][1][1], 0)}%.</li>
<li><b>Features:</b> hold times drift most ({EA['feature_shift_by_group']['H']:.2f} SD vs. {EA['feature_shift_by_group']['DD']:.2f} DD); biggest shift at <code>e→5</code> (letter → digit row). All 41 users got faster.</li>
<li>Drift size vs. per-user EER: ρ = {EA['spearman_shift_vs_eer'][0]:.2f} (p = {EA['spearman_shift_vs_eer'][1]:.2f}), not significant → hard users are also inconsistent or similar to others.</li>
<li>Enrolment-only rejection of slow entries: ≤ 0.25 pp gain.</li></ul></div>
<div style="flex:1.15">{img('fin_error.png', 62)}{img('fin_per_user.png', 52)}</div></div>
{FOOT(10)}</div>

<div class="s"><h2>Demo: RhythmGate, password + rhythm login</h2>
<div class="row"><div style="flex:1"><ul>
<li>Flask + SQLite, runs on localhost; browser records key-down/up times; same feature code (CMU rows replayed as key events → identical vectors, unit-tested).</li>
<li>Register → enrol ≥ 15 entries (2 sessions better) → log in. Typos / Backspace discard the entry, as in CMU.</li>
<li>Decision = exactly the report's rule: SM + SVM (+ Siamese for the CMU password), z-norm and threshold from own held-out entries; 3 security levels; k = 1 or 3 entries.</li>
<li><b>Storage:</b> password only as salted scrypt hash; template = timing numbers, no key text; local only; "delete my data" (cascade).</li>
<li>Impostor-test mode: a team-mate types my password; logged, never signs in. Own demo data: team members only, <b>collected with the instructor's approval</b>, never used in the evaluation.</li></ul></div>
<div style="flex:1">{img('demo_impostor_crop.png', 0, HERE, 'height:auto;width:100%;border:1px solid #ccd6ea;border-radius:2mm')}</div></div>
{FOOT(11)}</div>

<div class="s" style="display:flex;flex-direction:column;justify-content:center;align-items:center">
<h1 style="font-size:34pt">Live demo</h1>
<p style="font-size:17pt">1 · enrolled user logs in &nbsp;→&nbsp; 2 · team-mate types the same password (impostor test) &nbsp;→&nbsp; 3 · k = 3 entries &nbsp;→&nbsp; 4 · demo log</p>
<p class="note">Browser timing ≠ CMU clock and only a few trials: the demo illustrates the pipeline, the evaluation is on CMU only.</p>
{FOOT(12)}</div>

<div class="s"><h2>Limitations and conclusions</h2>
<div class="row"><div style="flex:1"><h3 style="color:#12306b;margin:0">Limitations</h3><ul>
<li>41 subjects → CIs of about ±3 pp; small differences unresolved.</li>
<li>One password, lab keyboard; impostors did not practise the victim's rhythm.</li>
<li>Drift partly = learning a new password.</li>
<li>Small Siamese MLP, ≈43 training subjects, no session-aware training.</li>
<li>Demo: browser timing, few trials, template stored unprotected.</li></ul></div>
<div style="flex:1.1"><h3 style="color:#12306b;margin:0">Conclusions</h3><ul>
<li>Reference reproduced (scaled Manhattan 9.6%).</li>
<li>Cross-session: best single detectors ≈ 14–15% EER, statistically tied.</li>
<li>Learned embedding: best within session, largest cross-session loss.</li>
<li>Error grows with time; enrolment thresholds transfer poorly.</li>
<li>Most effective: multi-session enrolment and multi-entry fusion (≈ 7% at k = 5).</li></ul>
<div class="take">Keystroke rhythm is a cheap, useful <b>second factor</b>, not a stand-alone authenticator.</div></div></div>
{FOOT(13)}</div>

<div class="s" style="display:flex;flex-direction:column;justify-content:center">
<h1 style="font-size:32pt">Thank you · Questions?</h1>
<p class="note" style="font-size:12.5pt;max-width:270mm"><b>Code:</b> <code>python reproduce.py</code> (all numbers, ~1 min) · <code>python demo/app.py</code> (demo) · <code>python tests/test_demo.py</code><br>
<b>Reference:</b> K. S. Killourhy, R. A. Maxion, “Comparing Anomaly-Detection Algorithms for Keystroke Dynamics,” DSN 2009. Further references in the report.<br>
<b>AI use:</b> Claude Code (Anthropic) for coding assistance, debugging, layout of report/slides and language editing; checked by reproducing [Killourhy &amp; Maxion], unit/end-to-end tests, re-running all scripts and verifying every reference ourselves.</p>
{FOOT(14)}</div>
</body></html>"""

out_html = os.path.join(HERE, "final_slides.html")
open(out_html, "w").write(HTML)
pdf = os.path.join(HERE, "..", "Final_Slides_221101034_221101059.pdf")
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", "file://" + out_html], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(os.path.abspath(pdf))
