# Final sunum – 10 dakikalık konuşma notları (14 slayt) + demo planı
Yüklenecek: `Final_Slides_221101034_221101059.pdf` · Teslim: 7 Aralık 2026 · 6 puan · 10 dk sunum + 5 dk soru
Yeniden üretmek: `cd proje && .venv/bin/python reproduce.py` → `cd ../paler/src && python3 build_final_slides.py`

**Önerilen bölüşüm:** Bahadır 1–6 (problem, protokol, sistem, replikasyon, ana sonuç) · Ömer 7–10 (öğrenen modeller, yaşlanma, füzyon, hata analizi) · Bahadır 11–12 demo (Ömer sahtekâr rolünde) · Ömer 13–14.

1. **Başlık (15 sn)** – Konu A5, CMU verisi, sonda canlı demo.
2. **Problem (40 sn)** – Parola çalınabilir ama yazma ritmi zor kopyalanır. Herkes aynı parolayı yazıyor; kişiye özel dedektör kabul/ret veriyor. Ritim günden güne kayıyor → oturum-içi sonuçlar iyimser olabilir. Soru bu.
3. **Veri ve protokol (60 sn)** – 51 kişi × 8 oturum × 50 giriş, 31 özellik. 10 ayar kişisi / 41 değerlendirme kişisi: hiçbir şey değerlendirme kişilerinde ayarlanmadı. C1 oturum içi, C2 oturumlar arası (asıl koşul), yaşlanma eğrisi, C3 makale protokolü. Kişi başı 8000 sahtekâr skoru → en düşük FMR %0,1. Güven aralığı denekleri yeniden örnekleyerek.
4. **Sistem (50 sn)** – Tuş olayları → 31 özellik → kayıt → dedektör → füzyon → karar. 5 dedektör. Siamese ortak model olduğu için kural: değerlendirilen kişiler ve test sahtekârları eğitimde yok → 5 katlı çapraz uydurma.
5. **Replikasyon (40 sn)** – Mesafe dedektörleri makaleyle 0,1 puan içinde aynı → kodumuz doğru. SVM 1,4 puan kötü ama makale değeri GA içinde. Ama C3 sahtekârları ilk, pratiksiz girişleriyle test ediyor; bizim C1/C2 daha zor.
6. **Ana sonuç (70 sn)** – C2'de en iyi tekli dedektörler ~%14–15, istatistiksel olarak berabere. Düz Manhattan çok kötü (%22). DET eğrisi asıl eğri. Füzyon %12,7, 5 giriş ortalamasıyla %7,1.
7. **Öğrenen modeller (60 sn)** – Siamese oturum içinde en iyi (%10,6) ama oturumlar arası en çok kaybeden (+5,1 puan, GA 0'ı içermiyor). Scaled Manhattan 8 kat fazla veriyle bile kaybediyor → kayma. Mahalanobis C1'de kovaryans tahmini yüzünden kötü. Skor dağılımı: gerçek kullanıcı skorları sağa kayıyor.
8. **Yaşlanma ve eşik (50 sn)** – Kayıt 25 girişe sabitken hata oturumla artıyor (%12,9 → %24,1). Eşiği yalnız kayıt verisinden seçince (%95'lik) sonraki oturumlarda FMR %55,6 → gerçek sistem şablon güncellemeli.
9. **Ne işe yarıyor (40 sn)** – Dedektör füzyonu sınırlı (aynı kullanıcılarda hata yapıyorlar, ρ=0,97). Çoklu giriş füzyonu ve çok oturumlu kayıt en etkili. Pratik: sınırda kalınca bir giriş daha iste (step-up).
10. **Hata analizi (50 sn)** – 5 kötü kullanıcı toplam hatanın %28'i ("goat"). Bazı sahtekârlar "wolf" (s026 %52). Tutma süreleri en çok kayan özellik, en büyük kayma e→5 geçişinde. Kayma miktarı ile kişi EER'i arasında anlamlı ilişki yok (ρ=0,24, p=0,13).
11. **Demo mimarisi (40 sn)** – Flask+SQLite, aynı özellik kodu (CMU satırları tuş olayı olarak tekrar oynatılınca birebir aynı vektör). Parola yalnızca scrypt özeti; şablon sadece süre sayıları; silinebilir. Demo verisi değerlendirmede kullanılmıyor.
12. **Canlı demo (~2 dk)** – (1) Bahadır kendi hesabıyla giriş → kabul; (2) Ömer "impostor test" ile Bahadır'ın parolasını yazar → çoğunlukla ret; (3) k=3; (4) Demo log sayfası. Ret olursa: "bu tam olarak FNMR, raporda ölçtüğümüz şey" de.
13. **Sınırlılıklar ve sonuç (40 sn)** – Son cümle: tuş ritmi ucuz ve faydalı bir **ikinci faktör**, tek başına kimlik doğrulayıcı değil.
14. **Teşekkür / sorular.**

## Demo öncesi kontrol listesi
- [ ] Demo verisi: verisini paylaşmayı kabul eden gönüllü katılımcılar (kayıtta rıza kutusu). Sunuma kadar katılımcılardan kayıt + hesap sahibi/sahtekâr denemeleri toplayın (her hesap ≥ 15 giriş, tercihen 2 farklı gün, aynı laptop ve klavye).
- [ ] Sonuçlar yalnızca sitede: **Demo kayıtları** (tek tek denemeler) ve **Demo analizi** (FMR/FNMR, skor payı histogramı, FMR–FNMR eğrisi, havuzlanmış EER, katılımcı bazında tablo, zaman çizelgesi). Raporda demo sonucu yok.
- [ ] Sunum günü aynı laptopu kullanın; eşik ayarı "balanced".
- [ ] Yedek: demo çalışmazsa slayt 11'deki ekran görüntüsünü gösterin.

## Olası sorular
- **Neden Siamese oturumlar arası kötü?** Eğitimde ~43 kişi var, oturumlar arası değişim zayıf temsil ediliyor; şablon tek bir merkez. Oturumlar arası pozitif çiftlerle eğitmek/şablon güncellemek gelecek iş.
- **Neden fold protokolü?** Siamese diğer kişileri negatif olarak görüyor; görülen sahtekârları testte kullanmak kural ihlali olurdu. Tüm dedektörleri aynı veride karşılaştırmak için hepsi bu protokolde de çalıştırıldı (fark < 0,2 puan).
- **EER eşiği nerede seçildi?** EER eşiksiz özet ölçüt; işletim noktası eşiği yalnız kayıt verisinden (oturum-bırakmalı) seçildi.
- **Neden FMR %0,1'in altı yok?** Kişi başı 8000 sahtekâr skoru; daha altı desteklenmiyor.
- **Sasikumar %1 EER diyor?** k-katlı çapraz doğrulama, oturumlar karışık, sahtekâr verisiyle eğitim → bizimle karşılaştırılamaz.
- **Kendi verinizi topladınız mı?** Evet, sadece demo için ve hocadan önceden onay alarak: verisini paylaşmayı kabul eden gönüllü katılımcılardan (rıza kutusu, istenince silinebilir, yerelde). Bu veriler sitedeki "Demo analizi" sayfasında analiz ediliyor; rapordaki değerlendirme yalnızca CMU verisiyle, ikisi karıştırılmıyor (tarayıcı zamanlaması, beyana dayalı roller).
