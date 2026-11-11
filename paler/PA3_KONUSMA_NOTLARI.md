# PA3 Checkpoint – 5 dakikalık konuşma notları (9 slayt, ~30 sn/slayt)
Yüklenecek: `PA3_Checkpoint_Slides_221101034_221101059.pdf` · Teslim: 9 Kasım 2026 · uzak.etu.edu.tr · 4 puan
Yeniden üretmek: `cd proje && .venv/bin/python checkpoint.py` → `cd ../paler/src && python3 build_checkpoint_slides.py`

1. **Başlık** – Konu A5, CMU verisi elimizde. Hocanın istediği 4 başlığı sırayla anlatacağız.
2. **İstatistikler** – 51 kişi × 8 oturum × 50 tekrar = 20.400 giriş, 31 özellik (11 H, 10 DD, 10 UD). Medyan yazma süresi 2,30 sn; kişiler arası 1,41–4,93 sn (3,5 kat). Oturum 1 → 8 hızlanma (2,80 → 2,08 sn), 51 kişiden 49'u hızlanmış. 10 ayar kişisi (gri) / 41 değerlendirme kişisi.
3. **Ön işleme hattı** – Yükle → doğrula → diziye çevir → yalnızca eğitimde ret → kullanıcıya özgü normalizasyon. 8 kontrolün hepsi geçti. Görüntüdeki gibi "tespit başarısız" adımı yok: CMU yazılımı yanlış yazılan parolayı kaydetmiyor, kişiye tekrar yazdırıyor. Test verisi asla filtrelenmiyor.
4. **Bir giriş → 31 boyutlu vektör** – H = bırakma − basma; DD = sonraki basma − bu basma; UD = DD − H. a→n'de UD negatif: n'ye a bırakılmadan basılmış.
5. **Bir kullanıcının şablonu** – Ham özellikler farklı büyüklükte (90 ms ile 600+ ms), bu yüzden düz Manhattan birkaç uzun aralığa boğuluyor. z-skor sonrası her özellik eşit ağırlıkta. Soldaki ilk girişler daha yavaş: oturumlar arası kayma.
6. **Kalite sorunları** – UD değerlerinin %10,8'i negatif (tuş çakışması, gerçek davranış, tutuluyor). 189 girişte 2 sn'den uzun duraksama var, en uzun giriş 36 sn. Pratik etkisi var. DD = H + UD olduğu için kovaryansın rangı 21 → Mahalanobis'e ridge ekliyoruz. Laboratuvar koşulları ile demo farklı. 5 ID eksik (veri böyle yayımlanmış).
7. **Reddedilen örnekler** – Kural: kayıt girişinin toplam süresi > 2 × kullanıcının kendi kayıt medyanı ise at. k=2 ile C2'de 8200 girişten 77'si (%0,9), 41 kişiden 25'i etkileniyor; çoğu oturum 1'de. Örnek: s049, 36 sn (i→e arası 26 sn duraksama).
8. **Etkisi** – EER sadece 0,1–0,25 puan düşüyor, 4 dedektörün 3'ünde fark istatistiksel olarak anlamlı değil. Asıl hata kaynağı oturumlar arası kayma. Karar: ana sonuçlar tüm verilerle (makaleyle karşılaştırılabilir olsun diye), ret ise ayrı bir varyant olarak raporlanacak.
9. **Sonraki adımlar** – 27 Kasım: C1 ve C2 için DET/EER, kişi başı EER, güven aralıkları, kayma eğrisi. Sonra skor birleştirme, isteğe bağlı Siamese, demo. Hocaya soru: demo verisi onayı.

**Olası sorular:** Neden test verisini filtrelemiyorsunuz? (Test verisine bakarak karar vermek sızıntı olur.) k=2 nereden geliyor? (Basit, açıklanabilir bir değer. 1,5 ve 3 için de sayıları gösterdik; EER etkisi küçük.) Negatif UD bir hata mı? (Hayır, çakışan tuş basımı; zaten DD = H + UD özdeşliği tutuyor.)
