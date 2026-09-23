# MOQ Lab v0.4.2 — Çalıştırma kanıtı

21 Eylül 2026. **Kaynak denetim çıktısı; tam dağıtım/ZIP onayı verilmedi.**

| Kontrol | Gözlenen sonuç |
|---|---|
| Başlangıç v0.4 | 30 geçti, 0 başarısız, 0 atlanan |
| v0.4.2 localization takip koşusu / Linux Python 3.12 | **542 geçti, 0 başarısız, 0 atlanan; 13.63 saniye** |
| Son kaynak / temiz Linux Python 3.12.14 venv | **541 geçti, 0 başarısız, 0 atlanan; 14.78 saniye** |
| Ayrı temiz kaynak kopyası / Linux Python 3.11.16 venv | **541 geçti, 0 başarısız, 0 atlanan; 16.08 saniye** |
| v0.4.1 Pytest discovery | 541 test bulundu |
| v0.4.2 Pytest discovery | 542 test bulundu |
| Bağımlılık kontrolü | İki ortamda `No broken requirements found.` |
| Bağımsız enumerasyon | 120 senaryo × 3 politika = 360 karşılaştırma geçti |
| Monotonluk/tekrar amaçları | 15 seed geçti |
| Gerçek Streamlit HTTP sunucusu | Her iki tam test koşusunda health=200/ok ve ana HTML=200; traceback yok |
| EN/TR UI | AppTest ile iki yönlü dil/state, tablo düzenleme, başarı/hata, grafik/hover, 1–100 teklif geçti |
| CSV | EN/TR BOM, ayırıcı, tam kuruş, formül koruması, plan alanları ve düğme semantiği geçti |
| Native browser/CSV download | Çalıştırılamadı: uzak browser localhost adresini ERR_BLOCKED_BY_CLIENT ile engelledi |
| Dar ekran görsel kontrolü | Çalıştırılmadı |
| Gerçek Excel | Çalıştırılmadı |
| Native Windows/PowerShell komutları | Çalıştırılmadı; Linux ortamı |
| v0.4.1 Astra ZIP kapısı | İlk denetimde yapılmadı; bu satır tarihsel Astra sonucudur. |
| v0.4.2 ZIP bütünlüğü ve yeniden test | Arşiv testi hatasız; ZIP'ten çıkarılan temiz kaynakta **542 geçti, 0 başarısız, 0 atlanan**. |

## Çalıştırılan komutlar

Bağımsız Python 3.11 ve 3.12 yorumlayıcılarıyla temiz sanal ortamlar oluşturuldu; her yorumlayıcının kendi `python -m ...` komutları kullanıldı:

```sh
python -m venv <temiz-ortam>
python -m pip install -r requirements-dev.txt
python -m pip check
python -m pytest --collect-only -q
python -m pytest -q -W error
python tools/benchmark.py
```

Son Python 3.11 test koşusu ayrı, cache/venv içermeyen kopyadan; 3.12 koşusu düzenlenmiş çalışma kaynaklarından çalıştırıldı. Kopyadaki kaynaklar hash ile karşılaştırıldı. `requirements-dev.txt`, `requirements.txt` dosyasını içerdiğinden uygulama bağımlılıkları da kuruldu. Gerçek HTTP başlangıç testinin çalıştırdığı komut:

```sh
python -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port <boş-test-portu>
```

Önceki bağımsız sunucu süreci daha sonra erişilemedi; bu durum başarı diye sunulmadı. Son kanıt, yaşam döngüsünü ve HTTP yanıtlarını aynı test içinde yöneten subprocess testidir.

`-W error` koşularında Python warning'i veya başarısız/atlanan test yok. AppTest'in bare-mode ScriptRunContext logları mevcut; filtrelenmedi ve native tarayıcı kanıtı sayılmadı. Solver UNKNOWN hem gerçek çok kısa zaman bütçesiyle hem kontrollü statü testleriyle; diğer nadir solver dalları statü enjeksiyonuyla doğrulandı.

## İçerik kontrolü

Kaynak kopyasında venv, cache, ZIP, geçici log, Git geçmişi, gerçek .env ve credential bulunmuyor. Özel anahtar, API token ve kişisel mutlak yol için yapılan örüntü taraması bulgu üretmedi; bu tarama mutlak güvenlik garantisi değildir. `LICENSE` içindeki mevcut MIT telif atfı bilinçli olarak korundu.

Girdi ZIP SHA-256 (çıktı ZIP'i değildir):

`1c63e98351a7e2fdde62eec1dddc7fdf827e6513befd0868ff970c629c2400fa`

Çıktı ZIP adı/yolu/SHA-256: **yok**. Kaynak dosyalarının bütünlüğü `SOURCE_SHA256SUMS.txt` ile kayıtlıdır. Açık kapılar ve gerekli devam adımları `AUDIT_REPORT.md` içindedir.
