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
TRN = {'Manhattan': 'Manhattan', 'Scaled Manhattan': 'Ölçekli Manhattan', 'Mahalanobis': 'Mahalanobis', 'One-class SVM': 'Tek sınıflı SVM', 'Siamese embedding': 'Siamese gömü', 'Fusion (SM+SVM+Siamese)': 'Füzyon (ÖM+SVM+Siamese)'}


def p(x, d=1): return f"{x * 100:.{d}f}".replace(".", ",")
def f2(x): return f"{x:.2f}".replace(".", ",")
def ci(c): return f"[{p(c[0])}; {p(c[1])}]"


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
FOOT = lambda n: f'<div class="ft"><span>BİL462 · A5 Tuş Vuruşu Dinamiği · Final sunumu</span><span>Herdem · Öztürk · {n}/{N}</span></div>'

t_ref = "".join(f"<tr><td>{TRN[n]}</td><td>{p(REF[n])}</td><td><b>{p(S[n]['C3_makale_protokolu']['eer_mean'])}</b></td><td>{ci(S[n]['C3_makale_protokolu']['ci95'])}</td></tr>" for n in BASE)
t_main = "".join(
    f"<tr{' class=hl' if n == FUS else ''}><td>{TRN[n]}</td><td>{p(FP[n]['C1']['eer_mean']) if 'C1' in FP[n] else '–'}</td><td><b>{p(FP[n]['C2']['eer_mean'])}</b> {ci(FP[n]['C2']['ci95'])}</td>"
    f"<td>{(('+' if FP[n]['C2_minus_C1'][0] >= 0 else '') + p(FP[n]['C2_minus_C1'][0])) if 'C2_minus_C1' in FP[n] else '–'}</td><td>{p(FP[n]['fusion_k']['5']['eer_mean'])}</td></tr>"
    for n in BASE + [SIA, FUS])
op = FP["Scaled Manhattan"]["operational"]
sm, sv, si = FP["Scaled Manhattan"], FP["One-class SVM"], FP[SIA]

HTML = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>Final – A5</title><style>{CSS}</style></head><body>

<div class="s" style="display:flex;flex-direction:column;justify-content:center">
<div class="note" style="font-size:13pt">BİL462 Biyometrik Tanıma · Proje Aşama 5 · Final Sunumu · Konu A5</div>
<h1 style="font-size:32pt;margin-top:4mm">Oturumlar Arası Parola Yazma Ritmiyle Doğrulama<br>Uzaklık dedektörleri, tek sınıflı SVM ve Siamese gömü</h1>
<p style="font-size:16pt">Bahadır İhsan Herdem (221101034) · Ömer Efe Öztürk (221101059)</p>
<p class="note" style="margin-top:8mm">CMU Keystroke Dynamics veri seti (Killourhy &amp; Maxion, DSN 2009) · tüm sayılar <code>python reproduce.py</code> ile yeniden üretilir · sonda canlı demo</p>
{FOOT(1)}</div>

<div class="s"><h2>Problem ve araştırma sorusu</h2>
<div class="row"><div style="flex:1.2"><ul>
<li>Parola çalınabilir; ama <b>nasıl</b> yazıldığı (basılı tutma süreleri, gecikmeler) kolay kopyalanmaz → ek donanım gerektirmeyen ücretsiz ikinci faktör.</li>
<li>Statik doğrulama: herkes aynı parolayı (<code>.tie5Roanl</code>) yazar; kişiye özel dedektör tek bir girişi kabul ya da reddeder.</li>
<li>Yazma ritmi günden güne <b>kayar</b> → oturum içi sonuçlar iyimser olabilir.</li>
<li><b>Soru (A5):</b> basit ve öğrenen dedektörler kullanıcıları ne kadar iyi ayırıyor, oturumlar arasında ne kadar kayıp yaşıyor?</li></ul></div>
<div style="flex:1.1">{img('cp_entry.png', 0, extra='height:auto;width:100%')}</div></div>
<div class="take">Ara sunumdan bu yana: güven aralıklı C1/C2 sonuçları · şablon yaşlanma eğrisi · Siamese gömü (çapraz uydurma) · dedektör ve çoklu giriş füzyonu · hata analizi · giriş demosu ve demo analizi.</div>
{FOOT(2)}</div>

<div class="s"><h2>Veri ve değerlendirme protokolü</h2>
<div class="row" style="margin-bottom:3mm">
<div class="tile"><div class="big">{D['subjects']}</div><span>denek · 8 oturum × 50 giriş</span></div>
<div class="tile"><div class="big">31</div><span>özellik: 11 H, 10 DD, 10 UD</span></div>
<div class="tile"><div class="big">10 / 41</div><span>ayar denekleri / değerlendirme denekleri (sabit tohum)</span></div>
<div class="tile"><div class="big">%{p(1 - D['session_median_total_s']['8'] / D['session_median_total_s']['1'], 0)}</div><span>8. oturumda 1. oturuma göre daha hızlı (medyan)</span></div></div>
<table style="width:100%"><tr><th>Koşul</th><th>Kayıt</th><th>Gerçek kullanıcı testi</th><th>Sahtekârlar</th><th>Karşılaştırma</th></tr>
<tr><td><b>C1</b> oturum içi</td><td>oturumun 1–25. girişleri</td><td>26–50. girişler, aynı oturum</td><td>diğer 40 kişi, aynı oturum</td><td>8.200 / 328.000</td></tr>
<tr><td><b>C2</b> oturumlar arası</td><td>1–4. oturumlar (200)</td><td>5–8. oturumlar</td><td>diğer 40 kişi, 5–8. oturumlar</td><td>8.200 / 328.000</td></tr>
<tr><td>Yaşlanma</td><td>1. oturum, 25 giriş</td><td>t = 1…8. oturum</td><td>diğerleri, t. oturum</td><td>her t: 1.025 / 41.000</td></tr>
<tr><td>Katlı (Siamese için)</td><td>C1/C2 gibi</td><td>C1/C2 gibi</td><td>yalnız aynı kat → görülmemiş</td><td>C2'de ≈ 59.000 sahtekâr</td></tr>
<tr><td>C3 makale tekrarı</td><td>ilk 200</td><td>son 200</td><td>diğerlerinin ilk 5'i</td><td>10.200 / 12.750</td></tr></table>
<p class="note">Ölçütler: DET (ana eğri), kullanıcı başına ortalama EER, sabit FMR'de FNMR (≥ %0,1; kişi başı 8.000 sahtekâr skorunun desteklediği çözünürlük), <b>denekleri</b> yeniden örnekleyerek %95 GA (2.000×).
Değerlendirme deneklerinde hiçbir ayar yapılmadı; eşikler yalnızca kayıt verisinden.</p>
{FOOT(3)}</div>

<div class="s"><h2>Sistem: değerlendirme ve demo için tek hat</h2>
<div class="flow"><div><b>Tuş olayları</b>basma / bırakma zamanları</div><i>→</i><div><b>31 özellik</b>H, DD, UD (s)</div><i>→</i><div><b>Kayıt</b>yalnız kullanıcının önceki girişleri</div><i>→</i>
<div><b>Dedektör</b>anomali skoru (yüksek = size daha az benziyor)</div><i>→</i><div><b>Füzyon</b>kayıttan z-normalizasyon; dedektörlerin / k girişin ortalaması</div><i>→</i><div><b>Karar</b>skor ≤ eşik</div></div>
<div class="row"><div style="flex:1"><table style="width:100%"><tr><th>Dedektör</th><th>Ne öğreniyor</th></tr>
<tr><td>Manhattan</td><td>ortalama vektör; L1 uzaklığı</td></tr>
<tr><td>Ölçekli Manhattan</td><td>ortalama + özellik başına ortalama mutlak sapma</td></tr>
<tr><td>Mahalanobis</td><td>ortalama + kovaryans (ridge: rank 21)</td></tr>
<tr><td>Tek sınıflı SVM</td><td>gerçek girişler etrafında RBF sınırı; ν={R['svm_params']['nu']}, γ={R['svm_params']['gamma']} (ayar deneklerinden)</td></tr>
<tr><td>Siamese gömü</td><td>ortak MLP 31→128→128→128, batch-hard üçlü kayıp; şablon = ortalama gömü</td></tr></table></div>
<div style="flex:.9"><ul><li><b>Ortak model kuralı:</b> Siamese ağ, değerlendirilen kişilerde <b>değil</b> başkalarında eğitilir → 5 katlı çapraz uydurma; test sahtekârları da görülmemiş.</li>
<li>Siamese boyutu/adım sayısı 10 ayar deneğinde seçildi (18 yapılandırma); uzun eğitim aşırı öğreniyor.</li>
<li>Uzaklık dedektörleri, ölçütler ve bootstrap bizim kodumuz (numpy); SVM çözücüsü sklearn; PyTorch.</li></ul></div></div>
{FOOT(4)}</div>

<div class="s"><h2>Doğrulama: referans sonucu yeniden üretiyoruz</h2>
<div class="row"><div style="flex:1"><table style="width:100%"><tr><th>Dedektör</th><th>Killourhy &amp; Maxion 2009</th><th>Bizim (C3)</th><th>%95 GA</th></tr>{t_ref}</table>
<p class="note">Aynı protokol: ilk 200 girişle eğitim, son 200 ile test, sahtekârlar = diğer 50 deneğin ilk 5 girişi. SVM yalnız 41 değerlendirme deneğinde (diğer 10'da ayarlandı).</p></div>
<div style="flex:.8"><ul><li>Uzaklık dedektörleri <b>≤ 0,1 puan</b> farkla tutuyor → özellikler, dedektörler ve EER kodu doğru.</li>
<li>SVM'imiz 1,4 puan kötü; referans değer güven aralığımızın içinde.</li>
<li>Sıralama her yerde aynı: ölçekli Manhattan &lt; Mahalanobis &lt; Manhattan → <b>değişkenliğe göre ölçekleme en önemli adım</b>.</li></ul></div></div>
<div class="take">Ancak C3 sahtekârları ilk, pratik yapılmamış girişleriyle test ediyor. Bizim C1/C2 aynı oturumlardan pratikli sahtekârlar kullanıyor → daha zor ve daha gerçekçi.</div>
{FOOT(5)}</div>

<div class="s"><h2>Ana sonuç: oturum içi ve oturumlar arası</h2>
<div class="row"><div style="flex:1.05"><table style="width:100%"><tr><th>Dedektör</th><th>C1 EER %</th><th>C2 EER % [%95 GA]</th><th>C2 − C1 puan</th><th>C2, k=5</th></tr>{t_main}</table>
<p class="note">Katlı protokol (tüm dedektörler için aynı veri, görülmemiş sahtekârlar). 41 denek.</p></div>
<div style="flex:.95">{img('fin_det_c2_fold.png', 120)}</div></div>
{FOOT(6)}</div>

<div class="s"><h2>Öğrenen modeller: bugün en iyi, yarın en kötü</h2>
<div class="row"><div style="flex:1"><ul>
<li><b>Siamese</b> oturum <i>içinde</i> en iyi dedektör: <span class="g">%{p(si['C1']['eer_mean'])}</span>, ölçekli Manhattan %{p(sm['C1']['eer_mean'])}.</li>
<li>Oturumlar arasında <span class="k">%{p(si['C2']['eer_mean'])}</span>'e düşüyor: tüm dedektörler içinde en büyük kayıp (+{p(si['C2_minus_C1'][0])} puan, GA {ci(si['C2_minus_C1'][1:])}).</li>
<li>Ölçekli Manhattan da kaybediyor (+{p(sm['C2_minus_C1'][0])} puan), <b>C2'de 8 kat fazla kayıt verisine rağmen</b>.</li>
<li>Mahalanobis C1→C2 iyileşiyor: 25 girişte darboğaz kovaryans tahmini, kayma değil.</li>
<li>C2'de ölçekli Manhattan, Mahalanobis, SVM ve Siamese <b>istatistiksel olarak eşit</b> (~%14–16).</li></ul>
<div class="take">Oturum içi sonuçlar iyimser; en çok da öğrenen gömü için.</div></div>
<div style="flex:1.25">{img('fin_scores.png', 0, extra='height:auto;width:100%')}<p class="note">Sonraki oturumların gerçek kullanıcı skorları kayıt ortalamasının (0) sağına kayıyor: bu kaymadır. Sahtekârlarla örtüşme büyük.</p></div></div>
{FOOT(7)}</div>

<div class="s"><h2>Şablon yaşlanması ve gerçek eşikler</h2>
<div class="row"><div style="flex:1.15">{img('fin_ageing_only.png', 112, HERE)}</div>
<div style="flex:1"><ul><li>Kayıt 1. oturumun 25 girişine sabitken EER aradaki süreyle artıyor: ölçekli Manhattan %{p(sm['drift_eer'][0])} → %{p(sm['drift_eer'][7])}, Siamese %{p(si['drift_eer'][0])} → %{p(si['drift_eer'][7])}.</li>
<li>Eşik yalnız kayıttan seçilip (kendi dışarıda bırakılan skorların %95'liği) 5–8. oturumlara uygulanınca, ölçekli Manhattan: FNMR %{p(op['0.95']['fnmr'])} ama FMR <span class="k">%{p(op['0.95']['fmr'])}</span>.</li>
<li>FMR %1'de gerçek girişlerin yaklaşık yarısı reddediliyor.</li></ul>
<div class="take">Gerçek bir sistem şablonu yeniden kaydetmeli / güncellemeli ya da çok sayıda yanlış eşleşmeyi kabullenmeli.</div></div></div>
{FOOT(8)}</div>

<div class="s"><h2>Ne işe yarıyor: daha büyük model değil, daha çok kanıt</h2>
<div class="row"><div style="flex:1">{img('fin_kfusion_only.png', 112, HERE)}<p class="note">Renkler: <span style="color:#8a8f98">■ Manhattan</span> <span style="color:#1b7f3b">■ ölçekli Manhattan</span> <span style="color:#c0392b">■ Mahalanobis</span> <span style="color:#1f5fbf">■ tek sınıflı SVM</span> <span style="color:#8e44ad">■ Siamese</span> <span style="color:#e67e22">■ füzyon ÖM+SVM+Siamese</span></p></div>
<div style="flex:1"><ul><li><b>Dedektör füzyonu</b> (ÖM + SVM + Siamese, kayıttan z-normalizasyon): C2 %{p(FP[FUS]['C2']['eer_mean'])} (%15,0'a karşı; kazancın GA'sı 0'ı içeriyor). Dedektörler <b>aynı kullanıcılarda</b> hata yapıyor (Spearman {f2(EA['per_user_eer_rank_corr']['Scaled Manhattan vs One-class SVM'])}).</li>
<li><b>Çoklu giriş füzyonu</b> (ardışık k girişin ortalaması): k=5 → %{p(FP[FUS]['fusion_k']['5']['eer_mean'])}, k=10 → %{p(FP[FUS]['fusion_k']['10']['eer_mean'])}.</li>
<li><b>Çok oturumlu kayıt</b>: 1–4. oturumlarla C2, sonraki her oturumda 25 girişlik yaşlanma eğrisinden iyi.</li></ul>
<div class="take">Pratik tasarım: normalde tek giriş, skor sınırdaysa bir giriş daha iste (step-up).</div></div></div>
{FOOT(9)}</div>

<div class="s"><h2>Hata analizi</h2>
<div class="row"><div style="flex:1"><ul>
<li><b>Hatayı az sayıda kullanıcı belirliyor:</b> 41 kişiden {EA['users_eer_below_5pct']}'i %5 EER'in altında, {EA['users_eer_above_25pct']}'i %25'in üstünde; en kötü 5 kişi toplam hatanın %{p(EA['share_of_error_from_worst5'], 0)}'ini oluşturuyor (her dedektör için zor, "keçiler").</li>
<li><b>Kurtlar:</b> EER eşiğinde medyan sahtekâr %{p(EA['median_wolf_rate'], 0)} kabul ediliyor, ama {EA['top_wolves'][0][0]} %{p(EA['top_wolves'][0][1], 0)} ve {EA['top_wolves'][1][0]} %{p(EA['top_wolves'][1][1], 0)}.</li>
<li><b>Özellikler:</b> en çok basılı tutma süreleri kayıyor ({f2(EA['feature_shift_by_group']['H'])} SS, DD'de {f2(EA['feature_shift_by_group']['DD'])}); en büyük kayma <code>e→5</code>'te (harf → rakam sırası). 41 kullanıcının hepsi hızlanmış.</li>
<li>Kayma büyüklüğü ve kişi başı EER: ρ = {f2(EA['spearman_shift_vs_eer'][0])} (p = {f2(EA['spearman_shift_vs_eer'][1])}), anlamlı değil → zor kullanıcılar tutarsız ya da başkalarına benziyor.</li>
<li>Yavaş girişlerin yalnız kayıtta reddi: ≤ 0,25 puan kazanç.</li></ul></div>
<div style="flex:1.15">{img('fin_error.png', 62)}{img('fin_per_user.png', 52)}</div></div>
{FOOT(10)}</div>

<div class="s"><h2>Demo: RitimKapısı, parola + ritimle giriş</h2>
<div class="row"><div style="flex:1"><ul>
<li>Flask + SQLite, localhost'ta çalışır; tarayıcı tuş basma/bırakma zamanlarını kaydeder; aynı özellik kodu (CMU satırları tuş olayı olarak oynatılınca birebir aynı vektör, birim testli).</li>
<li>Kayıt ol → en az 15 giriş kaydet (2 oturum daha iyi) → giriş yap. Yazım hatası / Backspace girişi iptal eder (CMU'daki gibi).</li>
<li>Karar = rapordaki kuralın aynısı: ÖM + SVM (+ CMU parolasında Siamese), kendi dışarıda bırakılan girişlerden z-normalizasyon ve eşik; 3 güvenlik seviyesi; k = 1 ya da 3 giriş.</li>
<li><b>Saklama:</b> parola yalnız tuzlu scrypt özeti; şablon = süre sayıları, tuş metni yok; yalnız yerel; "verilerimi sil" (zincirleme).</li>
<li><b>Demo verisi:</b> verisini paylaşmayı kabul eden gönüllü katılımcılardan (hoca onaylı, kayıtta rıza kutusu). Sahtekâr testi modunda başka bir katılımcı parolanızı yazar. Sonuçlar sitedeki <b>"Demo analizi"</b> sayfasında; CMU değerlendirmesine karışmaz.</li></ul></div>
<div style="flex:1">{img('demo_impostor_crop.png', 0, HERE, 'height:auto;width:100%;border:1px solid #ccd6ea;border-radius:2mm')}</div></div>
{FOOT(11)}</div>

<div class="s" style="display:flex;flex-direction:column;justify-content:center;align-items:center">
<h1 style="font-size:34pt">Canlı demo</h1>
<p style="font-size:17pt">1 · kayıtlı kullanıcı giriş yapar &nbsp;→&nbsp; 2 · başka bir katılımcı aynı parolayı yazar (sahtekâr testi) &nbsp;→&nbsp; 3 · k = 3 giriş &nbsp;→&nbsp; 4 · demo kayıtları ve demo analizi</p>
<p class="note">Demo analizi: katılımcıların denemeleri üzerinden FMR/FNMR, skor payı dağılımı, havuzlanmış EER ve katılımcı bazında tablo. Tarayıcı zamanlaması CMU saatinden farklı olduğu için bu sonuçlar CMU sonuçlarıyla doğrudan karşılaştırılmaz.</p>
{FOOT(12)}</div>

<div class="s"><h2>Sınırlılıklar ve sonuçlar</h2>
<div class="row"><div style="flex:1"><h3 style="color:#12306b;margin:0">Sınırlılıklar</h3><ul>
<li>41 denek → yaklaşık ±3 puanlık GA; küçük farklar ayırt edilemiyor.</li>
<li>Tek parola, laboratuvar klavyesi; sahtekârlar kurbanın ritmini çalışmadı.</li>
<li>Kaymanın bir kısmı yeni bir parolayı öğrenmekten kaynaklanıyor.</li>
<li>Küçük Siamese MLP, ≈43 eğitim deneği, oturum farkındalıklı eğitim yok.</li>
<li>Demo: tarayıcı zamanlaması, beyana dayalı roller, şablon korumasız saklanıyor.</li></ul></div>
<div style="flex:1.1"><h3 style="color:#12306b;margin:0">Sonuçlar</h3><ul>
<li>Referans sonuç yeniden üretildi (ölçekli Manhattan %9,6).</li>
<li>Oturumlar arası: en iyi tekil dedektörler ≈ %14–15 EER, istatistiksel olarak eşit.</li>
<li>Öğrenen gömü: oturum içinde en iyi, oturumlar arasında en büyük kayıp.</li>
<li>Hata zamanla artıyor; kayıttan seçilen eşikler iyi taşınmıyor.</li>
<li>En etkili: çok oturumlu kayıt ve çoklu giriş füzyonu (k = 5'te ≈ %7).</li></ul>
<div class="take">Tuş ritmi ucuz ve yararlı bir <b>ikinci faktördür</b>, tek başına bir kimlik doğrulayıcı değil.</div></div></div>
{FOOT(13)}</div>

<div class="s" style="display:flex;flex-direction:column;justify-content:center">
<h1 style="font-size:32pt">Teşekkürler · Sorular?</h1>
<p class="note" style="font-size:12.5pt;max-width:270mm"><b>Kod:</b> <code>python reproduce.py</code> (tüm sayılar, ~1 dk) · <code>python demo/app.py</code> (demo) · <code>python tests/test_demo.py</code><br>
<b>Kaynak:</b> K. S. Killourhy, R. A. Maxion, “Comparing Anomaly-Detection Algorithms for Keystroke Dynamics,” DSN 2009. Diğer kaynaklar raporda.<br>
<b>Yapay zekâ kullanımı:</b> Claude Code (Anthropic) kodlama desteği, hata ayıklama, rapor/slayt düzeni ve dil düzenlemesi için kullanıldı; [Killourhy &amp; Maxion] sonucunu yeniden üreterek, birim/uçtan uca testlerle, tüm betikleri yeniden çalıştırarak ve her kaynağı kendimiz kontrol ederek doğrulandı.</p>
{FOOT(14)}</div>
</body></html>"""

out_html = os.path.join(HERE, "final_slides.html")
open(out_html, "w").write(HTML)
pdf = os.path.join(HERE, "..", "Final_Slides_221101034_221101059.pdf")
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", "file://" + out_html], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(os.path.abspath(pdf))
