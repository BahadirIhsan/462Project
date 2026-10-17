import json, os, subprocess, base64
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
R = json.load(open(os.path.join(RES, "results.json")))
D = json.load(open(os.path.join(RES, "data_stats.json")))
S = R["summary"]
N = ["Manhattan", "Scaled Manhattan", "Mahalanobis", "One-class SVM"]
PAPER = {"Manhattan": 0.153, "Scaled Manhattan": 0.096, "Mahalanobis": 0.110, "One-class SVM": 0.102}

def p(x, d=1): return f"%{x*100:.{d}f}".replace(".", ",")
def pc(x): return f"{x*100:.1f}".replace(".", ",")
def ci(c): return f"[{c[0]*100:.1f}–{c[1]*100:.1f}]".replace(".", ",")
def img(name, w="100%"):
    b = base64.b64encode(open(os.path.join(RES, name), "rb").read()).decode()
    return f'<img src="data:image/png;base64,{b}" style="width:{w}">'

def tbl(head, rows, cls=""):
    h = "".join(f"<th>{c}</th>" for c in head)
    r = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f'<table class="{cls}"><tr>{h}</tr>{r}</table>'

t_rep = tbl(["Dedektör", "Makale (51 kişi)", "Bizim (51 kişi)", "Bizim (41 kişi)"],
    [[n, p(PAPER[n], 1),
      (f"{p(S[n]['C3_makale_protokolu']['eer_mean'])} {ci(S[n]['C3_makale_protokolu']['ci95'])}" if n != "One-class SVM" else "— (ayar kişileri dahil olmasın diye hesaplanmadı)"),
      f"{p(S[n]['C3_eval41']['eer_mean'])} {ci(S[n]['C3_eval41']['ci95'])}"] for n in N])
t_main = tbl(["Dedektör", "C1 oturum içi EER", "C2 oturumlar arası EER", "C2 − C1 farkı (puan)", "C2: FNMR @ FMR=%1", "C2: FNMR @ FMR=%0,1"],
    [[n, f"{p(S[n]['C1_oturum_ici']['eer_mean'])} {ci(S[n]['C1_oturum_ici']['ci95'])}",
      f"{p(S[n]['C2_oturumlar_arasi']['eer_mean'])} {ci(S[n]['C2_oturumlar_arasi']['ci95'])}",
      f"{R['c2_minus_c1'][n][0]*100:+.1f} {ci(R['c2_minus_c1'][n][1:])}".replace(".", ","),
      p(S[n]['C2_oturumlar_arasi']['fnmr@fmr1%'], 0), p(S[n]['C2_oturumlar_arasi']['fnmr@fmr0.1%'], 0)] for n in N])
t_drift = tbl(["Dedektör"] + [f"Oturum {i}" for i in range(1, 9)],
    [[n] + [p(v) for v in S[n]["drift_eer"]] for n in N])
t_fus = tbl(["Dedektör", "k=1", "k=3", "k=5", "k=10"],
    [[n] + [f"{p(S[n]['fusion'][str(k)]['eer_mean'])}" for k in (1, 3, 5, 10)] for n in N])
t_op = tbl(["Dedektör", "Hedef: gerçek kullanıcıların %90'ı geçsin → gerçekleşen FNMR", "Gerçekleşen FMR (yabancı kabul)"],
    [[n, p(R["operational"][n]["0.9"]["fnmr"]), p(R["operational"][n]["0.9"]["fmr"])] for n in N])
sp = R["svm_params"]
best_c2 = min(N, key=lambda n: S[n]["C2_oturumlar_arasi"]["eer_mean"])

CSS = """
@page { size: A4; margin: 18mm 17mm 18mm 17mm; }
body { font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; font-size: 10.6pt; line-height: 1.5; color: #1d2330; }
h1 { font-size: 24pt; margin: 0 0 4px; line-height: 1.15; }
h2 { font-size: 15pt; margin: 26px 0 6px; padding-top: 6px; border-top: 2px solid #1f5fbf; color: #12306b; page-break-after: avoid; }
h3 { font-size: 11.8pt; margin: 16px 0 3px; color: #12306b; page-break-after: avoid; }
p { margin: 5px 0 7px; }
.sub { color: #55607a; font-size: 11pt; margin-bottom: 12px; }
.meta { font-size: 9.6pt; color: #55607a; margin-bottom: 14px; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 9.2pt; page-break-inside: avoid; }
th { background: #eaf0fb; text-align: left; padding: 4px 6px; border: 1px solid #c9d5ee; }
td { padding: 4px 6px; border: 1px solid #dde4f2; vertical-align: top; }
.box { border-left: 4px solid #1f5fbf; background: #f3f7ff; padding: 7px 11px; margin: 9px 0; page-break-inside: avoid; }
.box b.t { color: #12306b; }
.why { border-left-color: #1b7f3b; background: #f1faf4; }
.why b.t { color: #17622f; }
.warn { border-left-color: #c0392b; background: #fdf3f1; }
.warn b.t { color: #a02d21; }
code { background: #eef1f6; padding: 0 3px; border-radius: 3px; font-size: 9.4pt; }
.flow { display: flex; flex-wrap: wrap; align-items: stretch; gap: 5px; margin: 10px 0 14px; }
.flow div { flex: 1 1 105px; border: 1.5px solid #1f5fbf; border-radius: 6px; padding: 6px 7px; text-align: center; font-size: 8.9pt; background: #f3f7ff; }
.flow div b { display: block; color: #12306b; margin-bottom: 2px; }
.flow span.ar { flex: 0 0 auto; align-self: center; color: #1f5fbf; font-weight: bold; }
img { margin: 6px 0; page-break-inside: avoid; }
.cap { font-size: 9pt; color: #55607a; margin-top: -2px; }
.two { display: flex; gap: 10px; } .two > div { flex: 1; }
ul, ol { margin: 4px 0 8px 18px; padding: 0; } li { margin: 2px 0; }
.pb { page-break-before: always; }
"""

HTML = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>A5 Okuma Kılavuzu</title><style>{CSS}</style></head><body>

<h1>Tuş Vuruşu Dinamiği ile Parola Doğrulama</h1>
<div class="sub">BİL462 Biyometrik Tanıma · Proje A5 · Okuma kılavuzu: ne yaptık, nasıl yaptık, neden böyle yaptık</div>
<div class="meta">Bahadır İhsan Herdem (221101034) · Ömer Efe Öztürk (221101059) · 17 Ekim 2026 · Durum: veri analizi, dedektörler ve değerlendirme tamamlandı; tasarım dokümanı, demo ve ikinci geliştirme sırada</div>

<div class="box"><b class="t">Bu belge ne işe yarar?</b> Hocaya vereceğimiz bir belge değil, bizim için bir okuma kılavuzu. Projedeki her kararın arkasındaki gerekçeyi anlatır; böylece sunumda “neden SVM?”, “neden oturuma göre ayırdınız?”, “bu sayı ne demek?” sorularına kendi cümlelerinizle cevap verebilirsiniz. Hocanın kuralı açık: sunumda kodun ve sonucun her parçasını açıklayabilmemiz gerekiyor. Aşağıdaki yeşil kutular (<i>Neden böyle?</i>) tam olarak bunun içindir.</div>

<h2>1. Proje bir bakışta</h2>
<p><b>Soru (hocanın A5 tanımı):</b> Aynı parolayı yazan kullanıcıları yazma ritimlerinden ayırabilir miyiz ve günler geçtikçe bu ayrım ne kadar bozulur?</p>
<p><b>Ana sonuç:</b> Oturum içi ile oturumlar arası hata oranı arasındaki fark. Hocanın deyişiyle “aynı oturumda ölçülen başarım yanıltıcı derecede iyidir, çünkü kişinin o günkü ritmi sabittir.”</p>
<div class="flow">
<div><b>1. Veri</b>CMU: 51 kişi × 8 oturum × 50 giriş</div><span class="ar">→</span>
<div><b>2. Özellik</b>31 zamanlama değeri (H, DD, UD)</div><span class="ar">→</span>
<div><b>3. Dedektör</b>Kişi başına bir model: 3 mesafe + 1 SVM</div><span class="ar">→</span>
<div><b>4. Skor</b>Anomali skoru: yazış ne kadar “senin gibi değil”</div><span class="ar">→</span>
<div><b>5. Ölçüm</b>DET, EER, kullanıcı başına EER, güven aralığı</div><span class="ar">→</span>
<div><b>6. Demo</b>Localhost giriş ekranı</div>
</div>

<h3>Şu ana kadar yapılanlar</h3>
<ul>
<li>Veri analizi ve 31 özelliğin incelenmesi (bölüm 3)</li>
<li>Dört dedektörün kendi kodumuzla yazılması: Manhattan, Scaled Manhattan, Mahalanobis, One-class SVM (bölüm 5)</li>
<li>Makalenin sonuçlarının yeniden üretilmesi (doğrulama testi): <b>başarılı</b> (bölüm 6.1)</li>
<li>Oturum içi, oturumlar arası, zamanla bozulma, skor birleştirme ve eşik seçimi deneyleri (bölüm 6)</li>
</ul>
<p>Kod klasörü: <code>~/Desktop/462Project/proje/</code>. Her sayıyı <code>run_all.py</code> ile tek komutta yeniden üretebiliyoruz (hocanın istediği “sonuçları yeniden üreten betik”).</p>

<h2>2. Temel kavramlar (kısa)</h2>
<h3>Doğrulama (1:1)</h3>
<p>Kullanıcı “ben Bahadır’ım” der ve parolasını yazar. Sistem tek bir soruyu yanıtlar: <i>bu yazış gerçekten Bahadır’a ait mi?</i> “Bu kişi kim?” sorusu (1:N tanımlama) değildir. Demomuz da bu yüzden bir doğrulama demosudur.</p>
<h3>İki hata türü</h3>
{tbl(["Terim","Anlamı","Günlük dilde"],[
["FMR","Yabancının yanlışlıkla kabul edilme oranı","Güvenlik hatası: yabancı içeri girdi"],
["FNMR","Gerçek kullanıcının yanlışlıkla reddedilme oranı","Rahatsızlık hatası: sen girdin, sistem almadı"],
["EER","FMR = FNMR olacak şekilde eşik seçilince ortak değer","Tek sayıyla özet; düşük iyi"],
["DET eğrisi","Eşik değiştikçe FMR ile FNMR’nin ödünleşimi","Bütün çalışma noktaları; sol alta yakın iyi"]])}
<div class="box why"><b class="t">Neden tek bir “doğruluk yüzdesi” vermiyoruz?</b> Çünkü iki hata birbirine bağlıdır: eşiği gevşetirsek gerçek kullanıcı rahat girer ama yabancı da girer; sıkarsak tersi olur. “%90 doğruluk” hangi eşikte olduğunu söylemez. Hocanın tekrar tekrar vurguladığı şey bu: sayının ne anlama geldiğini savunabilmek.</div>
<h3>Anomali (tek sınıf) dedektörü</h3>
<p>Her kullanıcı için yalnızca <b>o kullanıcının</b> örnekleriyle bir model eğitilir. Model “bu kişinin normal yazışı nasıl?” sorusunu öğrenir. Yeni bir giriş geldiğinde modelin normalinden ne kadar uzak olduğunu bir <b>anomali skoru</b> olarak verir (büyük skor = daha çok yabancı). Eşik üstündeyse reddedilir.</p>
<div class="box why"><b class="t">Neden her kullanıcıya ayrı model, neden 51 kişilik tek sınıflandırıcı değil?</b> Gerçek bir sistemde yeni kullanıcı kayıt olduğunda elimizde sadece onun örnekleri vardır, başkalarının verisi yoktur ve her yeni kayıtta herkesi yeniden eğitmek istemeyiz. Makale de (Killourhy &amp; Maxion, 2009) aynı senaryoyu kullanır. Bonus: her kullanıcının kendi modeli olduğundan hocanın “kişi-ayrık bölme” kuralı burada geçerli değildir; onun yerine zamana göre bölme kuralı geçerlidir.</div>

<h2 class="pb">3. Veri: CMU Keystroke Dynamics Benchmark</h2>
<p><b>İçeriği:</b> {D['n_rows']:,} giriş = 51 kişi × 8 oturum × 50 tekrar (kişi başına 400). Herkes <b>aynı</b> parolayı yazar: <code>.tie5Roanl</code> + Enter (Shift ile R ve 5 gibi büyük/özel karakterler içerir). Oturumlar arasında en az bir gün bırakılmıştır, böylece günden güne değişim ölçülebilir.</p>
<p><b>Özellikler ({D['n_features']} adet):</b> {D['n_H']} tuş-basılı-kalma süresi (<b>H</b>, bir tuşun basılı kaldığı süre), {D['n_DD']} tuştan-tuşa süre (<b>DD</b>, bir tuşa basıştan sonrakine basışa), {D['n_UD']} bırakma-basma süresi (<b>UD</b>, bir tuşu bırakıştan sonrakine basışa). 11 tuş (10 karakter + Enter) olduğu için 11 + 10 + 10 = 31.</p>
<div class="box why"><b class="t">Neden bu veri?</b> Hocanın A5 için belirttiği tek veri bu; herkese açık, küçük bir metin dosyası. Daha önemlisi referans makalenin de aynı verisi: yani sonuçlarımızı yayımlanmış sayılarla doğrudan karşılaştırabiliriz. Lisans/kullanım koşullarını tasarım dokümanı yazarken CMU sayfasından ayrıca teyit edeceğiz.</div>
{img('rhythm.png','100%')}
<div class="cap">Şekil 1. (a) Üç kullanıcının ortalama zamanlama profili: herkesin “parmak izi” farklı. (b) Aynı kişi günden güne değişiyor (oturum ortalamaları). Not: (a)’daki çukur, değeri sıfıra yakın olan bir UD özelliğidir; UD negatif olabildiği için log ölçekte böyle görünür.</div>

<h3>Veri kalitesi (9 Kasım kontrol noktası sunumu için not)</h3>
{tbl(["Gözlem","Değer"],[
["Eksik değer",str(D['n_missing'])],
["Ortalama H / DD / UD",f"{D['mean_H_ms']:.0f} ms / {D['mean_DD_ms']:.0f} ms / {D['mean_UD_ms']:.0f} ms"],
["Parolayı yazma süresi (medyan, %99, en uzun)",f"{D['median_total_s']:.1f} sn, {D['p99_total_s']:.1f} sn, {D['max_total_s']:.0f} sn"],
["Kişi başına medyan yazma süresi aralığı",f"{D['subject_median_total_min_s']:.1f} – {D['subject_median_total_max_s']:.1f} sn (kişiler arası büyük fark = iyi ayırt edici sinyal)"],
["Medyanın 3 katından uzun girişler",p(D['frac_total_gt_3x_median'],2)+" (duraksama/hata olabilir; şimdilik silmedik)"],
["Negatif UD değeri",f"{D['n_negative_UD']:,} (hata değil: sonraki tuşa, öncekini bırakmadan basıldı; hızlı yazanlarda normal)"]])}
<div class="box warn"><b class="t">Dürüstlük notu:</b> Şimdiye kadar hiçbir örneği reddetmedik. Hocanın checkpoint sunumunda “preprocessing’de reddedilen örnekler” istiyor; elimizde reddedilen yok, bunu açıkça söyleyeceğiz. İstersek aykırı girişleri temizleyen bir varyant (ör. “Manhattan filtered”) ekleyip etkisini ölçebiliriz.</div>

<h2>4. Deney tasarımı: neden böyle bölüyoruz?</h2>
<h3>4.1 Zamana göre bölme ve sızıntı önleme</h3>
<p>Hocanın kuralı: eğitim <b>önceki</b> oturumlardan, test <b>sonraki</b> oturumlardan; test verisiyle ne eğitim ne ayar yapılır; ayar/eğitimde kullanılan kişiler testte yabancı olarak da görünmez (kendi kayıt örnekleri hariç).</p>
<div class="box why"><b class="t">Neden bu kadar katı?</b> Rastgele bölseydik aynı oturumdan örnekler hem eğitime hem teste girerdi. Kişinin o günkü ritmi sabit olduğundan model “bu oturumu” ezberlerdi ve sonuç gerçekçi olmayacak kadar iyi çıkardı. Bizim projenin konusu tam olarak bu iyimserliği ölçmek.</div>
<h3>4.2 Ayar grubu ve değerlendirme grubu</h3>
<p>51 kişiyi rastgele (sabit tohum 0) ikiye ayırdık: <b>10 ayar kişisi</b> ({", ".join(R['tune_users'])}) ve <b>41 değerlendirme kişisi</b>. SVM’nin hiperparametreleri yalnızca ayar kişilerinin ilk 4 oturumuyla seçildi. Bütün sonuçlar değerlendirme kişileri üzerinde hesaplanır.</p>
<div class="box why"><b class="t">Neden?</b> Hiperparametre seçmek de bir tür eğitimdir. Aynı kişilerle hem seçip hem raporlarsak sonuç iyimser olur. Böylece hocanın “ayarda kullanılan kişiler testte yer almamalı” kuralını sağlıyoruz. Bedeli: 51 yerine 41 kişi ve yabancı sayısı 40’a düşüyor.</div>
<h3>4.3 Üç ayrı koşul</h3>
{tbl(["Koşul","Eğitim","Test (gerçek kullanıcı)","Test (yabancı)","Ne için?"],[
["<b>C1</b> oturum içi","Her oturumun ilk 25 girişi","Aynı oturumun son 25 girişi","Diğer 40 kişinin aynı oturumdaki son 25 girişi","İyimser taban"],
["<b>C2</b> oturumlar arası","Oturum 1–4 (200 giriş)","Oturum 5–8 (200 giriş)","Diğer 40 kişinin oturum 5–8 girişleri (8000)","Gerçekçi senaryo"],
["<b>C3</b> makale protokolü","İlk 200 giriş","Kalan 200 giriş","Her yabancının ilk 5 girişi","Makaleyle karşılaştırma ve kod doğrulaması"],
["<b>Zamanla bozulma</b>","Oturum 1’in ilk 25 girişi","Oturum t’nin son 25 girişi (t=1…8)","Aynı oturumdaki diğer kişiler","Temiz karşılaştırma"]])}
<div class="box warn"><b class="t">Önemli tuzak (kendi tasarımımızda yakaladık):</b> C1 ile C2’yi doğrudan kıyaslamak adil değil, çünkü C1’de 25, C2’de 200 örnekle eğitiyoruz; eğitim verisi farkı oturum farkıyla karışıyor. Bu yüzden eğitim ve test boyutunu sabit tutan <b>zamanla bozulma</b> deneyini ekledik: aynı 25 girişle eğitim, ama test günden güne uzaklaşıyor. Temiz kanıt bu.</div>
<h3>4.4 Neden bu metrikler ve bu eşik kuralı?</h3>
<ul>
<li><b>Kullanıcı başına EER:</b> Her kullanıcı için ayrı hesaplanır, sonra ortalaması alınır (makale de böyle). Bazı kullanıcılar çok tutarlı, bazıları çok değişken yazar; ortalama bunu gizler, bu yüzden dağılımı da gösteriyoruz.</li>
<li><b>EER’in eşiği:</b> EER’de eşik test skorlarına bakılarak seçilir (makalenin de yaptığı gibi). Bu bir <i>çalışma noktası değil, karşılaştırma ölçüsüdür</i> ve iyimser kalır. Gerçekçi olanı için ayrıca “eşiği sadece eğitim döneminden seç” deneyi yaptık (bölüm 6.5).</li>
<li><b>Güven aralığı:</b> 41 kullanıcıyı yerine koyarak 2000 kez yeniden örnekleyip ortalama EER’in %95 aralığını bulduk. Hocanın istediği “denekleri yeniden örnekleyen bootstrap” budur. Neden kişileri örnekliyoruz, girişleri değil? Aynı kişinin girişleri birbirine benzer; bağımsız değiller. Bağımsız birim kişidir.</li>
<li><b>Düşük FMR’de rapor:</b> Hata oranını ancak karşılaştırma sayımızın destekleyeceği düzeyde veririz. Kullanıcı başına 8000 yabancı girişle FMR %0,1 düzeyi (8 olay) sınırda destekleniyor; daha düşüğünü raporlamıyoruz.</li>
</ul>

<h2 class="pb">5. Dedektörler: ne yapıyorlar, neden bunlar?</h2>
<p>Hocanın şartı: üç uzaklık tabanlı dedektör + bir öğrenen model; en az bir aşama bizim kendi kodumuz. Hepsini <code>keystroke/detectors.py</code> içinde numpy ile kendimiz yazdık (SVM için <code>scikit-learn</code> çekirdeği kullandık ve bunu raporda beyan edeceğiz).</p>
{tbl(["Dedektör","Nasıl çalışır?","Güçlü / zayıf yanı"],[
["<b>Manhattan</b>","Eğitim girişlerinin ortalama vektörünü alır. Test girişi için 31 özelliğin her birinin ortalamadan farkının mutlak değerlerini toplar.","Çok basit. Ama bütün özellikleri eşit sayar; oysa tuştan tuşa süreler (DD) basılı kalma sürelerinden (H) çok daha oynaktır, böylece oynak özellikler skoru domine eder."],
["<b>Scaled Manhattan</b>","Aynı, ama her özelliğin farkını o özelliğin eğitimdeki ortalama mutlak sapmasına böler.","Oynak özelliklerin etkisini azaltır. Makalenin 14 dedektör içinde birincisi."],
["<b>Mahalanobis</b>","Ortalamadan uzaklığı özelliklerin <i>birbirleriyle ilişkisini</i> de hesaba katarak ölçer (kovaryans matrisinin tersi).","Korelasyonu görür; ama 31×31 kovaryansı az örnekle kestirmek zordur (C1’de 25 örnek var, bu yüzden küçük bir düzenlileştirme ekledik)."],
["<b>One-class SVM</b>","Eğitim girişlerini çekirdek (RBF) ile yüksek boyutlu bir uzaya taşır ve onları orijinden ayıran bir sınır öğrenir. Sınırın içi “bu kişinin normali”.","Doğrusal olmayan sınır öğrenebilir; hiperparametreleri var (ν ve γ)."]])}
<div class="box why"><b class="t">Makalenin en önemli dersi ve bizim sonuçlarımızla uyumu:</b> Makale, en iyi dedektörlerin ortak noktasının özellikleri <b>ölçeklemek</b> olduğunu söylüyor (Euclidean → Mahalanobis, Manhattan → Scaled Manhattan gibi). Bizim sonuçlarımızda da Manhattan’dan Scaled Manhattan’a geçmek hatayı yaklaşık %16’dan %10’a indiriyor.</div>

<h3>5.1 Öğrenen model olarak neden One-class SVM?</h3>
<p>Seçenekler arasında şu karşılaştırmayı yaptık (makalenin Tablo 2’deki sayıları, EER):</p>
{tbl(["Aday","Makaledeki EER","Karar ve gerekçe"],[
["One-class SVM","%10,2 (en iyi 4’te)","<b>Seçildi.</b> Yalnızca kullanıcının kendi verisiyle eğitilir, makalede güçlü, doğrudan karşılaştırılabilir."],
["Neural Network (auto-assoc)","%16,1","Makalede SVM’den belirgin kötü; 500 devirlik eğitim ve ek ayar gerektiriyor."],
["Neural Network (standard)","%82,8","Makalede yalnızca “1” çıktısı verecek şekilde eğitilmiş (hiç negatif örnek yok); işe yaramadı."],
["Fuzzy Logic","%22,1","Elle tasarlanmış kümeler, zayıf."],
["k-Means","%37,2","Zayıf."],
["Paylaşımlı sinir ağı gömüsü (Siamese)","Makalede yok","Daha modern; <b>ikinci geliştirme olarak</b> ekleyeceğiz (bölüm 8)."]])}
<div class="box why"><b class="t">SVM’yi seçme gerekçelerimiz (dürüst sürüm):</b>
<ol>
<li>Hocanın “bir öğrenen model” şartını sağlıyor.</li>
<li>Referans makalede ölçülmüş: kendi sayımızı yayımlanmış %10,2 ile kıyaslayabiliyoruz.</li>
<li>Tek sınıf: kayıt anında yalnızca kullanıcının verisi gerekir; bu, demoda da doğrudan geçerli (kayıt oturumlarının verisi ile birkaç saniyede eğitilir).</li>
<li>Küçük veriyle çalışır (25–200 örnek) ve skorları <i>yumuşak</i>, yani birden fazla girişin skoru birleştirilince çok kazanır (bölüm 6.4).</li>
<li>scikit-learn’de hazır, ama hiperparametre seçimi, ölçekleme ve skor üretimi bizim kodumuz.</li>
</ol>
<b>SVM “en doğru” model mi? Hayır, ve bunu raporda söyleyeceğiz.</b> Makale protokolünde (C3) Scaled Manhattan, SVM’den hafif iyi çıktı; farklar güven aralıkları içinde. Tezimiz “SVM kazandı” olmayacak, “her dedektör zamanla bozuluyor, ama farklı hızda ve SVM’nin skor birleştirmeye en yatkın olduğu görüldü” olacak. Hocanın dediği gibi: olumsuz ama doğru ölçülmüş sonuç değerlidir.</div>

<h3>5.2 SVM nasıl eğitildi?</h3>
<ol>
<li><b>Ölçekleme:</b> Kullanıcının eğitim girişlerinin her özelliği için ortalama çıkarılıp standart sapmaya bölünür (z-skor). <i>Neden?</i> RBF çekirdeği mesafeye duyarlı; saniye cinsinden 1,2 olan DD ile 0,09 olan H birlikte kullanılırsa büyük sayılar hâkim olur.</li>
<li><b>Model:</b> <code>OneClassSVM(kernel="rbf", nu=ν, gamma=γ)</code>; skor olarak karar fonksiyonunun eksi işaretlisi kullanılır (büyük = yabancı).</li>
<li><b>Hiperparametre seçimi:</b> ν ∈ {{0,01; 0,05; 0,1; 0,2; 0,5}} × γ ∈ {{0,003; 0,01; 0,03; 0,1; 0,3}} ızgarası; 10 ayar kişisinde oturum 1–3 ile eğitim, oturum 4 ile doğrulama, hedef ortalama EER. Seçilen: <b>ν = {sp['nu']}, γ = {sp['gamma']}</b> (ayar EER’i ≈ %10,5).</li>
</ol>
<div class="box why"><b class="t">Neden ν ve γ?</b> ν, eğitim örneklerinin en fazla ne kadarının sınır dışında kalabileceğini belirler (küçük ν = geniş, hoşgörülü sınır). γ, sınırın ne kadar “dalgalı” olacağını belirler (büyük γ = ezberlemeye eğilim). Izgara sonuçları ν = 0,01–0,2 aralığında γ = 0,03’te hep ≈ %10,5–10,6 verdi: seçim hassas bir ayara bağlı değil, bu iyi bir işaret (şans eseri bir noktaya oturmadık).</div>

<h2>6. Sonuçlar</h2>
<h3>6.1 Doğrulama testi: makaleyi yeniden üretebiliyor muyuz?</h3>
<p>C3 protokolüyle (makalenin protokolü) kendi kodumuzun sonuçlarını makaledeki sayılarla karşılaştırdık:</p>
{t_rep}
<div class="box why"><b class="t">Ne gördük?</b> Manhattan ve Scaled Manhattan makaleyle birebir (%15,3 ve %9,6), Mahalanobis neredeyse aynı (%11,1 / %11,0). Yani veri hattımız, özellik çıkarımımız, EER hesabımız ve dedektör kodlarımız doğru çalışıyor. SVM’de makaledeki uygulama ayrıntıları farklı olduğundan birebir aynı sayı beklemiyoruz (bizim %11,6, makalenin %10,2’si); fark güven aralığımız içinde. Bu test, “kod hatalı mı?” sorusunu baştan kapatır.</div>

<h3>6.2 Ana karşılaştırma: oturum içi ve oturumlar arası</h3>
{t_main}
<div class="cap">EER değerlerindeki köşeli parantez: kullanıcılar üzerinden %95 bootstrap güven aralığı. FNMR @ FMR: kullanıcı başına eşik (sonradan), kişi ortalaması. n = 41 kullanıcı.</div>
<ul>
<li>Doğrudan okuma: Scaled Manhattan için C2, C1’den <b>yaklaşık 2,7 puan kötü</b> ve güven aralığı sıfırı içermiyor. Mahalanobis’te tersi görülüyor çünkü C2’de 200 örnekle eğitiliyor (kovaryansı kestirmek kolaylaşıyor); bu, eğitim boyutu karışıklığının canlı kanıtı. Bu yüzden asıl cevabı bölüm 6.3’te arıyoruz.</li>
<li>Bütün dedektörler için FMR %1’de FNMR %{min(S[n]['C2_oturumlar_arasi']['fnmr@fmr1%'] for n in N)*100:.0f}–{max(S[n]['C2_oturumlar_arasi']['fnmr@fmr1%'] for n in N)*100:.0f} arasında. Yani sıkı güvenlik ayarında gerçek kullanıcıların çoğu reddedilir. Makale de aynı şeyi söylüyor: tuş vuruşu dinamiği tek başına erişim denetimi için yeterli değil; parolaya <i>ikinci katman</i> olarak anlamlı.</li>
</ul>
{img('det_c2.png','62%')}
<div class="cap">Şekil 2. C2 için DET eğrileri (kullanıcı başına eğrilerin ortalaması; FMR ekseni %0,1’den başlıyor çünkü altı için yeterli yabancı denememiz yok). Sol alta yakın daha iyi. Manhattan belirgin biçimde kötü; diğer üçü birbirine çok yakın.</div>

<h3>6.3 Temiz kanıt: zamanla bozulma</h3>
<p>Eğitim: oturum 1’in ilk 25 girişi. Test: oturum t’nin son 25 girişi. Eğitim ve test boyutu hep aynı, değişen tek şey <b>eğitimden ne kadar sonra</b> test edildiği.</p>
{t_drift}
{img('drift.png','58%')}
<div class="cap">Şekil 3. Ortalama EER, oturum numarasına göre. Oturum 1 aynı oturum (taban), 2–8 daha sonraki günler.</div>
<div class="box why"><b class="t">Ne gördük?</b> Dört dedektörde de hata günler geçtikçe yaklaşık monoton artıyor. SVM: %{pc(S['One-class SVM']['drift_eer'][0])} → %{pc(S['One-class SVM']['drift_eer'][7])}, Scaled Manhattan: %{pc(S['Scaled Manhattan']['drift_eer'][0])} → %{pc(S['Scaled Manhattan']['drift_eer'][7])}, Manhattan: %{pc(S['Manhattan']['drift_eer'][0])} → %{pc(S['Manhattan']['drift_eer'][7])}. Yani projenin sorusuna cevabımız: <b>aynı oturumdaki başarım iyimser; sistem yalnızca ilk günün verisiyle eğitilirse hata göreli olarak yaklaşık %40–90 artıyor (dedektöre göre 1,4–1,9 kat).</b> Dikkat: bu eğrinin güven aralığını henüz hesaplamadık ve oturum 8’de bozulmanın bir kısmı “alışma etkisi”nden gelebilir (insanlar parolayı yazdıkça hızlanıyor, Şekil 1b). Bunları tasarım dokümanında sınırlılık olarak yazacağız.</div>

<h3>6.4 Skor birleştirme (isteğe bağlı kısım, yaptık)</h3>
<p>Bir girişe karar vermek yerine ardışık <b>k</b> girişin anomali skorlarının ortalamasını alıp ona karar veriyoruz (C2 verisi, oturum içinde örtüşmeyen pencereler).</p>
{t_fus}
{img('fusion.png','52%')}
<div class="box why"><b class="t">Neden işe yarıyor?</b> Tek bir giriş gürültülüdür (o an dikkatsiz yazmış olabilirsin). Birkaç girişin ortalaması gürültüyü azaltır; gerçek kullanıcının skorları düşük kalır, yabancınınkiler yüksek kalır. <b>En çok kazanan SVM:</b> %{pc(S['One-class SVM']['fusion']['1']['eer_mean'])} → %{pc(S['One-class SVM']['fusion']['10']['eer_mean'])} (k=10). Bedel: kullanıcı 10 kez yazmak zorunda kalır, bu yüzden gerçek hayatta “oturumda birkaç deneme” senaryosuna uyar; tek seferlik girişe değil.</div>

<h3>6.5 Gerçekçi eşik: eşiği yalnızca eğitim döneminden seçersek?</h3>
<p>EER eşiği test verisine bakarak seçer, gerçek sistemde bu olmaz. Bu yüzden eşiği yalnızca eğitim oturumlarından seçtik: eğitim oturumlarını tek tek dışarıda bırakıp (oturum-bırakmalı çapraz doğrulama) kullanıcının kendi skorlarının %90’lık niceliğini eşik aldık; yani gerçek kullanıcıların %90’ı geçsin istedik. Sonra oturum 5–8’de test ettik:</p>
{t_op}
<div class="box warn"><b class="t">Yorum:</b> Gerçek kullanıcıların yaklaşık %6–9’u reddediliyor (hedeften iyi, eşik biraz gevşek), ama yabancıların %{R['operational']['One-class SVM']['0.9']['fmr']*100:.0f}–{R['operational']['Manhattan']['0.9']['fmr']*100:.0f}’i kabul ediliyor. Yani tek başına bir güvenlik katmanı olarak zayıf; demoda bunu dürüstçe söylemeliyiz (“parola yanlışsa zaten girilemez, ritim ek bir engel”). Bu aynı zamanda demo için eşik seçme yöntemimiz olacak.</div>

<h3>6.6 Kullanıcı farklılığı</h3>
{img('per_user_eer.png','78%')}
<div class="cap">Şekil 4. Kullanıcı başına EER dağılımı (kutu: çeyrekler, çizgi: medyan). Bazı kullanıcılar neredeyse %0, bazıları %40’ın üzerinde.</div>
<p>Dağılım çok geniş: bazı kullanıcıların ritmi çok ayırt edici, bazılarınınki neredeyse yok. Ortalama bunu saklar, o yüzden raporda dağılımı ve en kötü kullanıcıların hata analizini vereceğiz (hocanın “hataları analiz et” şartı).</p>

<h2 class="pb">7. Demo: localhost giriş ekranı</h2>
<p><b>Fikir yapılabilir mi? Evet.</b> Önerdiğin akış, projenin kendi deney tasarımının küçük bir kopyası: oturum 1 = eğitim, sonraki gün oturum 2 = hem test hem gösterilebilir bozulma.</p>
<h3>7.1 Akış</h3>
<ol>
<li><b>Kayıt (Enroll) ekranı:</b> Kullanıcı seçilir (Bahadır / Ömer Efe), “Oturum 1” seçilir, parola 50 kez yazılır. Tarayıcı her giriş için <code>keydown</code> ve <code>keyup</code> zamanlarını (<code>performance.now()</code>) kaydeder; H, DD, UD özellikleri hesaplanır ve kaydedilir.</li>
<li>Bir gün sonra “Oturum 2” aynı şekilde yapılır. Böylece her kullanıcıda CMU’daki yapıya benzer, gün bazında ayrılmış veri oluşur.</li>
<li><b>Eğitim:</b> Kullanıcının kayıt verisiyle ona özel dedektör (One-class SVM, istersek karşılaştırma için Scaled Manhattan) eğitilir; saniyeler sürer. Eşik, bölüm 6.5’teki yöntemle (oturum-bırakmalı) yalnızca kayıt verisinden seçilir.</li>
<li><b>Giriş (Login) ekranı:</b> Kullanıcı adı seçilir, parola yazılır. Sistem parolayı <i>ve</i> yazış ritmini kontrol eder, skoru ve kararı (kabul/ret) gösterir.</li>
<li><b>Saldırı gösterimi:</b> Parola ekranda yazılıdır; başkası (ör. Ömer, Bahadır’ın hesabına) aynı parolayı yazar ve ritmi uymadığı için reddedilir.</li>
</ol>
<h3>7.2 Parola: aynı olsun mu, farklı mı?</h3>
<div class="box why"><b class="t">Önerim: iki kullanıcı için de aynı parola, <code>bahadir23.</code></b>
<ul>
<li><b>Neden aynı?</b> Farklı parolada (<code>bahadir23.</code> ve <code>omerefe123.</code>) birinin hesabına başka parolayla girmek zaten parola yanlış olduğu için reddedilir; ritim hiç test edilmez. Aynı parolada tek ayırt edici şey yazış ritmidir, projenin iddiası tam olarak bunu gösterir. Üstelik CMU verisi de “herkes aynı parolayı yazar” tasarımıyla toplanmış.</li>
<li><b>Güzel bir tesadüf:</b> <code>bahadir23.</code> 10 karakter + Enter = 11 tuş, yani CMU’nun <code>.tie5Roanl</code> parolasıyla aynı yapıda: 11 H + 10 DD + 10 UD = <b>31 özellik</b>. Bu yüzden özellik çıkarım kodunu ve CMU’da seçtiğimiz hiperparametreleri (ν={sp['nu']}, γ={sp['gamma']}) hiç değiştirmeden kullanabiliriz. <code>omerefe123.</code> 11 karakter + Enter = 12 tuş = 34 özellik olurdu; teknik olarak mümkün ama ekstra uyarlama gerekir.</li>
<li>İstersen <code>omerefe123.</code> ile ek bir “farklı parola” senaryosu da gösterebiliriz, ama ana demo ortak parolayla olsun.</li>
</ul></div>
<h3>7.3 “Modeli önceden eğitelim” ne demek?</h3>
<p>CMU’da eğitilen model demodaki kullanıcılara <b>uygulanamaz</b>: dedektörler kişiye özel; Bahadır’ın ritmi CMU’da yok. Önceden hazır olan şey <b>hattın kendisi</b>: özellik çıkarımı, doğrulanmış dedektör kodu, CMU’da seçilmiş ν ve γ, eşik seçme yöntemi. Kişisel modeller kayıt bittiğinde saniyeler içinde eğitilir. (İkinci geliştirmedeki paylaşımlı gömü ağı ise CMU’da önceden eğitilebilir, bölüm 8.)</p>
<h3>7.4 Sınırlar ve riskler</h3>
<ul>
<li><b>Zamanlama farkı:</b> CMU verisi harici bir saatle toplandı; tarayıcı olay zamanları (klavye, işletim sistemi, tarayıcı) farklı gecikme taşır. Demo verisi bu yüzden CMU’yla karıştırılmaz ve doğruluk iddiası için kullanılmaz; demo sadece hattın çalıştığını gösterir.</li>
<li><b>Veri azlığı:</b> İki kullanıcı × birkaç oturum çok az; demodaki ret/kabul oranı istatistiksel kanıt değil. Raporda bunu açıkça yazacağız; ciddi sayılar CMU deneylerinden gelir.</li>
<li><b>Hoca onayı:</b> Proje metni “kendi biyometrik verini toplamak için hocanın önceden onayı gerekir” diyor. Demo verisi yalnızca ikimizden toplanacak olsa da, veriyi toplamadan önce hocaya kısa bir e-posta ile sormalıyız. Onay gelene kadar demoyu CMU’dan seçilmiş bir kişinin verisiyle simüle edecek şekilde de hazırlayabiliriz.</li>
<li><b>Başarı garantisi yok:</b> Biz de dahil, bazı insanların ritmi tutarsızdır (Şekil 4). Demoda Bahadır reddedilirse bunu sistemin sınırı olarak anlatırız; ama önceden denemek şart.</li>
</ul>
<h3>7.5 Teknik taslak</h3>
<p>Tarayıcıda küçük bir JavaScript (<code>keydown/keyup</code> yakalama), arkada Python <b>Flask</b> sunucusu (zaten kurulu), veriler SQLite veya JSON dosyasında. Dedektör kodu doğrudan <code>keystroke/detectors.py</code>’den yüklenir; yani demo ile deneyler aynı kodu paylaşır.</p>

<h2>8. İkinci geliştirme: paylaşımlı gömü ağı (isteğe bağlı)</h2>
<p>Önceliğimiz SVM; bunu hocaya “ek geliştirme” olarak sunacağız. Fikir: tek bir küçük sinir ağını (Siamese/üçlü kayıpla) birçok kişinin verisiyle eğitip her girişi bir “ritim vektörüne” çevirmek; sonra kullanıcı kaydı = birkaç vektörün ortalaması, doğrulama = vektör mesafesi.</p>
<div class="box warn"><b class="t">Hocanın kuralı:</b> “Kullanıcılar arasında paylaşılan öğrenen model, değerlendirmede kullanılmayan kullanıcılarla eğitilmelidir.” Çözüm: kişileri 5 gruba bölüp her grubu, <i>o grubu hiç görmemiş</i> ağla değerlendirmek (çapraz katlama). Böylece bütün 51 kişiyi dürüstçe değerlendirebiliriz. Bu daha fazla iş ve süre alacağı için SVM sonuçları oturduktan sonra yapacağız; yetişmezse “gelecek çalışma” olarak yazarız.</div>

<h2>9. Hocanın kurallarına karşı kontrol listesi</h2>
{tbl(["Kural","Durum"],[
["Kendi uyguladığımız en az bir aşama","Tamam: 4 dedektör, metrikler ve deneyler kendi kodumuz"],
["Açık kaynak parçaların beyanı","scikit-learn (OneClassSVM çekirdeği), numpy, pandas, matplotlib, Flask beyan edilecek"],
["Eğitim/test kişi ve zaman ayrımı","Tamam: zamana göre bölme + ayrık ayar grubu"],
["Eşiğin hangi veride seçildiğini yazmak","Tamam: EER = test skorlarından (makale gibi), gerçekçi eşik = yalnızca eğitim dönemi"],
["Desteklenen düzeyde hata oranı","FMR en fazla %0,1’e kadar"],
["Belirsizlik (denek bootstrap)","Tamam; zamanla bozulma eğrisi için eksik, eklenecek"],
["Hata analizi, makaleyle karşılaştırma","Karşılaştırma tamam; en kötü kullanıcıların analizi eksik"],
["En az 10 kaynak, hepsi gerçek ve doğrulanmış","Henüz yok. Yapay zekâ kaynak uydurabilir; her kaynağı arayıp doğrulayacağız ve yalnızca bulduklarımızı yazacağız."],
["AI Use Declaration (tasarım dokümanı ve raporun sonunda)","Yazılacak: hangi araç, hangi iş, nasıl denetlendi"],
["Kendi veri toplama onayı","Hocaya sorulacak (bölüm 7.4)"],
["Kod ZIP: README, requirements, sonuçları yeniden üreten betik","<code>requirements.txt</code> ve <code>run_all.py</code> hazır; README sonra"]])}

<h2>10. Yol haritası</h2>
{tbl(["Tarih","Ne","Durum"],[
["Hemen","Hocaya demo verisi için onay e-postası","Bekliyor"],
["30 Ekim","<b>Tasarım dokümanı</b> (2–3 sayfa PDF): literatür, şema, veri/lisans, bölme kuralı, metrikler, araçlar, AI beyanı","Sıradaki iş; 10 kaynak taraması ve doğrulama"],
["9 Kasım haftası","Veri ve ön işleme sunumu (5 dk): veri istatistikleri, kalite sorunları, reddedilen örnek","İçerik büyük oranda hazır (bölüm 3)"],
["27 Kasım","İlk sonuçlar: skor dağılımları ve DET","Şimdiden var; skor dağılım grafiği eklenecek"],
["Kasım","Demo uygulaması (kayıt, eğitim, giriş), ikinci geliştirme","Başlanmadı"],
["7 Aralık haftası","Final sunum ve demo (10 dk + 5 dk soru)","—"],
["11 Aralık","Rapor (10–15 sayfa) ve kod ZIP","—"]])}
<p><b>Sonraki adımım için öneri:</b> (1) Tasarım dokümanını birlikte yazmaya başlamak; önce kaynak taraması, sonra 2–3 sayfalık PDF. (2) Paralelde demo uygulamasının iskeletini kurmak.</p>

<h2>Sözlük</h2>
{tbl(["Terim","Anlamı"],[
["Genuine / gerçek kullanıcı","Kendi hesabına giren kişi"],["Impostor / yabancı","Başkasının hesabına girmeye çalışan kişi"],
["Anomali skoru","Girişin kullanıcının normalinden ne kadar uzak olduğu"],["Oturum","Bir günde yapılan 50 giriş"],
["Bootstrap","Veriyi yerine koyarak yeniden örnekleyip belirsizliği ölçme yöntemi"],["Hiperparametre","Öğrenmeden önce elle seçilen ayar (SVM’de ν ve γ)"],
["Sızıntı","Test bilgisinin yanlışlıkla eğitime karışması, sonucu olduğundan iyi gösterir"]])}
<p style="font-size:9pt;color:#55607a;margin-top:18px">Kaynaklar (bu belgede kullanılanlar): K. S. Killourhy ve R. A. Maxion, “Comparing Anomaly-Detection Algorithms for Keystroke Dynamics”, DSN 2009 (proje klasöründeki PDF’ten okundu); hocanın “Biometric Recognition Project” ve “Project Topics” belgeleri (30 Eylül 2026). Bu belgedeki bütün sayılar <code>results/results.json</code> dosyasından otomatik üretilmiştir. Belgenin hazırlanmasında Claude (Anthropic) kod yazma ve metin taslağı için kullanıldı; sonuçlar makale değerleriyle yeniden üretilerek denetlendi.</p>
</body></html>"""

out_html = os.path.join(HERE, "okuma_kilavuzu.html")
open(out_html, "w", encoding="utf-8").write(HTML)
pdf = os.path.join(HERE, "..", "..", "A5_Okuma_Kilavuzu.pdf")
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless=new", "--disable-gpu",
                "--no-pdf-header-footer", f"--print-to-pdf={pdf}", "file://" + out_html], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("PDF:", os.path.abspath(pdf))
