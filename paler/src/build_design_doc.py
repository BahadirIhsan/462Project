import base64, json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "..", "..", "proje", "results", "results.json")))
S = R["summary"]
sp = R["svm_params"]
def e(n, c="C3_eval41"): return f"{S[n][c]['eer_mean']*100:.1f}"
def b64(path): return base64.b64encode(open(path, "rb").read()).decode()
fig = b64(os.path.join(HERE, "split_fig.png"))

CSS = """
@page { size: A4; margin: 13mm 15mm 13mm 15mm; }
body { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 10pt; line-height: 1.4; color: #111; }
h1 { font-size: 16pt; margin: 0 0 1px; } .au { font-size: 8.6pt; color: #333; margin-bottom: 5px; }
h2 { font-size: 11.2pt; margin: 10px 0 3px; color: #12306b; border-bottom: 1px solid #1f5fbf; padding-bottom: 1px; }
p { margin: 2px 0 3px; text-align: justify; } ul { margin: 2px 0 3px 14px; padding: 0; } li { margin: 1px 0; }
table { border-collapse: collapse; width: 100%; margin: 3px 0 5px; font-size: 8.9pt; }
th { background: #eaf0fb; border: 1px solid #c9d5ee; padding: 2px 4px; text-align: left; } td { border: 1px solid #dde4f2; padding: 2px 4px; vertical-align: top; }
.flow { display: flex; align-items: stretch; gap: 3px; margin: 4px 0 4px; }
.flow div { flex: 1; border: 1.2px solid #1f5fbf; border-radius: 4px; padding: 3px 4px; text-align: center; font-size: 8.4pt; background: #f3f7ff; }
.flow b { display: block; color: #12306b; } .flow i.ar { flex: 0 0 auto; align-self: center; font-style: normal; color: #1f5fbf; font-weight: bold; }
img { display: block; margin: 2px auto; } code { font-size: 8pt; background: #eef1f6; padding: 0 2px; }
.refs { page-break-before: always; font-size: 8.3pt; } .refs h3 { font-size: 9pt; margin: 7px 0 1px; color: #12306b; } .refs a { color: #1f5fbf; text-decoration: none; white-space: nowrap; } .refs p { text-align: left; margin: 2px 0; padding-left: 16px; text-indent: -16px; }
.cap { font-size: 7.6pt; color: #444; text-align: center; margin-top: -1px; }
"""

HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Design Document – Keystroke Dynamics (A5)</title><style>{CSS}</style></head><body>
<h1>Password-Typing Verification Across Sessions: Distance-Based Detectors vs. a One-Class SVM on the CMU Keystroke Benchmark</h1>
<div class="au">BİL462 Biometric Recognition · Project Phase 2 – Literature Review, System Design &amp; Data Plan (topic A5) · Team: Bahadır İhsan Herdem (221101034), Ömer Efe Öztürk (221101059) · October 2026</div>

<h2>1. Problem statement and literature summary</h2>
<p><b>Problem.</b> A password can be stolen, but the way it is typed (key hold times and inter-key latencies) is harder to copy. We study <i>static</i> password-based keystroke verification: all subjects type the same fixed password, and a per-user detector decides whether a new entry was typed by the genuine user. Typing rhythm drifts from day to day, so results measured inside one session can be optimistic. Our question (topic A5): <i>how well do simple and learned detectors separate users who type the same password, and how much does performance degrade across sessions?</i> The biometric trait is keystroke dynamics (behavioural); the only dataset is the public CMU benchmark [1].</p>
<p><b>Literature.</b> Keystroke timing as an identity signal goes back to Joyce &amp; Gupta [2], who built a signature from the gaps between keystrokes (a Manhattan-type detector in the catalogue of [1]), and Monrose &amp; Rubin [3], who studied it for authentication. Because published studies differed in data, password, training size and threshold rule, they could not be compared; Killourhy &amp; Maxion [1] therefore released a benchmark (51 subjects × 8 sessions × 50 repetitions) and evaluated 14 anomaly detectors under one protocol. Their best detectors (scaled Manhattan, nearest-neighbour Mahalanobis, outlier count, one-class SVM) reach 9.6–10.2% mean EER, far from the error levels expected of access control, and detectors that scale features by their variability do best. A follow-up [6] examines which factors (algorithm, training amount, feature choice, updating, impostor practice, typist variability) drive error rates, which motivates our attention to evaluation conditions. One-class SVMs [5] were applied to keystroke novelty detection by Yu &amp; Cho [4]. Recent work shifts toward learned embeddings: Siamese/triplet recurrent and Transformer models for free-text typing (TypeNet [8], TypeFormer [9]) and boosted/MLP/LSTM classifiers for fixed text [10, 11]; surveys are given in [7]. Two points matter for us. (i) A recent fixed-text paper [11] reports 94.75% accuracy and 1.0% EER on this dataset using 5- and 10-fold cross-validation, i.e. not a session-ordered split, so such numbers are not comparable to a verification protocol with temporal separation. (ii) Template ageing is now studied explicitly: a 2026 subject-disjoint study over eight weekly sessions finds that error rises with the enrolment-to-query gap for every matcher, including a scaled-Manhattan matcher, and that matcher choice affects accuracy more than ageing rate [12]; cross-device drift is addressed in [13]. These studies use other datasets, so the CMU benchmark with its fixed 8 sessions remains a clean place to measure drift for the simple-versus-learned comparison that topic A5 asks for.</p>
<p><b>Reference result.</b> Killourhy &amp; Maxion [1], Table 2, mean equal-error rate over subjects (training: first 200 repetitions; test: remaining 200 genuine repetitions vs. the first 5 repetitions of each of 50 impostors): scaled Manhattan <b>0.096</b>, Mahalanobis <b>0.110</b>, Manhattan <b>0.153</b>, one-class SVM <b>0.102</b>. We compare against these four values. <i>Preliminary check:</i> our own implementation of this protocol (41 evaluation subjects) gives {e('Scaled Manhattan')}%, {e('Mahalanobis')}%, {e('Manhattan')}%, and {e('One-class SVM')}% respectively; on all 51 subjects the three distance detectors give 9.6%, 11.1%, 15.3%, matching [1].</p>

<h2>2. System design</h2>
<div class="flow">
<div><b>CMU CSV</b>20,400 entries, 31 timing features</div><i class="ar">→</i>
<div><b>Preprocessing</b>subject/session/rep indexing; no rejection so far</div><i class="ar">→</i>
<div><b>Per-user detector</b>trained on that user's enrolment entries only</div><i class="ar">→</i>
<div><b>Anomaly score</b>higher = less like the user (optional: mean of k consecutive scores)</div><i class="ar">→</i>
<div><b>Evaluation</b>DET, EER, per-user EER, bootstrap CI</div><i class="ar">→</i>
<div><b>Comparison</b>vs. [1], error analysis</div>
</div>
<p><b>Features.</b> The 31 values per entry for the password <code>.tie5Roanl</code>+Enter: 11 hold times (H), 10 down-down (DD) and 10 up-down (UD) latencies. <b>Detectors</b> (all written by us in numpy except the SVM kernel solver): <i>Manhattan</i> (L1 distance to the training mean), <i>scaled Manhattan</i> (each feature divided by its mean absolute deviation), <i>Mahalanobis</i> (inverse covariance, small ridge term because of few samples), and the <b>learned model: a one-class SVM</b> (RBF kernel, z-scored features, trained on the user's genuine entries only). Hyper-parameters of the SVM (ν, γ) are chosen on a separate tuning group of subjects (Section 3); the current choice is ν={sp['nu']}, γ={sp['gamma']}. The distance detectors have no tuned parameters. <b>Optional extensions:</b> (a) fusing the scores of k consecutive entries (already implemented, k∈{{1,3,5,10}}); (b) time permitting, a shared Siamese embedding network trained on subjects disjoint from the evaluated ones (cross-fitting over five subject groups), following the embedding approach of [8, 9]. A localhost login demo (enrolment sessions, then verification) reuses the same code; its data (team members only; instructor approval is requested before any collection) are <u>never</u> used in the evaluation.</p>

<h2>3. Data, licence and splitting rule</h2>
<p><b>Dataset.</b> CMU Keystroke Dynamics Benchmark [1], <code>cs.cmu.edu/~keystroke</code>, file <code>DSL-StrongPasswordData.csv</code>: 51 subjects, 8 sessions (≥1 day apart), 50 repetitions each, 31 features. <b>Licence/terms:</b> the page names no formal licence; it states that the data and evaluation procedure are "freely available for use" as "a shared resource for public use", asks as a courtesy to be informed of publications based on the data, and asks users of a different methodology to make clear that it differs from the original paper. We will follow all three (our protocols C1/C2 and the drift study differ from [1] and are labelled as such; C3 replicates [1]). The data are not redistributed in our code archive; the README gives the download address. No other dataset and no own biometric data are used for the evaluation.</p>
<p><b>Splitting rule (topic A5).</b> Every user has an individual model, so no person-disjoint split is needed for the distance detectors and the one-class SVM; instead data are split <b>by time</b>: training on earlier samples, testing on later ones, other subjects as impostors. Enrolment and test samples are always different. To tune the SVM without touching test people, the 51 subjects are split once (fixed seed) into a <b>tuning group of 10</b> subjects (ν, γ chosen on their sessions 1–3 for training and session 4 for validation) and an <b>evaluation group of 41</b> subjects; all reported results use only the 41. No impostor data are used in training, so impostor identities are never reused. A shared model (the optional embedding network) would be trained only on subjects not evaluated by it.</p>
<img src="data:image/png;base64,{fig}" style="width:72%"><div class="cap">Figure 1. Training/test split per condition (S1–S8 = sessions).</div>
{{TABLE_COND}}

<h2>4. Number of comparisons, metrics and thresholds</h2>
<p><b>Comparisons</b> (41 evaluation subjects; each subject's detector scores the other 40 as impostors): C2 and C1 each give 41×200 = 8,200 genuine and 41×8,000 = 328,000 impostor comparisons; the drift study gives 25 genuine and 1,000 impostor comparisons per subject and test session; the replication C3 on all 51 subjects gives 10,200 genuine and 12,750 impostor comparisons. SVM tuning uses 10 subjects × 50 genuine and 9 × 50 impostor validation entries each. With 8,000 impostor scores per subject, FMR can be resolved down to about 0.1% (8 events), so we report no operating point below FMR = 0.1%; DET axes start at 0.1%.</p>
<p><b>Metrics.</b> DET curve (main curve) and EER for each condition (within-session vs. cross-session; headline result = their difference), per-user EER distribution (mean hides consistent vs. erratic typists), and FNMR at FMR = 1% and 0.1%. <b>Thresholds:</b> the EER is the standard threshold-free benchmark summary used in [1], computed per user on the test scores of that condition; it is not an operating point. For an operational point we additionally choose the threshold using <i>training sessions only</i> (leave-one-session-out genuine scores) and report the resulting FNMR/FMR on the test sessions. <b>Uncertainty:</b> 95% bootstrap confidence intervals obtained by resampling <i>subjects</i> (2,000 resamples), since entries of one subject are not independent (cf. subset resampling in [14]); differences between conditions use paired subject resampling. <b>Error analysis:</b> worst subjects/features, and the effect of training size, which is confounded in C1 vs. C2 (25 vs. 200 training entries) and is therefore separated by the drift experiment.</p>

<h2>5. Tools, pretrained models and responsibility</h2>
<p>No pretrained models are used. Python 3.14; numpy, scipy, pandas, matplotlib; scikit-learn [15] (<code>OneClassSVM</code> only for the SVM solver); Flask for the demo; PyTorch only if the optional embedding network is built. The three distance detectors, feature handling, evaluation conditions, metrics, bootstrap and figures are our own code; one script (<code>run_all.py</code>) reproduces every number. <b>Risks:</b> keystroke dynamics is a weak stand-alone factor ([1]); drift may partly reflect typing practice; browser timing differs from the benchmark's clock, so demo accuracy is not evidence; 41 subjects limit statistical power.</p>

<h2>AI Use Declaration</h2>
<p><b>Tools:</b> Claude Code (Anthropic; model Claude Sonnet 5.5) and web search through it. <b>Used for:</b> writing and debugging the Python code (detectors, metrics, experiment scripts, figures), searching and summarising literature, drafting and editing this document. <b>How checked:</b> the implementation was validated by reproducing the published results of [1] (Manhattan 15.3%, scaled Manhattan 9.6%, Mahalanobis 11.1% vs. 15.3%, 9.6%, 11.0% reported); every reference was looked up online and its authors, title, venue and year were checked against the source page, and the team re-opened each link before submission; all design decisions (split rule, metrics, thresholds) were compared with the project description and topic A5 text. We can explain every part of the code and results.</p>

<div class="refs"><h2>References</h2>
<h3>Reference result and dataset (our results are compared against this study)</h3>
<p>[1] K. S. Killourhy and R. A. Maxion, “Comparing Anomaly-Detection Algorithms for Keystroke Dynamics,” in <i>Proc. IEEE/IFIP Int. Conf. Dependable Systems and Networks (DSN)</i>, 2009, pp. 125–134. Dataset and evaluation script: <a href="https://www.cs.cmu.edu/~keystroke/">https://www.cs.cmu.edu/~keystroke/</a></p>
<h3>Foundational work: keystroke timing, detectors and the one-class SVM (reviewed)</h3>
<p>[2] R. Joyce and G. Gupta, “Identity authentication based on keystroke latencies,” <i>Commun. ACM</i>, vol. 33, no. 2, pp. 168–176, 1990. <a href="https://doi.org/10.1145/75577.75582">https://doi.org/10.1145/75577.75582</a></p>
<p>[3] F. Monrose and A. D. Rubin, “Keystroke dynamics as a biometric for authentication,” <i>Future Generation Computer Systems</i>, vol. 16, pp. 351–359, 2000. <a href="https://www.passwordresearch.com/papers/paper60.html">https://www.passwordresearch.com/papers/paper60.html</a></p>
<p>[4] E. Yu and S. Cho, “Novelty detection approach for keystroke dynamics identity verification,” in <i>Intelligent Data Engineering and Automated Learning (IDEAL)</i>, 2003. <a href="https://dblp.org/rec/conf/ideal/YuC03.html">https://dblp.org/rec/conf/ideal/YuC03.html</a></p>
<p>[5] B. Schölkopf, J. C. Platt, J. Shawe-Taylor, A. J. Smola and R. C. Williamson, “Estimating the support of a high-dimensional distribution,” <i>Neural Computation</i>, vol. 13, no. 7, pp. 1443–1471, 2001. <a href="https://doi.org/10.1162/089976601750264965">https://doi.org/10.1162/089976601750264965</a></p>
<p>[6] K. Killourhy and R. Maxion, “Why did my detector do that?! Predicting keystroke-dynamics error rates,” in <i>Recent Advances in Intrusion Detection (RAID)</i>, LNCS 6307, 2010, pp. 256–276. <a href="https://www.cs.cmu.edu/~maxion/pubs/KillourhyMaxion10.pdf">https://www.cs.cmu.edu/~maxion/pubs/KillourhyMaxion10.pdf</a></p>
<h3>Survey and recent work (reviewed, 2021–2026)</h3>
<p>[7] R. Shadman, A. A. Wahab, M. Manno, M. Lukaszewski, D. Hou and F. Hussain, “Keystroke Dynamics: Concepts, Techniques, and Applications,” arXiv:2303.04605 (v3, 2025; accepted to ACM Computing Surveys). <a href="https://arxiv.org/abs/2303.04605">https://arxiv.org/abs/2303.04605</a></p>
<p>[8] A. Acien, A. Morales, J. V. Monaco, R. Vera-Rodriguez and J. Fierrez, “TypeNet: Deep Learning Keystroke Biometrics,” arXiv:2101.05570, 2021. <a href="https://arxiv.org/abs/2101.05570">https://arxiv.org/abs/2101.05570</a></p>
<p>[9] G. Stragapede, P. Delgado-Santos, R. Tolosana, R. Vera-Rodriguez, R. Guest and A. Morales, “TypeFormer: Transformers for Mobile Keystroke Biometrics,” arXiv:2212.13075, 2022 (rev. 2023). <a href="https://arxiv.org/abs/2212.13075">https://arxiv.org/abs/2212.13075</a></p>
<p>[10] H.-C. Chang, J. Li, C.-S. Wu and M. Stamp, “Machine Learning and Deep Learning for Fixed-Text Keystroke Dynamics,” arXiv:2107.00507, 2021. <a href="https://arxiv.org/abs/2107.00507">https://arxiv.org/abs/2107.00507</a></p>
<p>[11] K. Sasikumar and S. Nagarajan, “LSTM-based ensemble models for keystroke dynamics authentication: integrating explainable AI for transparency,” <i>Frontiers in Artificial Intelligence</i>, vol. 9, 2026. <a href="https://doi.org/10.3389/frai.2026.1860248">https://doi.org/10.3389/frai.2026.1860248</a></p>
<p>[12] S. Parkinson, S. Khan, N. Liu and Q. Xu, “Template Ageing and Longitudinal Verification in Fixed-Text Keystroke Dynamics: A Subject-Disjoint Study Across Eight Weeks,” arXiv:2609.29851, 2026. <a href="https://arxiv.org/abs/2609.29851">https://arxiv.org/abs/2609.29851</a></p>
<p>[13] N. Kaluarachchi, S. Kandanaarachchi, K. Moore, A. Arakala and C. Sanderson, “Transfer Learning of Keystroke Dynamics for Cross-Device User Authentication,” arXiv:2608.16334, 2026. <a href="https://arxiv.org/abs/2608.16334">https://arxiv.org/abs/2608.16334</a></p>
<h3>Evaluation methodology and tools</h3>
<p>[14] R. M. Bolle, N. K. Ratha and S. Pankanti, “Error analysis of pattern recognition systems—the subsets bootstrap,” <i>Computer Vision and Image Understanding</i>, vol. 93, no. 1, pp. 1–33, 2004. <a href="https://doi.org/10.1016/j.cviu.2003.08.002">https://doi.org/10.1016/j.cviu.2003.08.002</a></p>
<p>[15] F. Pedregosa et al., “Scikit-learn: Machine Learning in Python,” <i>J. Machine Learning Research</i>, vol. 12, pp. 2825–2830, 2011. <a href="https://jmlr.org/papers/v12/pedregosa11a.html">https://jmlr.org/papers/v12/pedregosa11a.html</a></p>
</div></body></html>"""

table = """<table><tr><th>Condition</th><th>Training (genuine user)</th><th>Test: genuine</th><th>Test: impostors</th><th>Purpose</th></tr>
<tr><td><b>C1</b> within-session</td><td>reps 1–25 of each session</td><td>reps 26–50, same session</td><td>other 40 subjects, same session, reps 26–50</td><td>optimistic baseline</td></tr>
<tr><td><b>C2</b> cross-session</td><td>sessions 1–4 (200)</td><td>sessions 5–8 (200)</td><td>other 40 subjects, sessions 5–8</td><td>realistic condition</td></tr>
<tr><td><b>Drift</b></td><td>session 1, reps 1–25</td><td>session t=1…8, reps 26–50</td><td>other 40 subjects, same session</td><td>controlled ageing curve (fixed training size)</td></tr>
<tr><td><b>C3</b> replication of [1]</td><td>first 200 reps</td><td>remaining 200</td><td>first 5 reps of each other subject</td><td>compare with reference</td></tr></table>"""
HTML = HTML.replace("{TABLE_COND}", table)
out_html = os.path.join(HERE, "design_doc.html")
open(out_html, "w", encoding="utf-8").write(HTML)
pdf = os.path.join(HERE, "..", "PA2_Design_Document_221101034_221101059.pdf")
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", "file://" + out_html], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(os.path.abspath(pdf))
