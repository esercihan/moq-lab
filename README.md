# MOQ Lab v0.4.2

MOQ Lab is a bilingual procurement decision-support app that optimizes supplier allocation for a single product under MOQ, capacity, fixed shipping, lead-time, surplus, and cash budget constraints.

It is built with Python, Streamlit, Pandas, Plotly, and Google OR-Tools CP-SAT. MOQ Lab is not an ERP, marketplace, AI chatbot, or automatic ordering system. It calculates a recommended purchasing plan; it does not send orders.

## English

### What It Does

MOQ Lab helps compare supplier offers when minimum order quantities and operational constraints make the cheapest-looking supplier not always the best choice.

The app can answer questions such as:

- Which suppliers should be used?
- How much should be purchased from each supplier?
- How much does a lead-time limit increase cost?
- Is a cash budget enough for the required demand?
- What changes when the decision policy is economical, urgent, or balanced?

### Key Features

- Single-product supplier allocation optimizer.
- MOQ and maximum capacity constraints.
- Fixed shipping cost per selected supplier.
- Optional maximum lead-time limit.
- Optional cash budget limit.
- Optional surplus stock penalty.
- Three decision policies: Economical, Urgent, and Balanced.
- English and Turkish localization.
- Language-safe state handling.
- Localized sample supplier names.
- Spreadsheet-safe CSV export.
- Independent verification before showing a result.
- Automated regression tests for model logic, localization, CSV output, and Streamlit startup.

### Quick Start

Python 3.11 or newer is required.

```sh
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Linux/macOS:

```sh
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

If Windows does not recognize `python`, create the virtual environment with:

```powershell
py -3.11 -m venv .venv
```

Then open the local URL printed by Streamlit.

### Running Tests

```sh
python -m pip install -r requirements-dev.txt
python -m pip check
python -m pytest -q -W error
python tools/benchmark.py
```

The v0.4.2 package was validated with the full automated test suite. See `VALIDATION_RESULTS.md` for the validation log and `AUDIT_REPORT.md` for audit notes and known limitations.

### Input Model

Each supplier row represents one offer.

| Field | Meaning |
|---|---|
| Supplier | Supplier name. Empty names are rejected. |
| MOQ | Minimum order quantity for that offer. |
| Unit price | Non-negative price with at most two decimal places. |
| Shipping | Fixed cost paid once if the supplier is selected. |
| Max capacity | Blank means uncapped; otherwise it must be at least MOQ. |
| Lead time | Estimated full days until the shipment arrives. |

Blank rows are ignored. Partial rows, fractional quantities or days, `NaN`, infinite values, invalid money precision, and negative values are rejected instead of being silently corrected.

### Optimization Model

For each supplier offer, `x_i` is the purchased quantity and `y_i` indicates whether the offer is selected.

```text
C = sum(unit_price_i * x_i + shipping_i * y_i)
sum(x_i) >= demand
max(1, MOQ_i) * y_i <= x_i <= U_i * y_i
surplus = sum(x_i) - demand
plan_lead_time = max(lead_time_i * y_i)
C <= budget                         if budget is enabled
y_i = 0 when lead_time_i > deadline  if deadline is enabled
```

Decision policies:

| Policy | Primary objective | Tie-break |
|---|---|---|
| Economical | Cash cost + surplus penalty | Shorter lead time |
| Urgent | Shortest plan lead time | Lower cash cost + surplus penalty |
| Balanced | Cash cost + surplus penalty + time value | Lower real cash cost |

Cash budget applies only to real supplier payments: product cost plus shipping. Surplus and time value are decision penalties, not supplier invoices.

### Reference Scenario

Demand: 1,700 units. Policy: Economical.

| Supplier | MOQ | Unit price | Shipping | Capacity | Lead time |
|---|---:|---:|---:|---:|---:|
| Anadolu Ambalaj | 500 | 1.20 | 35 | 1,000 | 5,200 days |
| Marmara Tedarik | 1,000 | 0.95 | 60 | 1,200 | 9 days |
| Ege Paketleme | 250 | 1.35 | 20 | 500 | 3 days |

Without a lead-time limit, the lowest-cost plan is Anadolu Ambalaj 500 + Marmara Tedarik 1,200. Total cost is 1,835 and plan lead time is 5,200 days.

With a 30-day lead-time limit, the recommended plan becomes Marmara Tedarik 1,200 + Ege Paketleme 500. Total cost is 1,895 and plan lead time is 9 days.

In this scenario, the deadline costs 60 more but saves 5,191 days.

### Localization Notes

The selected decision policy is stored as a stable internal code, so the visible dropdown label updates correctly when the language changes. Built-in sample supplier names switch between English and Turkish, while custom supplier names entered by the user are preserved.

CSV column names, separators, decimal marks, file names, chart titles, warnings, and result labels follow the active language.

### CSV Export

CSV exports include supplier identity, quantity, unit price, product cost, shipping, line total, cost share, lead time, currency, policy, demand, purchased quantity, surplus, plan lead time, cash total, decision penalties, solver status, deadline, and budget.

Turkish export uses semicolon separators and decimal commas. English export uses comma separators and decimal points. Both include UTF-8 BOM.

### Limitations

This version assumes fixed unit prices and one fixed shipping charge per selected offer. It does not model inventory already on hand, warehouse capacity, price breaks, taxes, exchange-rate risk, supplier reliability scores, shared shipping, multi-product budgets, or consuming early partial deliveries.

MOQ Lab is intended as a focused decision-support MVP and portfolio project, not as a production procurement suite.

## Türkçe

### Ne İşe Yarar?

MOQ Lab, minimum sipariş miktarı ve operasyonel kısıtlar yüzünden "en ucuz görünen" tedarikçinin her zaman en iyi seçenek olmadığı satın alma senaryolarını analiz eder.

Uygulama şu sorulara cevap verir:

- Hangi tedarikçiler kullanılmalı?
- Her tedarikçiden kaç adet alınmalı?
- Teslim süresi sınırı maliyeti ne kadar artırıyor?
- Nakit bütçesi talebi karşılamaya yetiyor mu?
- Ekonomik, acil veya dengeli karar politikası sonucu nasıl değiştiriyor?

### Temel Özellikler

- Tek ürün için tedarikçi dağılımı optimizasyonu.
- MOQ ve maksimum kapasite kısıtları.
- Seçilen tedarikçi başına sabit nakliye maliyeti.
- Opsiyonel maksimum teslim süresi sınırı.
- Opsiyonel nakit bütçesi sınırı.
- Opsiyonel fazla stok cezası.
- Üç karar politikası: Ekonomik, Acil ve Dengeli.
- İngilizce ve Türkçe arayüz.
- Dil değişiminde state koruması.
- Aktif dile göre değişen örnek tedarikçi adları.
- Excel açısından güvenli CSV dışa aktarımı.
- Sonuç gösterilmeden önce bağımsız doğrulama.
- Model mantığı, localization, CSV çıktısı ve Streamlit başlangıcı için otomatik regresyon testleri.

### Kurulum

Python 3.11 veya üzeri gerekir.

```sh
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Linux/macOS:

```sh
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Windows `python` komutunu tanımazsa sanal ortamı şu komutla oluşturabilirsiniz:

```powershell
py -3.11 -m venv .venv
```

Sonra Streamlit'in terminalde verdiği yerel adresi açın.

### Testler

```sh
python -m pip install -r requirements-dev.txt
python -m pip check
python -m pytest -q -W error
python tools/benchmark.py
```

v0.4.2 paketi tam otomatik test setiyle doğrulanmıştır. Doğrulama çıktısı için `VALIDATION_RESULTS.md`, denetim notları ve bilinen sınırlar için `AUDIT_REPORT.md` dosyasına bakın.

### Girdi Modeli

Her tedarikçi satırı bir teklifi temsil eder.

| Alan | Anlam |
|---|---|
| Tedarikçi | Tedarikçi adı. Boş adlar reddedilir. |
| MOQ | İlgili teklif için minimum sipariş miktarı. |
| Birim fiyat | En fazla iki ondalık basamaklı, negatif olmayan fiyat. |
| Nakliye | Tedarikçi seçilirse bir kere ödenen sabit maliyet. |
| Maks. kapasite | Boş bırakılırsa sınırsız kabul edilir; doluysa MOQ'dan küçük olamaz. |
| Teslim süresi | Sevkiyatın ulaşması için tahmini tam gün sayısı. |

Boş satırlar atlanır. Kısmi satırlar, kesirli adet veya günler, `NaN`, sonsuz değerler, hatalı para hassasiyeti ve negatif değerler sessizce düzeltilmez; reddedilir.

### Optimizasyon Modeli

Her tedarikçi teklifi için `x_i` satın alınan miktarı, `y_i` ise teklifin seçilip seçilmediğini gösterir.

```text
C = sum(birim_fiyat_i * x_i + nakliye_i * y_i)
sum(x_i) >= talep
max(1, MOQ_i) * y_i <= x_i <= U_i * y_i
fazla_alim = sum(x_i) - talep
plan_suresi = max(teslim_suresi_i * y_i)
C <= butce                              butce etkinse
y_i = 0, teslim_suresi_i > teslim_siniri teslim siniri etkinse
```

Karar politikaları:

| Politika | Birincil hedef | Eşitlik bozucu |
|---|---|---|
| Ekonomik | Nakit maliyet + fazla stok cezası | Daha kısa teslim süresi |
| Acil | En kısa plan süresi | Daha düşük nakit maliyet + fazla stok cezası |
| Dengeli | Nakit maliyet + fazla stok cezası + zaman değeri | Daha düşük gerçek nakit maliyet |

Nakit bütçesi yalnızca gerçek tedarikçi ödemelerine uygulanır: ürün maliyeti artı nakliye. Fazla stok ve zaman değeri karar cezasıdır, tedarikçi faturası değildir.

### Referans Senaryo

Talep: 1.700 adet. Politika: Ekonomik.

| Tedarikçi | MOQ | Birim fiyat | Nakliye | Kapasite | Teslim süresi |
|---|---:|---:|---:|---:|---:|
| Anadolu Ambalaj | 500 | 1,20 | 35 | 1.000 | 5.200 gün |
| Marmara Tedarik | 1.000 | 0,95 | 60 | 1.200 | 9 gün |
| Ege Paketleme | 250 | 1,35 | 20 | 500 | 3 gün |

Teslim süresi sınırı yokken en düşük maliyetli plan Anadolu Ambalaj 500 + Marmara Tedarik 1.200 olur. Toplam maliyet 1.835, plan süresi 5.200 gündür.

30 günlük teslim süresi sınırıyla önerilen plan Marmara Tedarik 1.200 + Ege Paketleme 500 olur. Toplam maliyet 1.895, plan süresi 9 gündür.

Bu senaryoda teslim süresi sınırı 60 maliyet artırır ama 5.191 gün kazandırır.

### Dil Notları

Karar politikası sabit bir iç kodla saklanır; bu yüzden dil değişince dropdown'daki görünen seçim doğru dile güncellenir. Yerleşik örnek tedarikçi adları İngilizce ve Türkçe arasında dönüşür; kullanıcının yazdığı özel tedarikçi adları korunur.

CSV kolonları, ayırıcılar, ondalık işaretleri, dosya adları, grafik başlıkları, uyarılar ve sonuç etiketleri aktif dile uyar.

### CSV Dışa Aktarma

CSV çıktısı tedarikçi kimliği, miktar, birim fiyat, ürün maliyeti, nakliye, satır toplamı, maliyet payı, teslim süresi, para birimi, politika, talep, satın alınan miktar, fazla alım, plan süresi, nakit toplamı, karar cezaları, solver durumu, teslim sınırı ve bütçe bilgilerini içerir.

Türkçe dışa aktarım noktalı virgül ve ondalık virgül kullanır. İngilizce dışa aktarım virgül ve ondalık nokta kullanır. İkisi de UTF-8 BOM içerir.

### Sınırlamalar

Bu sürüm sabit birim fiyat ve seçilen teklif başına tek sabit nakliye varsayar. Mevcut stok, depo kapasitesi, fiyat kırılımları, vergi, kur riski, tedarikçi güvenilirlik puanı, ortak nakliye, çok ürünlü bütçe veya erken gelen kısmi teslimatların tüketimini modellemez.

MOQ Lab üretim ortamı satın alma paketi değil; odaklı bir karar destek MVP'si ve portföy projesi olarak tasarlanmıştır.

## License

MIT. See `LICENSE`.
