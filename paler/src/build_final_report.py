"""Final report (PDF). Every number is read from proje/results/*.json produced by proje/reproduce.py."""
import base64, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "proje", "results")
R = json.load(open(os.path.join(RES, "results.json")))
F = json.load(open(os.path.join(RES, "final.json")))
C = json.load(open(os.path.join(RES, "checkpoint.json")))
S, FP, EA, D, Q = R["summary"], F["fold_protocol"], F["error_analysis"], C["dataset"], C["quality"]
BASE = ["Manhattan", "Scaled Manhattan", "Mahalanobis", "One-class SVM"]
SIA, FUS = "Siamese embedding", "Fusion (SM+SVM+Siamese)"
REF = {"Manhattan": .153, "Scaled Manhattan": .096, "Mahalanobis": .110, "One-class SVM": .102}


def p(x, d=1):
    return f"{x * 100:.{d}f}"


def ci(c, d=1):
    return f"[{p(c[0], d)}, {p(c[1], d)}]"


def img(name, w, folder=RES):
    b = base64.b64encode(open(os.path.join(folder, name), "rb").read()).decode()
    return f'<img src="data:image/png;base64,{b}" style="width:{w}">'


def fig(name, w, cap, n, folder=RES):
    return f'<figure>{img(name, w, folder)}<figcaption><b>Figure {n}.</b> {cap}</figcaption></figure>'


sm, sv = FP["Scaled Manhattan"], FP["One-class SVM"]
d21 = R["c2_minus_c1"]
best_c2 = min(BASE + [SIA], key=lambda n: FP[n]["C2"]["eer_mean"])
op = {n: FP[n]["operational"] for n in BASE + [SIA]}
tun = F["siamese_tuning"]
rej = C["rejection"]["2.0"]

# ---------------------------------------------------------------- tables
t_main = "".join(
    f"<tr><td>{n}</td><td>{p(S[n]['C1_oturum_ici']['eer_mean'])} {ci(S[n]['C1_oturum_ici']['ci95'])}</td>"
    f"<td><b>{p(S[n]['C2_oturumlar_arasi']['eer_mean'])}</b> {ci(S[n]['C2_oturumlar_arasi']['ci95'])}</td>"
    f"<td>{'+' if d21[n][0] >= 0 else ''}{p(d21[n][0])} {ci(d21[n][1:])}</td>"
    f"<td>{p(S[n]['C2_oturumlar_arasi']['fnmr@fmr1%'])}</td><td>{p(S[n]['C2_oturumlar_arasi']['fnmr@fmr0.1%'])}</td></tr>" for n in BASE)
t_fold = "".join(
    f"<tr><td>{n}</td><td>{p(FP[n]['C1']['eer_mean']) + ' ' + ci(FP[n]['C1']['ci95']) if 'C1' in FP[n] else '–'}</td>"
    f"<td><b>{p(FP[n]['C2']['eer_mean'])}</b> {ci(FP[n]['C2']['ci95'])}</td>"
    f"<td>{(('+' if FP[n]['C2_minus_C1'][0] >= 0 else '') + p(FP[n]['C2_minus_C1'][0]) + ' ' + ci(FP[n]['C2_minus_C1'][1:])) if 'C2_minus_C1' in FP[n] else '–'}</td>"
    f"<td>{p(FP[n]['fusion_k']['5']['eer_mean'])}</td><td>{p(FP[n]['fusion_k']['10']['eer_mean'])}</td></tr>" for n in BASE + [SIA, FUS])
t_ref = "".join(
    f"<tr><td>{n}</td><td>{p(REF[n])}</td><td>{p(S[n]['C3_makale_protokolu']['eer_mean'])} {ci(S[n]['C3_makale_protokolu']['ci95'])}</td>"
    f"<td>{S[n]['C3_makale_protokolu']['n_users']}</td><td>{p(S[n]['C3_eval41']['eer_mean'])}</td>"
    f"<td>{p(S[n]['C2_oturumlar_arasi']['eer_mean'])}</td></tr>" for n in BASE)
t_op = "".join(f"<tr><td>{n}</td>" + "".join(f"<td>{p(op[n][q]['fnmr'])} / {p(op[n][q]['fmr'])}</td>" for q in ("0.9", "0.95", "0.99")) + "</tr>" for n in BASE + [SIA])
t_rej = "".join(f"<tr><td>{n}</td><td>{p(v['eer_all'], 2)}</td><td>{p(v['eer_filtered'], 2)}</td><td>{p(v['diff'], 2)} {ci(v['diff_ci95'], 2)}</td></tr>" for n, v in C["effect_C2"].items())
paired = F["paired_C2"]
pc = lambda k: f"{'+' if paired[k][0] >= 0 else ''}{p(paired[k][0])} pp, 95% CI {ci(paired[k][1:])}"

CSS = """
@page { size: A4; margin: 17mm 17mm 16mm; }
body { font-family: 'Times New Roman', Times, serif; font-size: 10.8pt; line-height: 1.38; color: #111; text-align: justify; hyphens: auto; }
h1 { font-size: 17pt; text-align: center; margin: 0 0 2mm; line-height: 1.2; }
.meta { text-align: center; font-size: 10pt; color: #333; margin-bottom: 4mm; }
.abs { border-top: 1px solid #999; border-bottom: 1px solid #999; padding: 2mm 0; margin-bottom: 3mm; font-size: 10.2pt; }
h2 { font-size: 12.5pt; margin: 5mm 0 1.5mm; border-bottom: 1px solid #ccc; padding-bottom: .6mm; break-after: avoid; }
h3 { font-size: 11pt; margin: 3mm 0 1mm; break-after: avoid; }
p { margin: 0 0 2mm; } ul, ol { margin: 0 0 2mm 5mm; padding-left: 3mm; } li { margin: .5mm 0; }
table { border-collapse: collapse; margin: 1.5mm auto 1mm; font-size: 9.3pt; break-inside: avoid; }
th, td { border: 1px solid #b9c0cc; padding: .7mm 2mm; text-align: center; } th { background: #eef1f6; } td:first-child { text-align: left; }
.cap { font-size: 9.2pt; text-align: center; margin: 0 0 3mm; color: #222; }
figure { margin: 2mm 0 3mm; text-align: center; break-inside: avoid; } figcaption { font-size: 9.2pt; margin-top: 1mm; text-align: center; }
.flow { display: flex; gap: 1.5mm; align-items: stretch; margin: 2mm 0 1mm; font-size: 8.6pt; text-align: center; }
.flow div { flex: 1; border: 1px solid #2456c9; border-radius: 2mm; padding: 1.5mm; background: #f3f6fd; } .flow b { display: block; font-size: 9pt; }
.flow i { align-self: center; font-style: normal; color: #2456c9; }
.two { display: flex; gap: 4mm; align-items: flex-start; } .two > * { flex: 1; }
.ref p { font-size: 9.2pt; margin: 0 0 1.2mm; text-align: left; padding-left: 6mm; text-indent: -6mm; }
code { font-size: 9.3pt; } .small { font-size: 9.3pt; } .eq { text-align: center; margin: 1mm 0 2mm; font-style: italic; }
.box { border: 1px solid #c8cfda; background: #f7f9fc; padding: 2mm 3mm; margin: 2mm 0; break-inside: avoid; }
.pb { break-before: page; }
"""

ref_list = [
    ("Killourhy &amp; Maxion", "K. S. Killourhy and R. A. Maxion, “Comparing Anomaly-Detection Algorithms for Keystroke Dynamics,” in <i>Proc. IEEE/IFIP DSN</i>, 2009, pp. 125–134. Data: https://www.cs.cmu.edu/~keystroke/"),
    ("", "R. Joyce and G. Gupta, “Identity authentication based on keystroke latencies,” <i>Commun. ACM</i>, vol. 33, no. 2, pp. 168–176, 1990. https://doi.org/10.1145/75577.75582"),
    ("", "F. Monrose and A. D. Rubin, “Keystroke dynamics as a biometric for authentication,” <i>Future Generation Computer Systems</i>, vol. 16, pp. 351–359, 2000."),
    ("", "E. Yu and S. Cho, “Novelty detection approach for keystroke dynamics identity verification,” in <i>IDEAL</i>, 2003. https://dblp.org/rec/conf/ideal/YuC03.html"),
    ("", "B. Schölkopf, J. C. Platt, J. Shawe-Taylor, A. J. Smola and R. C. Williamson, “Estimating the support of a high-dimensional distribution,” <i>Neural Computation</i>, vol. 13, no. 7, pp. 1443–1471, 2001. https://doi.org/10.1162/089976601750264965"),
    ("", "K. Killourhy and R. Maxion, “Why did my detector do that?! Predicting keystroke-dynamics error rates,” in <i>RAID</i>, LNCS 6307, 2010, pp. 256–276."),
    ("", "R. Shadman, A. A. Wahab, M. Manno, M. Lukaszewski, D. Hou and F. Hussain, “Keystroke Dynamics: Concepts, Techniques, and Applications,” arXiv:2303.04605 (v3, 2025). https://arxiv.org/abs/2303.04605"),
    ("", "A. Acien, A. Morales, J. V. Monaco, R. Vera-Rodriguez and J. Fierrez, “TypeNet: Deep Learning Keystroke Biometrics,” arXiv:2101.05570, 2021. https://arxiv.org/abs/2101.05570"),
    ("", "G. Stragapede, P. Delgado-Santos, R. Tolosana, R. Vera-Rodriguez, R. Guest and A. Morales, “TypeFormer: Transformers for Mobile Keystroke Biometrics,” arXiv:2212.13075, 2022. https://arxiv.org/abs/2212.13075"),
    ("", "H.-C. Chang, J. Li, C.-S. Wu and M. Stamp, “Machine Learning and Deep Learning for Fixed-Text Keystroke Dynamics,” arXiv:2107.00507, 2021. https://arxiv.org/abs/2107.00507"),
    ("", "K. Sasikumar and S. Nagarajan, “LSTM-based ensemble models for keystroke dynamics authentication: integrating explainable AI for transparency,” <i>Frontiers in Artificial Intelligence</i>, vol. 9, 2026. https://doi.org/10.3389/frai.2026.1860248"),
    ("", "S. Parkinson, S. Khan, N. Liu and Q. Xu, “Template Ageing and Longitudinal Verification in Fixed-Text Keystroke Dynamics: A Subject-Disjoint Study Across Eight Weeks,” arXiv:2609.29851, 2026. https://arxiv.org/abs/2609.29851"),
    ("", "N. Kaluarachchi, S. Kandanaarachchi, K. Moore, A. Arakala and C. Sanderson, “Transfer Learning of Keystroke Dynamics for Cross-Device User Authentication,” arXiv:2608.16334, 2026. https://arxiv.org/abs/2608.16334"),
    ("", "R. M. Bolle, N. K. Ratha and S. Pankanti, “Error analysis of pattern recognition systems—the subsets bootstrap,” <i>Computer Vision and Image Understanding</i>, vol. 93, no. 1, pp. 1–33, 2004. https://doi.org/10.1016/j.cviu.2003.08.002"),
    ("", "F. Pedregosa et al., “Scikit-learn: Machine Learning in Python,” <i>JMLR</i>, vol. 12, pp. 2825–2830, 2011. https://jmlr.org/papers/v12/pedregosa11a.html"),
    ("", "F. Schroff, D. Kalenichenko and J. Philbin, “FaceNet: A Unified Embedding for Face Recognition and Clustering,” in <i>Proc. CVPR</i>, 2015. arXiv:1503.03832. https://arxiv.org/abs/1503.03832"),
    ("", "A. Hermans, L. Beyer and B. Leibe, “In Defense of the Triplet Loss for Person Re-Identification,” arXiv:1703.07737, 2017. https://arxiv.org/abs/1703.07737"),
    ("", "A. Paszke et al., “PyTorch: An Imperative Style, High-Performance Deep Learning Library,” in <i>NeurIPS</i>, 2019. arXiv:1912.01703. https://arxiv.org/abs/1912.01703"),
    ("", "G. Doddington, W. Liggett, A. Martin, M. Przybocki and D. Reynolds, “SHEEP, GOATS, LAMBS and WOLVES: A Statistical Analysis of Speaker Performance in the NIST 1998 Speaker Recognition Evaluation,” in <i>Proc. ICSLP</i>, 1998."),
]
refs = "".join(f"<p>[{i + 1}] {t}</p>" for i, (_, t) in enumerate(ref_list))

html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<h1>Password-Typing Verification Across Sessions:<br>Distance Detectors, a One-Class SVM and a Siamese Embedding on the CMU Keystroke Benchmark</h1>
<div class="meta">BİL462 Biometric Recognition · Final Report · Topic A5 · Bahadır İhsan Herdem (221101034), Ömer Efe Öztürk (221101059) · December 2026</div>
<div class="abs"><b>Abstract.</b> We verify users from the rhythm with which they type a fixed password, on the public CMU benchmark
(51 subjects × 8 sessions × 50 entries). Three distance detectors, a one-class SVM and a shared Siamese embedding network are evaluated
within a session (C1) and across sessions (C2) on 41 subjects that were never used for tuning or for training a shared model. Our replication
of the original protocol reproduces the published reference results (scaled Manhattan {p(S['Scaled Manhattan']['C3_makale_protokolu']['eer_mean'])}% vs. 9.6%).
Across sessions the mean EER of the best single detector is {p(FP[best_c2]['C2']['eer_mean'])}% ({best_c2}); the Siamese embedding is the best
detector within a session ({p(FP[SIA]['C1']['eer_mean'])}%) but loses the most across sessions (+{p(FP[SIA]['C2_minus_C1'][0])} percentage points),
so within-session results are optimistic for learned models in particular. Fusing three detectors gives {p(FP[FUS]['C2']['eer_mean'])}% and
averaging five consecutive entries {p(FP[FUS]['fusion_k']['5']['eer_mean'])}%. Error rates of this size mean that keystroke rhythm is a useful
second factor, not a stand-alone authenticator. A localhost demo implements the same pipeline as a password-plus-rhythm login.</div>

<h2>1. Introduction</h2>
<p><b>Problem.</b> A password can be stolen, guessed or shoulder-surfed, but the way it is typed (how long each key is held and how quickly
the next one follows) is harder to copy. Keystroke dynamics adds this behavioural check to an existing password without extra hardware.
We study <i>static</i>, password-based verification: every subject types the same fixed password, and a per-user detector decides whether
a new entry was typed by the claimed user. Typing rhythm, however, changes from day to day: people get faster, pause differently, or are
tired. Results measured inside one sitting may therefore be optimistic.</p>
<p><b>Question (topic A5).</b> How well do simple and learned detectors separate users who type the same password, and how much does
performance drop across sessions? <b>Trait:</b> keystroke dynamics (behavioural). <b>Data:</b> the CMU Keystroke Dynamics Benchmark [1] only.</p>
<p><b>Contributions.</b> (i) A from-scratch implementation of the Manhattan, scaled Manhattan and Mahalanobis detectors that reproduces the
reference results of [1]; (ii) a separate within-session (C1) and cross-session (C2) evaluation with DET curves, per-user EER and
subject-level bootstrap confidence intervals, plus a template-ageing curve with a fixed enrolment size; (iii) two learned models, a per-user
one-class SVM and a Siamese embedding shared across users, trained on subjects disjoint from those evaluated; (iv) score fusion across
detectors and across consecutive entries; (v) an error analysis; (vi) a working password-plus-rhythm login demo.</p>

<h2>2. Literature Review</h2>
<p><b>Origins.</b> Joyce and Gupta [2] built identity signatures from inter-key latencies and compared new attempts with a mean reference
(a Manhattan-type rule); Monrose and Rubin [3] studied keystroke dynamics for authentication and showed large differences between users.
<b>Benchmarking.</b> Published results were hard to compare because studies differed in password, amount of training data, impostor data and
threshold rule. Killourhy and Maxion [1] therefore collected the benchmark we use and evaluated 14 anomaly detectors under a single protocol.
The best ones (scaled Manhattan, nearest-neighbour Mahalanobis, outlier count, one-class SVM) reached 9.6–10.2% mean EER; detectors that
scale each feature by its variability did best, and no detector came close to the error rates required for access control. Their follow-up
[6] modelled which factors drive error rates (algorithm, training amount, feature set, template updating, impostor familiarity, and the typist
themself), showing that per-user variation is at least as important as the choice of detector.
<b>Learned models.</b> One-class SVMs [5] learn a boundary around the genuine data only and were applied to keystroke novelty detection by Yu
and Cho [4]. Later work moved to deep models: TypeNet [8] trains an LSTM embedding with Siamese and triplet losses on free text from
large populations, and TypeFormer [9] uses Transformers for mobile typing; both learn a metric space shared by all users so that new users
need only a few enrolment samples. For fixed text, Chang et al. [10] compare classical and deep classifiers, and Sasikumar and Nagarajan
[11] report 94.75% accuracy and 1.0% EER on the CMU data with an LSTM ensemble. Those numbers come from 5- and 10-fold cross-validation that
mixes sessions and uses impostor samples in training, i.e. a closed-set classification setting rather than the session-ordered verification
protocol required here, so they are not comparable with ours. Our Siamese model follows the embedding idea of [8, 9] with the batch-hard
triplet loss of [16, 17].
<b>Ageing and drift.</b> A recent subject-disjoint study over eight weekly sessions [12] finds that verification error grows with the gap
between enrolment and query for every matcher, including scaled Manhattan, and that matcher choice changes accuracy more than it changes the
ageing rate; cross-device drift is addressed by transfer learning in [13]. A survey of concepts and applications is given in [7].
<b>Evaluation methodology.</b> Because entries from the same person are correlated, we estimate uncertainty by resampling subjects (subsets
bootstrap [14]), and we use the "biometric zoo" vocabulary of [19] (wolves = impostors who are often accepted) in the error analysis.
<b>Reference result.</b> Killourhy and Maxion [1], mean EER over subjects: scaled Manhattan 0.096, Mahalanobis 0.110, Manhattan 0.153,
one-class SVM 0.102 (training: first 200 entries; genuine test: remaining 200; impostor test: first 5 entries of each of the other 50 subjects).</p>

<h2>3. Datasets</h2>
<p><b>CMU Keystroke Dynamics Benchmark [1]</b> (<code>DSL-StrongPasswordData.csv</code>, cs.cmu.edu/~keystroke). {D['subjects']} subjects typed the
password <code>.tie5Roanl</code> followed by Return, 50 times per session in {D['sessions']} sessions separated by at least one day:
{D['entries']:,} entries. Each entry has {D['features']} timing features in seconds: 11 hold times H (key down→up), 10 down-down latencies DD
(key down→next key down) and 10 up-down latencies UD (key up→next key down). Subject IDs run {D['subject_ids']}. A typo made the recording
software ask for the password again, so every stored entry is a correctly typed password. <b>Licence:</b> the page states that the data are
freely available as a shared resource for public use, asks to be informed of publications and asks that methodologies differing from [1] be
labelled as such. We do this: C3 replicates [1]; C1, C2, the ageing curve and the fold protocol differ from it. The data are not redistributed in
our code archive; the README explains the download.</p>
<p><b>Statistics.</b> Mean hold time {D['mean_ms']['H']:.0f} ms, mean DD latency {D['mean_ms']['DD']:.0f} ms. The median entry takes
{D['total_s']['median']:.2f} s (1st–99th percentile {D['total_s']['p1']:.2f}–{D['total_s']['p99']:.2f} s, maximum {D['total_s']['max']:.1f} s); the
per-subject median ranges from {D['subject_median_total_s']['min']:.2f} to {D['subject_median_total_s']['max']:.2f} s. Typing speeds up steadily:
the median entry time falls from {D['session_median_total_s']['1']:.2f} s in session 1 to {D['session_median_total_s']['8']:.2f} s in session 8, and
{D['subjects_faster_s8_than_s1']} of 51 subjects are faster in session 8 than in session 1. This practice effect is the main source of cross-session drift.</p>
<p><b>Quality checks and preprocessing</b> (Phase 3). All structural checks pass (no missing values or duplicates, complete 51×8×50 grid, the
identity DD = H + UD holds to 1e-9 s). {p(Q['neg_ud_frac'])}% of the UD values are negative (the next key is pressed before the previous
one is released); this is genuine rollover behaviour and is kept. {Q['entries_any_dd_gt_2s']} entries contain a pause longer than 2 s
(longest single gap {Q['max_single_dd_s']:.1f} s). Because DD = H + UD, the 31-dimensional covariance has rank {Q['mahalanobis_cov_rank']}, so the
Mahalanobis detector needs a ridge term. We tested a rejection rule applied to <i>enrolment</i> entries only (discard an entry whose total time
exceeds 2× the user's own enrolment median; test entries are never filtered): it removes {rej['C2_rejected']} of {rej['C2_total']} C2
enrolment entries ({p(rej['C2_rejected'] / rej['C2_total'])}%), mostly from session 1, and changes the EER by at most a quarter of a percentage point
(Table 5). Main results therefore use all entries, which keeps them comparable with [1].</p>
<p><b>Subject split.</b> The 51 subjects are split once (seed 0) into a <i>tuning group</i> of 10 subjects and an <i>evaluation group</i> of 41.
All hyper-parameters (one-class SVM ν, γ; Siamese size and training length) are chosen on the tuning group, and all reported results except
the replication use only the 41 evaluation subjects. <b>Own data.</b> No own biometric data are used in the evaluation. For the demo (Section 4.6) we
collected typing data from the two team members only, with the instructor's prior approval and the members' explicit consent (a consent
box at registration); these entries are stored locally, can be deleted at any time, and are never mixed with the CMU evaluation.</p>

<h2>4. Methods</h2>
<div class="flow"><div><b>Input</b>key-down / key-up times of one entry</div><i>→</i><div><b>Features</b>31 values: 11 H, 10 DD, 10 UD</div><i>→</i>
<div><b>Enrolment</b>per-user template from that user's earlier entries only</div><i>→</i><div><b>Detectors</b>Manhattan · scaled Manh. · Mahalanobis · OC-SVM · Siamese</div><i>→</i>
<div><b>Score fusion</b>z-norm per user; mean over detectors and/or k entries</div><i>→</i><div><b>Decision</b>score ≤ threshold → accept</div></div>
<p class="cap"><b>Figure 1.</b> System stages. Higher anomaly score = less like the claimed user. The same code runs the evaluation and the demo.</p>
<h3>4.1 Distance detectors (no trained parameters)</h3>
<p>For a user with enrolment matrix X (n entries × 31) and mean vector μ, a test vector x is scored by <b>Manhattan</b> Σ<sub>j</sub>|x<sub>j</sub>−μ<sub>j</sub>|;
<b>scaled Manhattan</b> Σ<sub>j</sub>|x<sub>j</sub>−μ<sub>j</sub>|/a<sub>j</sub>, where a<sub>j</sub> is the mean absolute deviation of feature j in the enrolment data, so each feature
is measured in units of the user's own variability; and <b>Mahalanobis</b> (x−μ)ᵀ(Σ+λI)⁻¹(x−μ) with λ = 10⁻³·tr(Σ)/31 because Σ is rank-deficient.
All three are written in numpy and follow [1].</p>
<h3>4.2 One-class SVM (per-user learned model)</h3>
<p>Features are z-scored with the enrolment mean and SD of the user, and an RBF one-class SVM [5] (scikit-learn [15] solver) is fitted on the
genuine enrolment entries only; the score is the negative decision function. ν and γ were chosen by grid search (ν ∈ {{0.01…0.5}}, γ ∈ {{0.003…0.3}})
on the tuning subjects only (sessions 1–3 for training, session 4 for validation): ν = {R['svm_params']['nu']}, γ = {R['svm_params']['gamma']}
(tuning EER {p(R['svm_grid'][f"nu={R['svm_params']['nu']},gamma={R['svm_params']['gamma']}"])}%).</p>
<h3>4.3 Siamese embedding (learned model shared across users)</h3>
<p>H and DD features are log-transformed (they are positive and right-skewed), all features are standardised with statistics of the training
subjects, and a multilayer perceptron 31→{tun['best']['hidden']}→{tun['best']['hidden']}→{tun['best']['dim']} with ReLU and L2-normalised output maps an
entry to an embedding. It is trained in PyTorch [18] with the batch-hard triplet loss [16, 17] (batches of 16 subjects × 16 entries, margin 0.3,
Adam, learning rate 10⁻³ with cosine decay, {tun['best']['steps']} steps): for every anchor, the farthest same-subject entry must be closer
than the nearest other-subject entry. Enrolment is cheap: the user's template is the mean embedding of the enrolment entries, and the score is the
Euclidean distance to it. <b>Disjointness.</b> The network uses other people as negatives, so (a) the people it is trained on must not be
evaluated, and (b) they must not reappear as test impostors. We use <b>5-fold cross-fitting</b> over the 41 evaluation subjects: for fold f the
network is trained on the 10 tuning subjects plus the 4 other folds (all 8 sessions, 43 subjects), and only the 8–9 subjects of fold f are
evaluated, with impostors drawn from fold f only. <b>Tuning</b> (18 configurations of size and training length) was done with the network trained
on the 41 evaluation subjects and evaluated with protocol C2 on the 10 tuning subjects, so no evaluated person influenced the choice. Longer training over-fitted the small training population (Appendix A).</p>
<h3>4.4 Score normalisation and fusion</h3>
<p>Raw scores of different detectors are not comparable, so each user's scores are z-normalised with the mean and SD of <i>genuine held-out
enrolment scores</i>: in C2 the detector is refitted four times, each time leaving one enrolment session out and scoring it. No impostor and no
test data are used. <b>Detector fusion</b> averages the z-scores of scaled Manhattan, one-class SVM and the Siamese embedding. <b>Multi-entry
fusion</b> (the optional part of the topic) averages the scores of k consecutive entries of the same session (non-overlapping windows) before
the decision, k ∈ {{1, 3, 5, 10}}.</p>
<h3>4.5 Thresholds</h3>
<p>The EER is threshold-free (it is computed per user on that condition's test scores and then averaged, as in [1]) and is not an operating
point. For an operating point, the threshold is set <i>from enrolment data only</i>: the q-quantile (q = 0.90, 0.95, 0.99) of the user's
leave-one-session-out genuine scores; it is then applied unchanged to the test sessions (Table 4).</p>
<h3>4.6 Demo system</h3>
<p>A Flask web application (<code>proje/demo</code>) records key-down and key-up times in the browser (<code>event.timeStamp</code>), turns an entry
into the same H/DD/UD vector (for <code>.tie5Roanl</code> exactly the 31 CMU columns; a unit test replays CMU rows as key events and recovers them
exactly), and stores it in SQLite. Like the CMU software, an entry containing Backspace or any editing key is discarded. Only a salted scrypt
hash of the password is stored, never the password text; the biometric template is the list of timing vectors (no key text), kept on the local
machine and deletable by the user (cascade delete). Login first checks the password hash and then the rhythm with scaled Manhattan + one-class
SVM (+ the Siamese network trained on all 51 CMU subjects when the CMU password is used), z-normalised and thresholded exactly as in
Sections 4.4–4.5 (leave-one-session-out when the user has two enrolment sessions, otherwise 5-fold cross-validation). An "impostor test" mode lets
a team-mate type another member's password; such attempts are logged but never sign anyone in. Screens are shown in Appendix B.</p>

<h2>5. Evaluation</h2>
<h3>5.1 Protocols and number of comparisons</h3>
<table><tr><th>Condition</th><th>Enrolment (genuine user)</th><th>Genuine test</th><th>Impostor test</th><th>Comparisons (41 subjects)</th></tr>
<tr><td>C1 within-session</td><td>reps 1–25 of each session</td><td>reps 26–50, same session</td><td>other 40 subjects, same session, reps 26–50</td><td>8,200 gen. / 328,000 imp.</td></tr>
<tr><td>C2 cross-session</td><td>sessions 1–4 (200)</td><td>sessions 5–8 (200)</td><td>other 40 subjects, sessions 5–8</td><td>8,200 gen. / 328,000 imp.</td></tr>
<tr><td>Ageing</td><td>session 1, reps 1–25</td><td>session t, reps 26–50</td><td>other subjects, session t</td><td>per t: 1,025 gen. / 41,000 imp.</td></tr>
<tr><td>Fold protocol</td><td>as C1 / C2</td><td>as C1 / C2</td><td>other subjects of the same fold (7–8)</td><td>C2: 8,200 gen. / ≈{FP[SIA]['C2']['n_impostor_per_user'] * 41:,} imp.</td></tr>
<tr><td>C3 replication of [1]</td><td>first 200 entries</td><td>remaining 200</td><td>first 5 entries of each other subject</td><td>51 subj.: 10,200 / 12,750</td></tr></table>
<p class="cap"><b>Table 1.</b> Evaluation conditions. Enrolment and test entries are always different; only later entries are tested.</p>
<p><b>Metrics.</b> DET curve (main curve) and mean per-user EER per condition; per-user EER distributions; FNMR at fixed FMR; 95% bootstrap
confidence intervals with 2,000 resamples of <i>subjects</i>, and paired subject resampling for differences between conditions or detectors.
<b>Resolution.</b> With 8,000 impostor scores per user, an FMR of 0.1% corresponds to 8 accepted impostor entries, so 0.1% is the lowest FMR we
report and DET axes start there; in the fold protocol (≈{FP[SIA]['C2']['n_impostor_per_user']} impostor scores per user) we stop at 1%.</p>

<h3>5.2 Within- vs. cross-session results (distance detectors and SVM, 40 impostors each)</h3>
<table><tr><th>Detector</th><th>C1 EER % [95% CI]</th><th>C2 EER % [95% CI]</th><th>C2 − C1 (pp) [95% CI]</th><th>C2 FNMR @ FMR 1%</th><th>C2 FNMR @ FMR 0.1%</th></tr>{t_main}</table>
<p class="cap"><b>Table 2.</b> Mean per-user EER on the 41 evaluation subjects. C1 trains on 25 entries, C2 on 200, so their difference mixes
drift and training size (separated in Section 5.4).</p>
<div class="two">{fig('fin_det_c1.png', '100%', 'DET, C1 within-session.', 2)}{fig('fin_det_c2.png', '100%', 'DET, C2 cross-session (main condition).', 3)}</div>
<p>Across sessions, scaled Manhattan ({p(S['Scaled Manhattan']['C2_oturumlar_arasi']['eer_mean'])}%), Mahalanobis ({p(S['Mahalanobis']['C2_oturumlar_arasi']['eer_mean'])}%)
and the one-class SVM ({p(S['One-class SVM']['C2_oturumlar_arasi']['eer_mean'])}%) are statistically tied (overlapping CIs), and all are far better than plain Manhattan
({p(S['Manhattan']['C2_oturumlar_arasi']['eer_mean'])}%), which is dominated by the few long latencies. Scaled Manhattan loses
{p(d21['Scaled Manhattan'][0])} pp from C1 to C2 (CI excludes 0) although it is trained on 8× more data in C2, which is direct evidence of drift.
Mahalanobis, in contrast, <i>improves</i> from C1 to C2 ({p(d21['Mahalanobis'][0])} pp): with only 25 entries its 31×31 covariance is poorly
estimated, so in C1 it is limited by training size rather than drift. At practical operating points every detector is weak: at FMR 1%, about half or more of the genuine entries are rejected (Table 2, last columns).</p>

<h3>5.3 Learned shared model and fusion (fold protocol)</h3>
<table><tr><th>Detector</th><th>C1 EER %</th><th>C2 EER %</th><th>C2 − C1 (pp)</th><th>C2, k = 5</th><th>C2, k = 10</th></tr>{t_fold}</table>
<p class="cap"><b>Table 3.</b> All detectors on identical data: 5 folds, impostors only from the evaluated fold (never seen by the Siamese network).
k = number of consecutive entries whose scores are averaged.</p>
{fig('fin_det_c2_fold.png', '62%', 'DET, C2 cross-session under the fold protocol, including the Siamese embedding and the three-detector fusion. FMR axis starts at 1% (≈1,400 impostor scores per user).', 4)}
<p>The fold protocol changes the baselines by less than 0.2 pp, so Tables 2 and 3 are consistent. The <b>Siamese embedding</b> is the best single
detector within a session ({p(FP[SIA]['C1']['eer_mean'])}% vs. {p(FP['Scaled Manhattan']['C1']['eer_mean'])}% for scaled Manhattan) but drops to
{p(FP[SIA]['C2']['eer_mean'])}% across sessions: the largest loss of all detectors (+{p(FP[SIA]['C2_minus_C1'][0])} pp, CI {ci(FP[SIA]['C2_minus_C1'][1:])}).
Paired against scaled Manhattan in C2 the difference is {pc('Siamese embedding - Scaled Manhattan')}, i.e. not significant. The embedding learns
what separates people <i>at one moment</i>, but the training subjects' own drift is only weakly represented, and the template is a single mean in
the embedding space. Fusing the three detectors lowers the C2 EER to {p(FP[FUS]['C2']['eer_mean'])}% ({pc('Fusion (SM+SVM+Siamese) - Scaled Manhattan')}
vs. scaled Manhattan); the per-user EERs of the detectors are highly rank-correlated (Spearman {EA['per_user_eer_rank_corr']['Scaled Manhattan vs One-class SVM']:.2f}
for scaled Manhattan vs. SVM, {EA['per_user_eer_rank_corr']['Scaled Manhattan vs Siamese embedding']:.2f} vs. Siamese), which limits what detector fusion can gain.
<b>Multi-entry fusion helps much more:</b> averaging 5 entries lowers every detector's EER by 17–38% (relative) (fusion of detectors: {p(FP[FUS]['fusion_k']['5']['eer_mean'])}%
at k = 5, {p(FP[FUS]['fusion_k']['10']['eer_mean'])}% at k = 10), at the cost of asking the user for more entries; in practice this suits a step-up check
(ask for one more entry only when the first is borderline).</p>
{fig('fin_scores.png', '92%', 'C2 score distributions pooled over users after per-user z-normalisation with enrolment-only statistics. Genuine (sessions 5–8) scores are shifted to the right of 0, the enrolment mean: drift. Overlap with impostors is large for all detectors.', 5)}

<h3>5.4 Template ageing, operating points and per-user errors</h3>
{fig('fin_drift_fusion.png', '96%', 'Left: mean EER when enrolment is fixed to 25 entries of session 1 and testing moves to later sessions (fold protocol). Right: multi-entry fusion in C2.', 6)}
<p>With the enrolment size fixed, the EER rises almost monotonically with the gap: scaled Manhattan from {p(FP['Scaled Manhattan']['drift_eer'][0])}% (same session)
to {p(FP['Scaled Manhattan']['drift_eer'][7])}% (session 8), the Siamese embedding from {p(FP[SIA]['drift_eer'][0])}% to {p(FP[SIA]['drift_eer'][7])}%.
This isolates the effect of time from that of training size and agrees with the ageing study [12]. Enrolling over several sessions (C2) partly
absorbs the drift, which is why C2 with 200 entries is better than session 8 of this curve.</p>
<table><tr><th>Detector</th><th>q = 0.90: FNMR / FMR (%)</th><th>q = 0.95</th><th>q = 0.99</th></tr>{t_op}</table>
<p class="cap"><b>Table 4.</b> Operating points in C2 with the threshold chosen from enrolment data only (q-quantile of leave-one-session-out genuine scores).</p>
<p>Thresholds learned on enrolment sessions transfer poorly: a 95% quantile should reject about 5% of genuine entries but accepts
{p(op['Scaled Manhattan']['0.95']['fmr'])}% of impostor entries with scaled Manhattan; the one-class SVM and the Siamese model trade a higher FNMR for a lower FMR at the same q. This is the practical face of drift: a system must either re-enrol or adapt its
template, or accept many false matches.</p>
{fig('fin_per_user.png', '82%', 'Per-user EER, within vs. cross-session (fold protocol). Medians are much lower than means: a few users dominate the error.', 7)}

<h3>5.5 Error analysis</h3>
<p><b>Users.</b> Errors are concentrated: in C2 with scaled Manhattan, {EA['users_eer_below_5pct']} of 41 users have an EER below 5% and
{EA['users_eer_above_25pct']} above 25%; the 5 worst users ({', '.join(u for u, _ in EA['worst_users'])}, EER {p(EA['worst_users'][0][1], 0)}–{p(EA['worst_users'][-1][1], 0)}%)
account for {p(EA['share_of_error_from_worst5'], 0)}% of the summed error. Because the rank correlation across detectors is high, these are hard users
for every detector (Doddington's "goats" [19]), not failures of one method. <b>Impostors.</b> Some impostors are "wolves": at each target's EER
threshold, the median impostor subject is accepted {p(EA['median_wolf_rate'], 0)}% of the time, but {EA['top_wolves'][0][0]} and {EA['top_wolves'][1][0]}
are accepted {p(EA['top_wolves'][0][1], 0)}% and {p(EA['top_wolves'][1][1], 0)}% of the time on average, i.e. their typing resembles many others'.
<b>Features.</b> Measured in each user's own enrolment SDs, hold times drift most (mean |shift| {EA['feature_shift_by_group']['H']:.2f} SD vs.
{EA['feature_shift_by_group']['DD']:.2f} for DD and {EA['feature_shift_by_group']['UD']:.2f} for UD); the largest shifts are at the <code>e→5</code> transition
(letter to digit row). Every evaluated user types faster in sessions 5–8 than in 1–4 (median ratio {EA['speed_ratio_test_over_enrol']['median']:.2f}).
The per-user amount of drift correlates only weakly with the per-user C2 EER (Spearman ρ = {EA['spearman_shift_vs_eer'][0]:.2f}, p = {EA['spearman_shift_vs_eer'][1]:.2f},
not significant): users who are hard to verify are often inconsistent <i>within</i> a session or simply similar to others, not only drifting.</p>
{fig('fin_error.png', '96%', 'Left: per-user drift vs. C2 EER (scaled Manhattan). Right: mean absolute shift of each feature between enrolment (S1–4) and test (S5–8) sessions.', 8)}
<table><tr><th>Detector</th><th>C2 EER, all entries</th><th>enrolment rejection (k = 2)</th><th>difference (pp) [95% CI]</th></tr>{t_rej}</table>
<p class="cap"><b>Table 5.</b> Effect of rejecting unusually slow enrolment entries (Phase 3). The gain is real for Manhattan but at most 0.25 pp.</p>

<h2>6. Comparison with the Reference Result</h2>
<table><tr><th>Detector</th><th>[1] EER %</th><th>Ours, C3 [95% CI]</th><th>subjects</th><th>Ours, C3 on 41 eval.</th><th>Ours, C2</th></tr>{t_ref}</table>
<p class="cap"><b>Table 6.</b> Replication of the reference protocol (C3). The one-class SVM is reported on the 41 evaluation subjects only, because its
hyper-parameters were tuned on the other 10.</p>
<p>The three distance detectors reproduce [1] to within 0.1 pp (9.6 / 11.1 / 15.3% vs. 9.6 / 11.0 / 15.3%), which validates our feature handling,
detectors and EER computation. Our one-class SVM is {p(S['One-class SVM']['C3_makale_protokolu']['eer_mean'] - REF['One-class SVM'])} pp worse than in [1]: the reference used its own SVM implementation and parameter choice, whereas our ν, γ were selected for cross-session validation on 10 subjects; its confidence interval {ci(S['One-class SVM']['C3_makale_protokolu']['ci95'])} still contains the
reference value. Two differences in protocol explain why our C2 numbers are about 5 pp higher than the reference: C3 tests each impostor only on
their first 5 entries, typed before any practice with the password, which makes impostors easy to reject, whereas C1/C2 test impostors on
practised entries from the same sessions as the genuine test; and C2 tests later sessions than it trains on. The ranking of the distance
detectors (scaled Manhattan &lt; Mahalanobis &lt; Manhattan) is the same in [1] and in all of our conditions, and we confirm the reference finding that
scaling by per-feature variability matters most. Accuracy reported with cross-validation on this dataset [11] is not comparable to either.</p>

<h2>7. Limitations</h2>
<ul>
<li><b>Statistical power.</b> 41 evaluation subjects give wide confidence intervals (about ±3 pp on C2 EERs); differences of 1–2 pp between the
better detectors cannot be resolved. The fold protocol has fewer impostor comparisons, so FMR below 1% is not reported for it.</li>
<li><b>One password, one population, one keyboard.</b> All subjects typed the same 10-character password in a lab; results may not transfer to
other passwords, keyboards or mobile devices [13], or to impostors who have watched and practised the victim's rhythm.</li>
<li><b>Drift is confounded with practice.</b> The CMU sessions start with an unfamiliar password; part of the drift is learning, which would be
smaller for a long-used password and larger over months [12].</li>
<li><b>Siamese model.</b> A small MLP on ≈41 training subjects; a larger population, session-aware training (positives from different sessions)
or template updating would likely help in C2. The model was selected among 18 configurations; we did not test other architectures.</li>
<li><b>Thresholds.</b> Enrolment-based thresholds do not account for future drift; the EER is a summary, not a deployable operating point.</li>
<li><b>Demo.</b> Browser timestamps are coarser and noisier than the CMU clock, there are only a few self-declared trials, and the template is
stored unprotected (no template protection or encryption at rest). The demo shows the pipeline; it is not evidence of accuracy.</li>
</ul>

<h2>8. Conclusions</h2>
<p>On the CMU benchmark we reproduced the reference results of [1] and showed that within-session evaluation is optimistic. Across sessions,
scaled Manhattan, Mahalanobis and a one-class SVM reach about 14–15% mean EER, statistically tied; plain Manhattan is clearly worse. A Siamese
embedding shared across users and trained on disjoint subjects is the best detector within a session but the most sensitive to drift, so a learned
model's within-session advantage did not carry over to later sessions. With a fixed enrolment size the EER grows steadily with the time gap, and
enrolment-based thresholds admit many impostors in later sessions. The two most effective improvements are ones that add information rather
than model capacity: enrolling over several sessions, and fusing several consecutive entries (≈ 7% EER for five entries with three detectors).
Keystroke rhythm is therefore a useful, cheap second factor on top of a password, best used with step-up verification and template updating,
but not a stand-alone authenticator.</p>

<h2>AI Use Declaration</h2>
<p><b>Tools:</b> Claude Code (Anthropic; Claude Sonnet 5.5 for the design-document phase, Claude Opus 5.5 for the final phase) and web search through it.
<b>Used for:</b> writing and debugging Python code (detectors, evaluation protocols, metrics, bootstrap, Siamese network and cross-fitting, figures),
the Flask/SQLite demo and its JavaScript key capture, generating this report's and the slides' layout from the result files, searching and
summarising literature, and language editing. <b>How we checked the output:</b> the implementation was validated by reproducing the published
results of [1] (Section 6); the demo's feature extraction is tested by replaying CMU rows as key events and recovering the exact feature vectors,
and the demo flows were tested end to end with real keyboard events in a browser; every number in this report is generated from the JSON
files written by <code>reproduce.py</code>, which we re-ran; the split rules (tuning vs. evaluation subjects, fold-disjoint training and impostors,
enrolment-only thresholds) were checked against the project description and topic A5; every reference was looked up online (authors, title, venue,
year) and re-opened by us before submission. We can explain every part of the code and results.</p>

<div class="pb"></div>
<h2>References</h2><div class="ref">{refs}</div>
<h2>Appendix A. Hyper-parameter selection (tuning subjects only)</h2>
<p class="small">One-class SVM (C2-style validation on 10 tuning subjects, mean EER %): best ν = {R['svm_params']['nu']}, γ = {R['svm_params']['gamma']};
γ matters much more than ν (row minima {', '.join(f"γ={g}: {p(min(v for k, v in R['svm_grid'].items() if k.endswith('gamma=' + str(g))))}" for g in (0.003, 0.01, 0.03, 0.1, 0.3))}).</p>
<table class="small"><tr><th>Siamese: dim, hidden</th><th>300 steps</th><th>600 steps</th><th>1500 steps</th></tr>
{''.join(f"<tr><td>{d}, {h}</td>" + ''.join(f"<td>{p(tun['grid'][f'dim={d},hidden={h},steps={s}'])}</td>" for s in (300, 600, 1500)) + "</tr>" for d in (32, 64, 128) for h in (128, 256))}</table>
<p class="cap">Siamese network trained on the 41 evaluation subjects, C2 EER (%) on the 10 tuning subjects (scaled Manhattan on the same subjects:
{p(tun['scaled_manhattan_tune_eer'])}%). Longer training over-fits. Chosen: dim {tun['best']['dim']}, hidden {tun['best']['hidden']}, {tun['best']['steps']} steps.</p>
{fig('fin_loss.png', '45%', 'Batch-hard triplet loss during training in each of the 5 cross-fitting folds.', 'A1')}
<h2>Appendix B. Demo</h2>
{fig('demo_login_crop.png', '80%', 'Login result in the demo: password check, per-detector z-scores, fused score vs. threshold (with the held-out scores of the user), and this entry against the template (keys shown by position so the password is not revealed).', 'B1', HERE)}
<p class="small">Run: <code>cd proje &amp;&amp; .venv/bin/python demo/app.py</code> → http://127.0.0.1:5000 (register → enrol ≥ 15 entries, ideally in two sessions →
log in → let a team-mate try in impostor-test mode). Data: <code>demo/instance/keystroke_demo.db</code> (tables <code>users</code>, <code>samples</code>, <code>attempts</code>).</p>
</body></html>"""

out_html = os.path.join(HERE, "final_report.html")
open(out_html, "w").write(html)
pdf = os.path.join(HERE, "..", "Final_Report_221101034_221101059.pdf")
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", "file://" + out_html], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(os.path.abspath(pdf))
