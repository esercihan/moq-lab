# MOQ Lab v0.4.2 paketleme notu

Bu paket, Astra'nın v0.4.1 kaynakları üzerinde yapılan gerçek Windows tarayıcı geri bildirimi sonrasında güncellendi.

v0.4.2 düzeltmeleri:

- Dil değişiminde karar politikası seçili metni aktif dile geçer; seçilen politika korunur.
- Yerleşik örnek tedarikçi adları EN/TR arasında otomatik çevrilir.
- Kullanıcının yazdığı özel tedarikçi adları çevrilmez veya ezilmez.
- Kullanıcı elle para birimi seçmediyse örnek varsayılanı EN/USD ve TR/TRY arasında değişir; kullanıcı seçimi korunur.
- Açık bir sonuçta örnek adları çevrilirse sonuç yeni adlarla otomatik yeniden doğrulanır.
- Localization test paketi genişletildi; tam koşuda 542 test geçti.

AUDIT_REPORT.md ve VALIDATION_RESULTS.md önceki Astra denetiminin kanıtlarını ve yeni takip koşusunu birlikte içerir. Raporlardaki eski “ZIP oluşturulmadı” ifadeleri ilk denetim anını anlatır.

Bu kontroller yapılmış veya geçmiş sayılmamıştır. Paket bütün platformlarda doğrulanmış ya da production-ready olarak sunulmaz. Kaynak kodu, testler, README, raporlar ve yapılandırma dosyaları dahildir. Sanal ortamlar, cache, geçici dosyalar ve credential dosyaları dahil edilmemiştir.

Kurulum için README.md dosyasını kullanın. SOURCE_SHA256SUMS.txt bu sürümün paketlenecek kaynak dosyalarının bütünlük kaydıdır.
