# MOQ Lab v0.4.2 — Paket içeriği

## Uygulama

- `app.py`: Streamlit arayüzü ve state yönetimi.
- `moq_lab/`: optimizasyon, veri dönüşümü, açıklamalar, doğrulama ve localization modülleri.
- `.streamlit/config.toml`: yerel Streamlit ayarları.

## Kurulum

- `README.md`: Windows/Linux kurulumu, kullanım ve model varsayımları.
- `requirements.txt`: çalışma zamanı bağımlılıkları.
- `requirements-dev.txt`: test bağımlılıkları.
- `pyproject.toml`: paket ve pytest yapılandırması.

## Doğrulama

- `tests/`: model, brute-force referans, localization, CSV, performans ve sunucu testleri.
- `tools/benchmark.py`: performans smoke testi.
- `AUDIT_REPORT.md`: ayrıntılı denetim ve düzeltme raporu.
- `VALIDATION_RESULTS.md`: çalıştırılmış testlerin kanıtı.
- `SOURCE_SHA256SUMS.txt`: paket içindeki kaynakların SHA-256 değerleri.
- `BUILD_NOTES.md`: v0.4.2 takip düzeltmesinin özeti.

Sanal ortamlar, cache dosyaları, Git geçmişi, geçici çıktılar ve kullanıcı bilgileri pakete dahil edilmez.
