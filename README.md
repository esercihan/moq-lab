# MOQ Lab v0.4.2

MOQ Lab is a bilingual Streamlit app for optimizing a single-product purchase plan under MOQ, supplier capacity, fixed shipping cost, lead time, surplus, and cash budget constraints.

MOQ Lab, tek ürün satın alma kararlarında MOQ, tedarikçi kapasitesi, sabit nakliye, teslim süresi, fazla alım ve nakit bütçe kısıtlarını birlikte değerlendiren iki dilli bir Streamlit uygulamasıdır.

It uses Google OR-Tools CP-SAT. It is not an ERP, marketplace, AI chat model, or automatic ordering system; it does not send purchase orders.

Google OR-Tools CP-SAT kullanır. ERP, pazar yeri, yapay zeka sohbet modeli veya otomatik sipariş sistemi değildir; sipariş göndermez.

## Features / Özellikler

- English and Turkish UI with state-safe language switching.
- Dil değişiminde mevcut girdileri koruyan İngilizce/Türkçe arayüz.
- Built-in sample suppliers switch between English and Turkish names.
- Yerleşik örnek tedarikçi adları İngilizce/Türkçe arasında otomatik dönüşür.
- Three decision policies: Economical, Urgent, Balanced.
- Üç karar politikası: Ekonomik, Acil, Dengeli.
- MOQ, capacity, lead-time limit, cash budget, surplus penalty, and time-value constraints.
- MOQ, kapasite, teslim süresi sınırı, nakit bütçesi, fazla stok cezası ve zaman değeri kısıtları.
- Spreadsheet-safe CSV export with locale-aware separators and decimal formats.
- Bölgesel formata uygun, Excel açısından güvenli CSV çıktısı.
- Independent result verification before displaying plans.
- Plan gösterilmeden önce bağımsız sonuç doğrulaması.

## Quick Start / Hızlı Başlangıç

Python 3.11 or newer is required.

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

If Windows does not find `python`, create the environment with:

Windows `python` komutunu bulamazsa ortamı şu komutla oluşturabilirsiniz:

```powershell
py -3.11 -m venv .venv
```

Then open the local URL printed by Streamlit.

Sonra Streamlit'in terminalde verdiği yerel adresi açın.

## Running Tests / Testleri Çalıştırma

```sh
python -m pip install -r requirements-dev.txt
python -m pip check
python -m pytest -q -W error
python tools/benchmark.py
```

If you do not activate the virtual environment, replace `python` with `.\.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on Linux/macOS.

Sanal ortamı aktive etmiyorsanız Windows'ta `python` yerine `.\.venv\Scripts\python.exe`, Linux/macOS'ta `.venv/bin/python` kullanın.

The v0.4.2 package was validated with the full automated test suite. See `VALIDATION_RESULTS.md` for evidence and `AUDIT_REPORT.md` for known limitations.

v0.4.2 paketi tam otomatik test setiyle doğrulanmıştır. Kanıtlar için `VALIDATION_RESULTS.md`, bilinen sınırlar için `AUDIT_REPORT.md` dosyasına bakın.

## Input Model / Girdi Modeli

Each supplier row describes one offer:

Her tedarikçi satırı bir teklifi temsil eder:

| Field | Meaning |
|---|---|
| Supplier / Tedarikçi | Supplier name. Empty names are rejected. |
| MOQ | Minimum order quantity for that offer. |
| Unit price / Birim fiyat | Non-negative price with at most two decimal places. |
| Shipping / Nakliye | Fixed cost paid once if the supplier is used. |
| Max capacity / Maks. kapasite | Blank means uncapped; otherwise it must be at least MOQ. |
| Lead time / Teslim süresi | Estimated full days until the shipment arrives. |

Blank rows are ignored. Partial rows, fractional quantities/days, `NaN`, infinite values, invalid money precision, and negative values are rejected instead of being silently corrected.

Boş satırlar atlanır. Kısmi satırlar, kesirli adet/günler, `NaN`, sonsuz değerler, hatalı para hassasiyeti ve negatif değerler sessizce düzeltilmez; reddedilir.

Supported limits:

Desteklenen sınırlar:

| Limit | Value |
|---|---:|
| Offers / Teklif sayısı | 100 |
| Quantity fields / Miktar alanları | 10,000,000 |
| Lead-time fields / Süre alanları | 1,000,000 days |
| Money fields / Para alanları | 1,000,000,000 |

Very large but valid lead times produce a warning. They are not automatically changed.

Çok büyük ama geçerli teslim süreleri uyarı üretir. Otomatik düzeltilmez.

## Optimization Model / Optimizasyon Modeli

For each supplier offer, `x_i` is the purchased quantity and `y_i` indicates whether the offer is selected.

Her tedarikçi teklifi için `x_i` satın alınan miktarı, `y_i` ise teklifin seçilip seçilmediğini gösterir.

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

Karar politikaları:

| Policy / Politika | Primary objective / Birincil hedef | Tie-break / Eşitlik bozucu |
|---|---|---|
| Economical / Ekonomik | Cash cost + surplus penalty | Shorter lead time |
| Urgent / Acil | Shortest plan lead time | Lower cash cost + surplus penalty |
| Balanced / Dengeli | Cash cost + surplus penalty + time value | Lower real cash cost |

Cash budget applies only to real supplier payments: product cost plus shipping. Surplus and time value are decision penalties, not supplier invoices.

Nakit bütçesi yalnızca gerçek tedarikçi ödemelerine uygulanır: ürün maliyeti artı nakliye. Fazla stok ve zaman değeri karar cezasıdır, tedarikçi faturası değildir.

## Reference Scenario / Referans Senaryo

Demand / Talep: 1,700. Policy / Politika: Economical / Ekonomik.

| Supplier / Tedarikçi | MOQ | Unit price / Birim fiyat | Shipping / Nakliye | Capacity / Kapasite | Lead time / Süre |
|---|---:|---:|---:|---:|---:|
| Anadolu Ambalaj | 500 | 1.20 | 35 | 1,000 | 5,200 days |
| Marmara Tedarik | 1,000 | 0.95 | 60 | 1,200 | 9 days |
| Ege Paketleme | 250 | 1.35 | 20 | 500 | 3 days |

Without a lead-time limit, the lowest-cost plan is:

Teslim süresi sınırı yokken en düşük maliyetli plan:

| Supplier / Tedarikçi | Quantity / Miktar |
|---|---:|
| Anadolu Ambalaj | 500 |
| Marmara Tedarik | 1,200 |

Total cost / Toplam maliyet: 1,835. Plan lead time / Plan süresi: 5,200 days.

With a 30-day lead-time limit:

30 günlük teslim süresi sınırıyla:

| Supplier / Tedarikçi | Quantity / Miktar |
|---|---:|
| Marmara Tedarik | 1,200 |
| Ege Paketleme | 500 |

Total cost / Toplam maliyet: 1,895. Plan lead time / Plan süresi: 9 days.

The deadline costs 60 more but saves 5,191 days.

Teslim süresi sınırı 60 maliyet artırır ama 5,191 gün kazandırır.

## Localization Notes / Dil Notları

- The decision policy dropdown stores a stable internal code, so the selected policy label updates when language changes.
- Karar politikası dropdown'u sabit bir iç kod saklar; dil değişince seçili politika etiketi güncellenir.
- Built-in sample supplier names switch between English and Turkish.
- Yerleşik örnek tedarikçi adları İngilizce/Türkçe arasında dönüşür.
- Custom supplier names entered by the user are preserved.
- Kullanıcının yazdığı özel tedarikçi adları korunur.
- If the user has not manually changed the currency, the sample default is USD in English and TRY in Turkish.
- Kullanıcı para birimini elle değiştirmediyse örnek varsayılanı İngilizcede USD, Türkçede TRY olur.
- CSV column names, separators, decimal marks, file names, chart titles, warnings, and result labels follow the active language.
- CSV kolonları, ayırıcılar, ondalık işaretleri, dosya adları, grafik başlıkları, uyarılar ve sonuç etiketleri aktif dile uyar.

## CSV Export / CSV Dışa Aktarma

CSV exports include supplier identity, quantity, unit price, product cost, shipping, line total, cost share, lead time, currency, policy, demand, purchased quantity, surplus, plan lead time, cash total, decision penalties, solver status, deadline, and budget.

CSV çıktısı tedarikçi kimliği, miktar, birim fiyat, ürün maliyeti, nakliye, satır toplamı, maliyet payı, teslim süresi, para birimi, politika, talep, satın alınan miktar, fazla alım, plan süresi, nakit toplamı, karar cezaları, solver durumu, teslim sınırı ve bütçe bilgilerini içerir.

Turkish export uses semicolon separators and decimal commas. English export uses comma separators and decimal points. Both include UTF-8 BOM.

Türkçe dışa aktarım noktalı virgül ve ondalık virgül kullanır. İngilizce dışa aktarım virgül ve ondalık nokta kullanır. İkisi de UTF-8 BOM içerir.

## Limitations / Sınırlamalar

This version assumes fixed unit prices and one fixed shipping charge per selected offer. It does not model inventory already on hand, warehouse capacity, price breaks, taxes, exchange-rate risk, supplier reliability scores, shared shipping, multi-product budgets, or consuming early partial deliveries.

Bu sürüm sabit birim fiyat ve seçilen teklif başına tek sabit nakliye varsayar. Mevcut stok, depo kapasitesi, fiyat kırılımları, vergi, kur riski, tedarikçi güvenilirlik puanı, ortak nakliye, çok ürünlü bütçe veya erken gelen kısmi teslimatların tüketimini modellemez.

The project is intended as a focused decision-support MVP and portfolio project, not as a production procurement suite.

Proje, üretim ortamı satın alma paketi değil; odaklı bir karar destek MVP'si ve portföy projesi olarak tasarlanmıştır.

## Troubleshooting / Sorun Giderme

- `No module named streamlit`: run Streamlit with the same Python interpreter that installed `requirements.txt`.
- `No module named streamlit`: Streamlit'i, `requirements.txt` bağımlılıklarını kuran aynı Python yorumlayıcısıyla çalıştırın.
- Blank capacity means uncapped; zero capacity does not mean uncapped.
- Boş kapasite sınırsızdır; sıfır kapasite sınırsız anlamına gelmez.
- If the budget is infeasible, the reported minimum cash amount belongs to the currently active lead-time limit.
- Bütçe uygulanamazsa raporlanan asgari nakit tutarı aktif teslim süresi sınırına göre hesaplanır.
- `UNKNOWN` means no verified solution was found within the solver time budget; it is not an impossibility proof.
- `UNKNOWN`, solver süresi içinde doğrulanmış çözüm bulunamadığı anlamına gelir; imkansızlık kanıtı değildir.

## License / Lisans

MIT. See `LICENSE`.
