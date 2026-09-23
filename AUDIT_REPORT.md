# MOQ Lab v0.4.2 — Denetim raporu

Tarih: 21 Eylül 2026. Kaynak: kullanıcının MOQ-Lab-v0.4.zip dosyasının mevcut v3 içeriği; uygulama sürümü 0.4.0. Denetlenen çıktı sürümü 0.4.1.

## Yönetici özeti

Başlangıçta 30/30 test geçiyordu. Buna rağmen modelin dengeli eşitlik kuralı, solver durumlarının yorumlanması, sessiz para yuvarlama, tablo tam sayı dönüşümü, dil/state davranışı, karşılaştırmalar ve CSV güvenliği yetersizdi. Bu rapordaki 13 bulgu düzeltilmiştir: **P0: 1, P1: 5, P2: 6, P3: 1**.

**Tam teslim onayı verilmedi; ZIP oluşturulmadı.** Linux Python 3.11 ve 3.12 kurulum/test akışları, AppTest etkileşimleri ve gerçek HTTP başlangıcı doğrulandı. Windows/PowerShell komutları native Windows üzerinde çalıştırılamadı. Uzak tarayıcı yerel uygulamaya erişimi `ERR_BLOCKED_BY_CLIENT` ile reddetti; gerçek görsel/dar ekran QA yapılmış sayılmadı. Kullanıcının “kurulum komutlarını gerçekten çalıştırmadan doğru kabul etme” ve eksik kalite kapısında ZIP vermeme koşulları gereği kaynaklar bir **denetim çalışma çıktısı** olarak korunmuştur. ZIP yerine başka bir arşiv biçimiyle bu kapı aşılmamıştır.

Commit/push yapılmadı. Girdi ZIP'i değiştirilmedi. Dağıtım arşivi SHA-256 değeri yoktur. Kaynak dosyaların ayrı SHA-256 değerleri `SOURCE_SHA256SUMS.txt` içindedir.

## Bulunan sorunlar

Her kayıtta yeniden üretim, beklenen/gerçek davranış, kök neden, düzeltme ve regresyon kanıtı yer alır. P0 güvenlik/veri kaybı; P1 önemli yanlış karar; P2 yanıltıcı açıklama veya önemli state/UX; P3 düşük etkili dokümantasyon eksikliği anlamında kullanıldı.

### A01 — P0 — CSV formula injection

- Yeniden üretim: şirket adını `=1+1`, `+SUM(A1)`, `-1+1` veya `@SUM(A1)` yapıp CSV dışa aktarın.
- Beklenen: kullanıcı metni hücre formülü olarak yorumlanmamalı. Gerçek: ham ad doğrudan CSV'ye yazılıyordu; yalnızca CSV tırnaklama formül yorumunu engellemez. Excel'de zararlı formül çalıştırılmadı; risk dışa aktarılan baytlarda doğrulandı.
- Kök neden: `DataFrame.to_csv` öncesi metin güvenliği uygulanmaması.
- Düzeltme: tehlikeli başlangıçlar ve ön kontrol karakterleri için yalnızca dışa aktarmada apostrof; UTF-8 BOM ve yerel ayırıcılar korunuyor. Markdown ve grafikte HTML benzeri adlar ayrıca literal metin olarak ele alınıyor.
- Test: `test_csv_preserves_data_with_safe_text_and_exact_totals`, `test_markdown_is_literal_and_formula_prefix_is_preserved_only_in_export`.
- Durum: kod/bayt testlerinde düzeltildi; gerçek Excel sürümlerindeki görsel davranış çalıştırılmadı.

### A02 — P1 — Dengeli politikanın yanlış eşitlik hedefi

- Yeniden üretim: talep 1; teklif A MOQ 2/fiyat 1/süre 0; teklif B MOQ 1/fiyat 4/süre 1; fazla stok cezası 3, günlük değer 1. Her iki karar skoru 5.
- Beklenen: nakit 2 olan A. Gerçek v0.4: nakit 4 olan B seçildi; bu çıktı başlangıç kaynaklarında ayrıca çalıştırılarak görüldü.
- Kök neden: ikinci hedefin nakit yerine `nakit + stok cezası` olması.
- Düzeltme: Dengeli ikinci hedefi yalnızca gerçek nakit maliyeti. Birinci hedef tamsayı eşitliğiyle sabit.
- Test: `test_balanced_cash_tiebreak_distinct_from_base_cost`, üç politikada bağımsız enumerasyon.
- Durum: düzeltildi.

### A03 — P1 — Solver durumları ve sahte kesinlik

- Yeniden üretim: birinci solver dönüşünü UNKNOWN/MODEL_INVALID yapın ve bütçeyi açık tutun; ayrıca birinci OPTIMAL, ikinci UNKNOWN akışını uygulayın.
- Beklenen: zaman aşımı/model hatası ayrı olmalı; ikinci hedef kanıtlanmadan tam optimum iddiası olmamalı. Gerçek: başarısızlıklar bütçe yetersizliğine yönleniyordu; ikinci aşama UNKNOWN olduğunda ilk OPTIMAL etiketi korunabiliyordu.
- Kök neden: tüm başarısız durumların tek dalda işlenmesi ve son aşama statüsünün güncellenmemesi.
- Düzeltme: OPTIMAL/FEASIBLE/INFEASIBLE/UNKNOWN/MODEL_INVALID ayrı; iki aşamanın statüsü ve amaç değeri sonuçta tutuluyor. Minimum bütçe ancak birincil nakit optimumu kanıtlanırsa kesin veriliyor. Tutarsız tanı güvenli hataya dönüşüyor. UNKNOWN hatası cache'e kilitlenmiyor; kullanıcı tekrar deneyebiliyor.
- Test: `test_solver_failure_never_fabricates_budget_reason`, `test_incomplete_lexicographic_proof_is_only_feasible`, `test_unproven_minimum_is_not_reported_as_exact`, `test_actual_tiny_time_limit_has_honest_unknown_status`, UI solver hata/FEASIBLE/yeniden deneme testleri.
- Durum: düzeltildi. Nadir durum dalları kontrollü statü enjeksiyonuyla, UNKNOWN ayrıca gerçek 1 mikro saniye solver bütçesiyle test edildi.

### A04 — P1 — Sessiz para yuvarlama ve geçersiz küçük negatifler

- Yeniden üretim: birim fiyatı `1.005`, `1.015`, `-0.001` yapın.
- Beklenen: hassasiyet açıkça doğrulanmalı; negatif değer kabul edilmemeli. Gerçek v0.4 çalıştırması sırasıyla `1.01`, `1.02`, `0.00` döndürdü; kullanıcıya dönüşüm bildirilmiyordu.
- Kök neden: doğrulamadan önce quantize.
- Düzeltme: finite Decimal doğrulaması, açık iki ondalık hassasiyet reddi, negatif girdinin korunarak reddedilmesi. Türetilmiş ortalamalar HALF_UP.
- Test: fiyat, NaN/Infinity, negatif, hassasiyet, tam bütçe/bir kuruş altı parametrik testleri.
- Durum: düzeltildi. Sessiz yuvarlama yerine kullanıcı düzeltmesi gerektiren iş kuralı README/UI'da açıklandı.

### A05 — P1 — Tablo adet/gün değerlerinde sessiz kırpma

- Yeniden üretim: tablo verisine MOQ veya teslim süresi `1.5` gönderin; zorunlu alanı boş bırakın.
- Beklenen: kesirli/missing girdi reddedilmeli. Gerçek: `int(...)` kesirli değeri 1'e çevirebiliyor, eksik ad `nan` metnine dönüşebiliyordu.
- Kök neden: doğrulamadan önce int/str dönüşümü.
- Düzeltme: ortak saf tablo parser'ı, sonlu tam sayı kontrolü, gerçek boş ad denetimi, tamamen boş/kısmi satır ayrımı.
- Test: `test_table_rejects_partial_fractional_text_and_missing_fields`, gerçek editor delta ekleme/silme/boş/kesir akışı.
- Durum: düzeltildi.

### A06 — P1 — Sayısal sınırlar ve sonuç doğrulaması eksikliği

- Yeniden üretim: çok yüksek fiyat × miktar × teklif sayısı veya modele aykırı sonuç toplamı üretin.
- Beklenen: overflow önlenmeli, hatalı sonuç yayınlanmamalı. Gerçek: açık birleşik katsayı sınırı ve sonuç/amaç bütünlüğü kapısı yoktu.
- Kök neden: yalnızca işaret kontrolleri ve solver çıktısına doğrudan güven.
- Düzeltme: alan sınırları, 2^60 kuruş maliyet üst sınırı, güvenli değişken üst sınırları, seçilme için en az 1 adet, tam max-equality süre ve bağımsız sonuç doğrulayıcısı.
- Test: büyük miktar/fiyat/kapasite/süre/sayı sınırları; `test_overflow_guard`; altı sonuç bozma vakası; float kesinliğini aşan ama geçerli maliyet testi.
- Durum: düzeltildi.

### A07 — P2 — Dil değişiminde girdilerin korunmaması

- Yeniden üretim: EN'de tabloyu ve talebi değiştirin; TR'ye geçin.
- Beklenen: aynı iş problemi korunmalı. Gerçek: dile özel editor/currency key'leri ve görünür metne bağlı widget kimlikleri başka tablo/varsayılan değerler açabiliyordu.
- Kök neden: dil başına veri tabanı gibi kullanılan widget state'i.
- Düzeltme: tek kanonik teklif tablosu, kalıcı teklif kimliği, kararlı ayar key'leri, editor delta callback'i, açık örnek yükleme düğmesi. Dil değişimi kullanıcı adını çevirmiyor veya değiştirmiyor.
- Test: iki yönlü EN/TR düzenlenmiş tablo+ayar+sonuç akışları; ekleme/silme kimlik koruması.
- Durum: AppTest ile düzeltildi. V0.4'ün ayrı örnek state'i bekleyen testi, yeni açık kabul kriterlerine göre güncellendi; silinmedi veya atlanmadı.

### A08 — P2 — Sonucun yalnızca düğme basımında görünmesi

- Yeniden üretim: optimize edin, dil veya başka rerun tetikleyen kontrolü değiştirin.
- Beklenen: geçerli sonuç dilde yeniden çizilmeli; problem değişince eski sonuç temizlenmeli. Gerçek: bütün sonuç ağacı düğmenin geçici boolean değeri altındaydı.
- Kök neden: kalıcı sonuç/snapshot kimliği olmaması.
- Düzeltme: hesaplama girdisi fingerprint'i ile sonuç/hata state'i; dil değişiminde yeniden render; etkin veri değişiminde temizleme ve mesaj.
- Test: sekiz farklı girdi değişikliği, beş ardışık optimizasyon, geçerli→hatalı→geçerli ve kalıcı çevirilen hata.
- Durum: AppTest ile düzeltildi. Tam tarayıcı yenilemesi yeni oturumdur; kalıcı proje kaydı vaat edilmez.

### A09 — P2 — Aynı adlı tekliflerin reddi ve açıklama kimliği

- Yeniden üretim: aynı şirket adına iki bağımsız teklif girin.
- Beklenen: satırlar ayrı tutulmalı. Gerçek: ad benzersizliği zorunluydu; açıklama motoru adlardan seçilme kümesi oluşturuyordu.
- Kök neden: iş etiketi ile kimliğin karışması.
- Düzeltme: ayrı row_id, sonuç/insights kimlik eşlemesi, aynı adlı grafik etiketlerinin ayırt edilmesi. UI satır ekleme/silme sırasında kimlikleri korur; doğrudan API kimlik verilmezse snapshot sırasından üretir.
- Test: iki aynı adlı teklifin birlikte seçilmesi, nakliyenin teklif başına tek sayılması, bağımsız random senaryolar ve editor kimlik akışı.
- Durum: düzeltildi. Aynı şirketin alternatif fiyat tekliflerini birbirini dışlayan seçenekler olarak modellemek kapsam dışıdır.

### A10 — P2 — Deadline karşılaştırmasında politika değişmesi

- Yeniden üretim: Dengeli veya Acil modda teslim sınırıyla optimize edin.
- Beklenen: karşılaştırmada yalnızca teslim sınırı kalkmalı. Gerçek: referans her zaman Ekonomik çözülüyor ve günlük zaman değeri iletilmiyordu; negatif maliyet farkı sıfırlanıyordu.
- Kök neden: karşılaştırma çağrısındaki hard-coded politika ve farkı clamp etme.
- Düzeltme: bütün diğer parametreler aynen korunuyor; negatif fark tasarruf; çözüm doğrulanamıyorsa açık bilgi. Kesin fark iddiası yalnızca iki optimum planla.
- Test: parametreleri gözlemleyen UI regresyonu, 1.700 adet/5.200 gün örneği, FEASIBLE karşılaştırma UI testi.
- Durum: düzeltildi.

### A11 — P2 — What-if noktalarının gizlenmesi ve gereksiz tekrar hesaplama

- Yeniden üretim: talep senaryolarının bir kısmı kapasite/bütçe dışında kalsın; sonuç ekranını yeniden çalıştırın.
- Beklenen: başarısız noktalar açıklanmalı, grafikte aradan çizgi çekilmemeli. Gerçek: exception sonrası continue ile kayboluyordu; her sonuçta çok sayıda solver çağrısı tekrar yapılıyordu.
- Kök neden: yalnızca başarılı noktaları saklama, açık tetik/önbellek olmaması.
- Düzeltme: isteğe bağlı analiz, en fazla 12 nokta, tam girdi bazlı sınırlı cache, null boşluklar, lokal hata/FEASIBLE açıklaması ve politika etiketi. UNKNOWN gibi geçici solver hataları tekrar denemeyi engelleyecek biçimde cache'lenmez.
- Test: gap/hover/dil UI testi, cache çağrı sayacı, 1/10/50/100 performans smoke.
- Durum: düzeltildi.

### A12 — P2 — Çıktıda para kesinliği ve eksik plan bağlamı

- Yeniden üretim: yüksek fakat geçerli fiyat × miktar, ardından sonuç tablosu/CSV; normal CSV'de politika ve talep bağlamını arayın.
- Beklenen: kuruşlar ve plan bağlamı korunmalı. Gerçek: sonuçlar önce float'a çevriliyor, CSV yalnızca satır tablosunu içeriyordu.
- Kök neden: gösterim DataFrame'inin aynı zamanda veri aktarım kaynağı olması.
- Düzeltme: Decimal'dan yerel tutar metni, tam hover tutarı, bağımsız CSV serializer; politika/talep/fazla alım/statü/kısıt alanları. Küçük paylar sıfır gibi gösterilmez; yüzdelerin yuvarlanma kuralı açıklanır.
- Test: EN/TR özel karakter/formül örnekleri; `test_large_totals_table_and_hover_keep_exact_cents`; `test_large_valid_money_preserves_cents_beyond_float_precision`.
- Durum: byte ve AppTest semantiğinde düzeltildi; gerçek Excel ve dar ekran görsel incelemesi açık.

### A13 — P3 — Dokümantasyon ve kurulum kapsamı

- Yeniden üretim: README'de sıfırların iş anlamını, hassasiyet reddini, aynı şirket tekliflerini, döviz etiketi davranışını, state yenilemeyi arayın.
- Beklenen: gerçek iş varsayımları açık olmalı. Gerçek: bu noktalar eksik, dengeli eşitlik ve örnek veri davranışı yeni istekle uyumsuzdu.
- Kök neden: README'nin sınırlı v0.4 davranışını anlatması.
- Düzeltme: alan tablosu, tüm politikalar, kapsam dışı unsurlar, kesinlik/statü, örnek, Windows doğrudan yorumlayıcı komutları, test/benchmark komutları ve sorun giderme.
- Test: Linux kurulum/test/HTTP başlangıç komutları çalıştırıldı; README örneği regresyonlarla eşleşiyor.
- Durum: içerik güncellendi; Windows komutlarının çalıştırılması teslim kapısı olarak açık.

## Matematiksel doğrulama

Bağımsız referans `tests/test_reference.py` içinde; optimizer yardımcılarını veya CP-SAT modelini kullanmaz. Her aday miktar vektörü `itertools.product` ile sayılır; kısıtlar, nakit maliyet, fazla stok cezası ve politika hedef çifti doğrudan hesaplanır.

- Seed: **29481**.
- **120 farklı küçük senaryo × 3 politika = 360** bağımsız optimum/uygulanamazlık karşılaştırması.
- 1–5 teklif, sıfır MOQ/fiyat/nakliye/süre/kapasite, aynı adlar, sınırlı/sınırsız kapasite, bütçe ve deadline açık/kapalı, stok ve zaman cezası dahil.
- Çoklu optimumda aynı dağılım zorunlu tutulmaz; iki hedef değeri ve bütün kısıtlar karşılaştırılır. Her seçilen satırın kimliği, ürün ve nakliye hesabı doğrulanır.
- Ayrıca **15 seed** ile bütçe/deadline gevşetme, tekrar çözüm amaç tutarlılığı kontrolleri.
- Sonuç doğrulayıcısı; satır/miktar/ürün/nakliye/toplam/fazla alım/süre/bütçe/deadline/MOQ/kapasite/amaç çiftini tekrar hesaplar. Bozulmuş sonuçlar güvenli hatayla kesilir.
- 1.700 referansı: sınır yokken 500 Anadolu+1.200 Marmara, 1.835 ve 5.200 gün; 30 gün sınırında 1.200 Marmara+500 Ege, 1.895 ve 9 gün; fark 60 ve 5.191 gün. TR/EN UI, tablo ve grafik dışlama kontrolleri de var.

Kural seçimleri açıkça değiştirildi: MOQ sıfır desteklenir; kapasite sıfır tedarik yok demektir (MOQ da sıfır olmalı); ücretsiz ürün/nakliye, sıfır günlük değer ve sıfır nakit bütçe geçerlidir; talep sıfır satın alma akışında reddedilir. Üçüncü ondalık basamak sessiz yuvarlanmaz. Dengeli eşitlik gerçek nakit maliyetindedir.

## Localization ve güvenlik doğrulaması

EN ve TR anahtar/format-placeholder eşliği otomatik kontrol edilir. UI testleri iki yönde dil değiştirme, Türkçe kullanıcı adı koruma, politika değişimi, kısıt aç/kapat, hata dilinin yenilenmesi, CSV düğme etiketi, sonuç başlıkları, grafik hover metinleri ve güncel sonuç state'ini gözler. Editor ekleme/silme olayları pinned Streamlit sürümünde public API bulunmadığından gerçek WidgetStates delta olaylarıyla çalıştırılır; yalnızca parser çağrısı yapılmaz.

CSV içerikleri ayrı byte testlerinde doğrulanır. Gerçek tarayıcı üzerinden CSV indirme ve gerçek Excel açılışı bu ortamda çalıştırılmadı; bunlar AppTest düğme/serializer testleriyle aynı şey olarak sunulmaz. Kullanıcı metinleri Markdown/HTML benzeri yorumlamaya karşı literal gösterilir. HTML izni sadece geliştiriciye ait statik CSS ve çeviri altyazısında kalır; kullanıcı metni bu yola verilmez.

## Performans

Linux Python 3.12, `python tools/benchmark.py`; tek ölçüm, performans garantisi değildir. Model süresine giriş doğrulaması dahildir. AppTest süreleri tarayıcı paint/frame ölçümü değildir.

| Teklif | Model (s) | Solver (s) | Toplam (s) | 11 what-if (s) | Çöz+AppTest render (s) | Dil rerun (s) |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0,000794 | 0,002110 | 0,003150 | 0,009884 | 0,094926 | 0,060875 |
| 10 | 0,000919 | 0,005960 | 0,006944 | 0,114776 | 0,075952 | 0,061978 |
| 50 | 0,002801 | 0,016082 | 0,019003 | 0,201646 | 0,119177 | 0,084835 |
| 100 | 0,003848 | 0,029267 | 0,033283 | 0,396741 | 0,165623 | 0,104110 |

Bu örneklerin hepsi OPTIMAL. Karmaşık farklı veride zaman sınırı dolabilir; optimumluk garantisi yerine gerçek statü gösterilir. What-if en fazla 12 nokta ve kısa solver bütçesiyle sınırlıdır. Bütçe tanısı ek çözüm gerektirebilir. Cache 256 girişle sınırlıdır; transient solver hatası tekrar denemeyi kilitlemez. Görsel 100 satır kullanılabilirliği test edilmedi; 100 satır AppTest akışı ve solver performansı test edildi.

## Yeni özellikler ve kabul kriterleri

| Özellik | Gerekçe ve kabul kriteri | Kanıt / belge |
|---|---|---|
| Snapshot sonuç/state | Dil değişimi girdileri ve sonucu korusun; aktif problem değişiminde eski sonuç görünmesin. | İki yönlü AppTest, 8 girdi değişimi; README dil/state. |
| Teklif kimliği + örnek localization | Aynı adlar çakışmasın; yerleşik örnek adları dille değişsin, özel adlar korunsun; ekleme/silme kimliği korunsun. | Duplicate, editor, iki yönlü dil ve örnek localization testleri; README alanlar. |
| Sonuç doğrulama kapısı | Bütün maliyet ve kısıtlar tekrar hesaplanmadan sonuç gösterilmesin; bozuk sonuç güvenli hata olsun. | Altı bozma testi, UI result_invalid; README güvenilir sonuç. |
| Güvenli/tam CSV | EN/TR, BOM, ayırıcı, hassasiyet, formül koruması ve plan bağlamı tutarlı olsun. | 24 dil/ad kombinasyonu, büyük toplam; README CSV. |
| Açık hassasiyet ve sınırlar | NaN/Infinity/fraction/overflow sessizce geçmesin; sıfırlar iş anlamına göre işlensin. | Parametrik API ve tablo testleri; README alanlar. |
| İsteğe bağlı what-if/cache | En fazla 12 örnek, aynı kısıtlar, başarısız noktada açıklama/boşluk, dilde yeniden solver yok. | UI gap/hover/call-count; benchmark; README senaryolar. |

Yeni özelliklerden sonra tüm test paketi yeniden çalıştırıldı. Ekran görüntüsü/dar ekran kanıtı bulunmayan davranışlar görsel olarak doğrulanmış sayılmadı.

## Test kanıtı ve kalite kapıları

Kesin son koşu sayıları ve temiz kopya kontrolü `VALIDATION_RESULTS.md` içinde kaydedilir. Başlangıç: **30 geçti**. Son kaynak testleri Python 3.11.16 ve 3.12.14'te `python -m pytest -q -W error` ile çalıştırılır. `pip check` her iki ortamda bağımlılık uyumsuzluğu göstermedi. AppTest'in beklenen `missing ScriptRunContext ... bare mode` logu filtrelenmedi; gerçek sunucu testinde traceback yok.

| Kapı | Durum ve kanıt |
|---|---|
| 1–5: bağımlılık, doğru yorumlayıcı, discovery, tüm testler, yeni özellik testleri | Linux 3.11/3.12 doğrulandı; son sayılar VALIDATION_RESULTS. |
| 6–10: başlangıç, smoke, EN/TR ve dil/state | Gerçek HTTP başlangıcı + AppTest doğrulandı. Native tarayıcı görsel QA ayrıdır ve açık. |
| 11–14: politika/deadline/bütçe/fazla alım | Bağımsız referans ve regresyonlar doğrulandı. |
| 15: CSV indirme | Serializer baytları ve AppTest düğmesi doğrulandı; gerçek browser indirme/Excel açılışı çalıştırılamadı. Tam uçtan uca kapı **açık** tutuldu. |
| 16–18: 1.700 senaryo, brute-force, ekran toplamları | Otomatik doğrulandı; çok büyük toplamın exact tablo/hover testi dahil. |
| 19–21: kritik warning/traceback, çeviri anahtarı, eski state | Çalıştırılan otomatik kapsamda doğrulandı. |
| 22: README kurulum komutları | Linux komutları çalıştırıldı; Windows/PowerShell çalıştırılmadı, **açık**. |
| 23–24: ZIP içeriği ve ZIP'ten tekrar çalışma | **Çalıştırılmadı:** önceki kapılar tam kapanmadığı için ZIP üretilmedi. Temiz kaynak kopyası test edilebilirliği ayrıca doğrulanır. |

## Kalan riskler ve gerekli devam işi

1. **Windows kapısı:** native Windows'ta README'nin sanal ortam, pip, pytest ve Streamlit komutlarını çalıştırın; aynı testleri ve temel akışları gözleyin. Burada Windows veya PowerShell yok; platform çalıştırması uydurulmadı.
2. **Gerçek tarayıcı/CSV kapısı:** yerel tarayıcıda EN/TR, düzenleme→optimizasyon→dil geçişi, CSV indirme ve dar ekran kontrolü. Cloud tarayıcının localhost erişim reddi etrafından dolaşılmadı.
3. Gerçek Excel bölgesel ayarlarında BOM/ayırıcı/formül ön eki davranışının açılarak gözlenmesi; byte doğruluğu test edilmiş olsa da uygulama uyumluluğu ayrı kontroldür.
4. Bu kapılar kapandıktan sonra kaynak/test/README/rapor/bağımlılık/config dosyalarıyla ZIP oluşturulmalı; içeriği/secrets denetlenmeli; ayrı dizine açılıp kurulum, tüm testler ve başlangıç tekrar çalıştırılmalı; **ancak bundan sonra** ZIP SHA-256 üretilip teslim edilmeli.
5. Scope: tek ürün, sabit fiyat, teklif başına sabit nakliye, eşzamanlı sipariş ve tüm seçili sevkiyatların tamamlanması. Vergi/kur/stok/depo/risk/kısmi kullanım/çok ürün/ortak nakliye/alternatif teklif dışlama yok. Bunlar üretim işletme kararında kullanıcı tarafından ayrıca değerlendirilmelidir.
6. Python/solver sürümü veya platform değişiminde eşit optimum dağılım değişebilir; amaç/kısıt doğruluğu esastır. Kalıcı proje kaydı yok; tam yenileme oturumu sıfırlar.

## Değiştirilen dosyalar

| Dosya | Değişiklik |
|---|---|
| app.py | Kararlı state, editor callback, sonuç fingerprint'i, cache, doğru karşılaştırma, exact para gösterimi, güvenli grafik/CSV, isteğe bağlı what-if. |
| moq_lab/domain.py | Teklif kimlikleri, açık solver/amaç bilgisi, zamanlar, SolverFailure. |
| moq_lab/optimizer.py | Doğrulama, sınırlar, sıfır semantiği, balanced eşitlik, solver statüleri, bağımsız sonuç kapısı. |
| moq_lab/verification.py | Yeni sonuç bütünlüğü denetimi. |
| moq_lab/data_io.py | Yeni katı tablo parser'ı ve güvenli exact CSV serializer. |
| moq_lab/insights.py | Ad yerine satır kimliğiyle doğru açıklama. |
| moq_lab/i18n.py | EN/TR yeni hata, state, karşılaştırma, CSV ve kapsam açıklamaları. |
| tests/test_optimizer.py | Yeni belgelenmiş duplicate/sıfır zaman kuralına uyarlama; önceki kapsam korundu. |
| tests/test_app_localization.py | Kapsamlı EN/TR, delta editor, state, cache, büyük toplam, solver UX. |
| tests/test_audit_model.py | Sınırlar, statüler, bütçe hassasiyeti, tam sayı overflow, sonuç doğrulama. |
| tests/test_reference.py | 360 bağımsız enumerasyon karşılaştırması + 15 property senaryosu. |
| tests/test_data_io.py | CSV güvenliği/yerel biçim, katı parser, çeviri placeholder eşliği. |
| tests/test_performance.py | 1/10/50/100 teklif için geniş toleranslı smoke. |
| tests/test_server_startup.py | Gerçek Streamlit HTTP başlangıcı/health/sayfa testi. |
| tools/benchmark.py | Tekrar üretilebilir model/solver/what-if/AppTest süre ölçümü. |
| README.md | Gerçek kurallar, kurulum, testler, model varsayımları ve açık sınırlar. |
| pyproject.toml | Sürüm 0.4.2. |

## v0.4.2 localization takip düzeltmesi

Gerçek Windows tarayıcı kontrolünde, dil değiştikten sonra karar politikası widget'ının seçili metni ile yerleşik örnek tedarikçi adlarının eski dilde kalabildiği gözlendi. Streamlit aynı widget kimliğinde seçeneklerin görünen `format_func` metnini tarayıcı tarafında yenilemeyebiliyordu; ayrıca v0.4.1 testleri örnek adlarının yalnızca düğmeyle değişmesini özellikle bekliyordu.

v0.4.2 ile politika widget'ı dile özgü bir görünüm kimliği ve dil bağımsız kanonik politika kodu kullanır. Seçili politika korunurken görünen metin yeni dile geçer. Yerleşik örnek adları iki yönde otomatik çevrilir; eşleşmeyen kullanıcı adları korunur. Para birimi kullanıcı tarafından değiştirilmediyse EN/USD ve TR/TRY örnek varsayılanını izler, kullanıcı seçimi varsa korunur. Açık bir sonuçta örnek adları çevrilmişse sonuç yeni adlarla otomatik yeniden doğrulanır.

Bu davranışlar iki yönlü AppTest regresyonlarıyla kapsandı. Son takip koşusunda `python -m pytest -q -W error` sonucu **542 geçti, 0 başarısız, 0 atlanan** oldu.
| AUDIT_REPORT.md / VALIDATION_RESULTS.md | Denetim ve çalıştırma kanıtı; açık teslim kapıları. |

Girdi LICENSE telif atfı korunmuştur; gerçek credential, .env, token veya kişisel sistem yolu dağıtım kaynaklarına eklenmemiştir. Kaynak çalışma çıktısı tam teslim veya production-ready iddiası taşımaz.
