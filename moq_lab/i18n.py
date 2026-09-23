from __future__ import annotations

from decimal import Decimal
from typing import Any

SUPPORTED_LANGUAGES = {"English": "en", "Türkçe": "tr"}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "subtitle": "Build a practical purchasing plan across cost, MOQ, capacity, delivery time, budget, and surplus risk.",
        "purchase_request": "Purchase request",
        "required_quantity": "Required quantity",
        "currency": "Currency",
        "decision_policy": "Decision policy",
        "mode_lowest_cost": "Economical — lowest cost",
        "mode_fastest": "Urgent — fastest delivery",
        "mode_balanced": "Balanced — cost and time value",
        "mode_help_lowest_cost": "Minimizes purchasing and surplus cost; equal-cost plans prefer faster delivery.",
        "mode_help_fastest": "Minimizes plan completion time; equally fast plans prefer lower cost.",
        "mode_help_balanced": "Adds the business value of each elapsed day to cost, then minimizes the combined amount.",
        "enforce_deadline": "Enforce a delivery-time limit",
        "max_lead_time": "Maximum acceptable lead time (days)",
        "advanced_settings": "Advanced business constraints",
        "surplus_cost_per_unit": "Surplus handling cost per unit",
        "surplus_cost_help": "Optional storage, obsolescence, handling, or disposal cost for every unit purchased above demand.",
        "delay_cost_per_day": "Business cost per elapsed day",
        "delay_cost_help": "Used only in Balanced mode. Estimate lost sales, downtime, or urgency cost for each day until the full order arrives.",
        "enforce_budget": "Enforce a cash budget",
        "budget_limit": "Maximum purchasing budget",
        "capacity_caption": "Blank maximum capacity means the supplier is uncapped.",
        "supplier_offers": "Supplier offers",
        "sample_data_caption": "Sample company names are fictional.",
        "supplier": "Supplier",
        "moq": "MOQ",
        "unit_price": "Unit price",
        "shipping": "Shipping",
        "max_capacity": "Max capacity",
        "lead_time_days": "Lead time (days)",
        "optimize": "Optimize purchasing plan",
        "optimal_found": "The selected policy's optimum has been proven.",
        "optimal_lowest_cost": "The lowest-cost plan satisfying all active constraints has been proven optimal.",
        "optimal_fastest": "The fastest plan has been found; cost was minimized among equally fast plans.",
        "optimal_balanced": "The best cost-time trade-off under the stated daily time value has been proven optimal.",
        "feasible_found": "A feasible plan was found, but optimality was not proven within the solver time limit.",
        "outlier_warning": "Possible input outlier: **{supplier}** has a unit price of **{unit_price} {currency}**, which is {multiple}× the median of the other offers ({reference_price} {currency}). Check whether this value is intentional.",
        "lead_outlier_warning": "Possible lead-time outlier: **{supplier}** is **{lead_time} days**, {multiple}× the median of the other offers ({reference} days). Check whether this is intentional.",
        "lead_outlier_warning_absolute": "Possible lead-time outlier: **{supplier}** is **{lead_time} days**. Check whether this is intentional.",
        "deadline_exclusion": "**{supplier} was excluded** because its {lead_time}-day lead time exceeds the {deadline}-day limit.",
        "deadline_impact_title": "Delivery-limit impact",
        "deadline_impact": "Compared with the unconstrained cheapest plan, this plan arrives **{days_saved} days sooner** for an additional **{premium} {currency}**.",
        "deadline_impact_no_premium": "Compared with the unconstrained cheapest plan, this plan arrives **{days_saved} days sooner** without increasing purchasing cost.",
        "unconstrained_reference": "Unconstrained reference: {cost} {currency}, {days} days.",
        "why_plan": "Why this plan?",
        "critical_capacity": "Without **{supplier}**, the other eligible suppliers can provide at most **{capacity} units**—a shortage of **{shortage}** against demand.",
        "moq_trigger": "That {shortage}-unit capacity gap activates **{supplier}'s {moq}-unit MOQ**. The model cannot purchase only the missing quantity.",
        "capacity_feasible": "A plan without {supplier} becomes capacity-feasible at demand {capacity} or below, or if other eligible supplier capacity increases by at least {shortage} units.",
        "no_critical": "No selected supplier is individually required by capacity alone. The allocation follows the active decision policy under all MOQ, capacity, delivery, and budget constraints.",
        "dominant_cost": "**{supplier} contributes {share} of purchasing cost** ({amount} {currency}).",
        "total_cost": "Total purchasing cost",
        "exact": "Exact: {amount} {currency}",
        "effective_unit_cost": "Effective unit cost",
        "suppliers_used": "Suppliers used",
        "purchased": "Purchased",
        "surplus": "Surplus",
        "longest_lead_time": "Plan completion time",
        "deadline_slack": "Delivery-limit buffer: {days} days.",
        "budget_remaining": "Budget remaining: {amount} {currency}.",
        "decision_cost_breakdown": "Decision-cost breakdown",
        "surplus_handling_cost": "Surplus handling cost",
        "time_value_cost": "Time-value cost",
        "evaluated_cost": "Evaluated decision cost",
        "cash_cost_note": "Purchasing cost is the expected cash outlay. Handling and time-value amounts are decision penalties, not supplier invoices.",
        "days": "{days} days",
        "recommended_allocation": "Recommended allocation",
        "quantity": "Quantity",
        "product_cost": "Product cost",
        "line_total": "Line total",
        "cost_share": "Cost share",
        "download_csv": "Download plan as CSV",
        "csv_filename": "moq_lab_purchase_plan.csv",
        "supplier_cost_contribution": "Supplier cost contribution",
        "cost_axis": "Cost ({currency})",
        "what_if": "What-if: how demand changes the active policy",
        "demand": "Demand",
        "threshold_annotation": "{supplier} becomes capacity-required above {threshold}",
        "how_model_works": "How the model works",
        "model_explanation": """MOQ Lab v0.4.1 uses a mixed-integer optimization model. It chooses whole-number order quantities, activates fixed shipping only for used suppliers, and enforces MOQ, capacity, delivery-time, and optional cash-budget constraints.

**Economical** minimizes purchasing plus surplus-handling cost and uses lead time as a tie-breaker. **Urgent** minimizes full-plan arrival time and then cost. **Balanced** adds the stated daily business cost of elapsed time to the decision objective. Plan completion time is the slowest selected supplier because the full requirement is available only when all selected shipments arrive.

Purchasing cost remains the supplier cash outlay. Surplus and time-value costs are explicit decision penalties. Explanations are deterministic analyses of the same constraints; they are not generated by an AI model.""",
        "error.demand_positive": "Demand must be a positive whole number.",
        "error.add_supplier": "Add at least one supplier.",
        "error.supplier_name": "Every supplier needs a name.",
        "error.duplicate_supplier": "Supplier names must be unique: {name!r}.",
        "error.moq_positive": "{name}: MOQ must be a positive whole number.",
        "error.unit_price_negative": "{name}: unit price cannot be negative.",
        "error.shipping_negative": "{name}: shipping cost cannot be negative.",
        "error.capacity_integer": "{name}: maximum capacity must be a whole number.",
        "error.capacity_below_moq": "{name}: maximum capacity cannot be below MOQ.",
        "error.lead_time_nonnegative": "{name}: lead time must be a non-negative whole number.",
        "error.optimization_mode": "Select a valid decision policy.",
        "error.max_lead_time_nonnegative": "Maximum lead time must be a non-negative whole number.",
        "error.budget_positive": "Budget limit must be positive.",
        "error.surplus_cost_nonnegative": "Surplus handling cost cannot be negative.",
        "error.delay_cost_nonnegative": "Daily delay cost cannot be negative.",
        "error.balanced_delay_cost_positive": "Balanced mode requires a positive business cost per elapsed day.",
        "error.capacity_below_demand": "Total supplier capacity is {available}, below demand of {demand}.",
        "error.no_supplier_within_deadline": "No supplier can deliver within the {max_lead_time_days}-day limit. Increase the limit or add a faster supplier.",
        "error.deadline_capacity_shortfall": "Suppliers within the {max_lead_time_days}-day limit can provide only {available} units. Demand is {demand}; at least {shortage} more units of fast capacity are required.",
        "error.budget_too_low": "The {budget} {currency} budget is insufficient. The minimum feasible purchasing cost is {minimum_cost} {currency}; increase the budget by at least {shortfall} {currency}.",
        "error.no_combination": "No supplier combination can meet all active constraints.",
        "error.invalid_input": "One or more inputs are missing or invalid. Check the supplier table.",
    },
    "tr": {
        "subtitle": "Maliyet, MOQ, kapasite, teslim süresi, bütçe ve fazla stok riskini birlikte değerlendirerek uygulanabilir satın alma planı oluşturun.",
        "purchase_request": "Satın alma talebi",
        "required_quantity": "İhtiyaç miktarı",
        "currency": "Para birimi",
        "decision_policy": "Karar politikası",
        "mode_lowest_cost": "Ekonomik — en düşük maliyet",
        "mode_fastest": "Acil — en hızlı teslimat",
        "mode_balanced": "Dengeli — maliyet ve zaman değeri",
        "mode_help_lowest_cost": "Satın alma ve fazla stok maliyetini azaltır; maliyet eşitse daha hızlı planı seçer.",
        "mode_help_fastest": "Planın tamamlanma süresini azaltır; hız eşitse daha düşük maliyetli planı seçer.",
        "mode_help_balanced": "Geçen her günün işletme değerini maliyete ekleyerek toplam karar maliyetini azaltır.",
        "enforce_deadline": "Teslim süresi sınırı uygula",
        "max_lead_time": "Kabul edilen azami teslim süresi (gün)",
        "advanced_settings": "Gelişmiş işletme kısıtları",
        "surplus_cost_per_unit": "Fazla stok birim maliyeti",
        "surplus_cost_help": "Talebin üzerinde alınan her birim için isteğe bağlı depolama, eskime, elleçleme veya imha maliyeti.",
        "delay_cost_per_day": "Geçen her günün işletme maliyeti",
        "delay_cost_help": "Yalnızca Dengeli modda kullanılır. Siparişin tamamı gelene kadar her gün oluşan satış kaybı, duruş veya aciliyet maliyetini tahmin edin.",
        "enforce_budget": "Nakit bütçe sınırı uygula",
        "budget_limit": "Azami satın alma bütçesi",
        "capacity_caption": "Maksimum kapasiteyi boş bırakırsanız tedarikçi kapasitesi sınırsız kabul edilir.",
        "supplier_offers": "Tedarikçi teklifleri",
        "sample_data_caption": "Örnek şirket adları kurgusaldır.",
        "supplier": "Tedarikçi",
        "moq": "MOQ",
        "unit_price": "Birim fiyat",
        "shipping": "Nakliye",
        "max_capacity": "Maks. kapasite",
        "lead_time_days": "Teslim süresi (gün)",
        "optimize": "Satın alma planını optimize et",
        "optimal_found": "Seçilen karar politikasının optimumluğu kanıtlandı.",
        "optimal_lowest_cost": "Tüm etkin kısıtları sağlayan en düşük maliyetli planın optimumluğu kanıtlandı.",
        "optimal_fastest": "En hızlı plan bulundu; aynı hızdaki seçenekler arasında maliyet en aza indirildi.",
        "optimal_balanced": "Belirtilen günlük zaman değerine göre en uygun maliyet-zaman dengesi bulundu.",
        "feasible_found": "Uygulanabilir bir plan bulundu ancak süre sınırı içinde optimumluğu kanıtlanamadı.",
        "outlier_warning": "Olası aykırı veri: **{supplier}** birim fiyatı **{unit_price} {currency}**; bu değer diğer tekliflerin medyanının ({reference_price} {currency}) {multiple} katı. Değerin bilinçli girildiğini kontrol edin.",
        "lead_outlier_warning": "Olası teslim süresi aykırısı: **{supplier} için {lead_time} gün** girilmiş; bu değer diğer tekliflerin medyanının ({reference} gün) {multiple} katı. Değerin bilinçli girildiğini kontrol edin.",
        "lead_outlier_warning_absolute": "Olası teslim süresi aykırısı: **{supplier} için {lead_time} gün** girilmiş. Değerin bilinçli girildiğini kontrol edin.",
        "deadline_exclusion": "**{supplier} değerlendirme dışı bırakıldı:** {lead_time} günlük teslim süresi, {deadline} günlük sınırı aşıyor.",
        "deadline_impact_title": "Teslim süresi sınırının etkisi",
        "deadline_impact": "Kısıtsız en ucuz plana kıyasla bu plan **{days_saved} gün daha erken** tamamlanıyor ve **{premium} {currency}** ek satın alma maliyeti oluşturuyor.",
        "deadline_impact_no_premium": "Kısıtsız en ucuz plana kıyasla bu plan, satın alma maliyetini artırmadan **{days_saved} gün daha erken** tamamlanıyor.",
        "unconstrained_reference": "Kısıtsız referans: {cost} {currency}, {days} gün.",
        "why_plan": "Bu plan neden seçildi?",
        "critical_capacity": "**{supplier}** olmadan diğer uygun tedarikçiler en fazla **{capacity} adet** sağlayabiliyor; talebe göre **{shortage} adet kapasite açığı** oluşuyor.",
        "moq_trigger": "{shortage} adetlik kapasite açığı, **{supplier} tedarikçisinin {moq} adetlik MOQ koşulunu** tetikliyor. Model yalnızca eksik miktarı satın alamıyor.",
        "capacity_feasible": "{supplier} kullanılmayan bir plan; talep {capacity} veya altına indiğinde ya da diğer uygun tedarikçilerin kapasitesi en az {shortage} adet arttığında kapasite açısından mümkün hâle gelir.",
        "no_critical": "Seçilen tedarikçilerden hiçbiri yalnızca kapasite nedeniyle tek başına zorunlu değil. Dağılım; tüm MOQ, kapasite, teslimat ve bütçe koşulları altında etkin karar politikasına göre belirlendi.",
        "dominant_cost": "**Satın alma maliyetinin {share} oranındaki kısmı {supplier} kaynaklıdır** ({amount} {currency}).",
        "total_cost": "Toplam satın alma maliyeti",
        "exact": "Tam tutar: {amount} {currency}",
        "effective_unit_cost": "Efektif birim maliyet",
        "suppliers_used": "Kullanılan tedarikçi",
        "purchased": "Satın alınan",
        "surplus": "Fazla alım",
        "longest_lead_time": "Planın tamamlanma süresi",
        "deadline_slack": "Teslim süresi tamponu: {days} gün.",
        "budget_remaining": "Kalan bütçe: {amount} {currency}.",
        "decision_cost_breakdown": "Karar maliyeti kırılımı",
        "surplus_handling_cost": "Fazla stok maliyeti",
        "time_value_cost": "Zaman değeri maliyeti",
        "evaluated_cost": "Değerlendirilen karar maliyeti",
        "cash_cost_note": "Satın alma maliyeti beklenen nakit çıkışıdır. Fazla stok ve zaman değeri tutarları tedarikçi faturası değil, karar cezasıdır.",
        "days": "{days} gün",
        "recommended_allocation": "Önerilen sipariş dağılımı",
        "quantity": "Miktar",
        "product_cost": "Ürün maliyeti",
        "line_total": "Satır toplamı",
        "cost_share": "Maliyet payı",
        "download_csv": "Planı CSV olarak indir",
        "csv_filename": "moq_lab_satin_alma_plani.csv",
        "supplier_cost_contribution": "Tedarikçi maliyet katkısı",
        "cost_axis": "Maliyet ({currency})",
        "what_if": "Senaryo analizi: talep değişince etkin politika ne sonuç verir?",
        "demand": "Talep",
        "threshold_annotation": "{threshold} üzerindeki talepte {supplier} kapasite nedeniyle gerekli",
        "how_model_works": "Model nasıl çalışıyor?",
        "model_explanation": """MOQ Lab v0.4.1, karma tamsayılı bir optimizasyon modeli kullanır. Tam sayı sipariş miktarlarını belirler; sabit nakliye maliyetini yalnızca kullanılan tedarikçiler için devreye sokar; MOQ, kapasite, teslim süresi ve isteğe bağlı nakit bütçesi koşullarını uygular.

**Ekonomik** politika satın alma ile fazla stok maliyetini azaltır ve eşit maliyette teslim süresini kullanır. **Acil** politika önce planın tamamlanma süresini, ardından maliyeti azaltır. **Dengeli** politika geçen her gün için belirtilen işletme maliyetini karar hedefine ekler. Planın tamamlanma süresi, ihtiyacın tamamı ancak bütün sevkiyatlar ulaştığında hazır olacağı için seçilen en yavaş tedarikçinin süresidir.

Satın alma maliyeti tedarikçiye yapılacak nakit çıkışıdır. Fazla stok ve zaman değeri açık karar cezalarıdır. Açıklamalar aynı kısıtların deterministik analizidir; bir yapay zekâ modeli tarafından üretilmez.""",
        "error.demand_positive": "Talep pozitif bir tam sayı olmalıdır.",
        "error.add_supplier": "En az bir tedarikçi ekleyin.",
        "error.supplier_name": "Her tedarikçinin bir adı olmalıdır.",
        "error.duplicate_supplier": "Tedarikçi adları benzersiz olmalıdır: {name!r}.",
        "error.moq_positive": "{name}: MOQ pozitif bir tam sayı olmalıdır.",
        "error.unit_price_negative": "{name}: birim fiyat negatif olamaz.",
        "error.shipping_negative": "{name}: nakliye maliyeti negatif olamaz.",
        "error.capacity_integer": "{name}: maksimum kapasite tam sayı olmalıdır.",
        "error.capacity_below_moq": "{name}: maksimum kapasite MOQ değerinden düşük olamaz.",
        "error.lead_time_nonnegative": "{name}: teslim süresi negatif olmayan bir tam sayı olmalıdır.",
        "error.optimization_mode": "Geçerli bir karar politikası seçin.",
        "error.max_lead_time_nonnegative": "Azami teslim süresi negatif olmayan bir tam sayı olmalıdır.",
        "error.budget_positive": "Bütçe sınırı pozitif olmalıdır.",
        "error.surplus_cost_nonnegative": "Fazla stok maliyeti negatif olamaz.",
        "error.delay_cost_nonnegative": "Günlük gecikme maliyeti negatif olamaz.",
        "error.balanced_delay_cost_positive": "Dengeli mod için geçen her günün işletme maliyeti pozitif olmalıdır.",
        "error.capacity_below_demand": "Toplam tedarikçi kapasitesi {available}; {demand} adetlik talebin altında.",
        "error.no_supplier_within_deadline": "Hiçbir tedarikçi {max_lead_time_days} günlük sınır içinde teslimat yapamıyor. Süreyi artırın veya daha hızlı bir tedarikçi ekleyin.",
        "error.deadline_capacity_shortfall": "{max_lead_time_days} günlük sınır içindeki tedarikçiler yalnızca {available} adet sağlayabiliyor. Talep {demand}; en az {shortage} adet ek hızlı kapasite gerekiyor.",
        "error.budget_too_low": "{budget} {currency} tutarındaki bütçe yetersiz. Uygulanabilir en düşük satın alma maliyeti {minimum_cost} {currency}; bütçeyi en az {shortfall} {currency} artırın.",
        "error.no_combination": "Tüm etkin kısıtları karşılayan bir tedarikçi kombinasyonu bulunamadı.",
        "error.invalid_input": "Bir veya daha fazla veri eksik ya da geçersiz. Tedarikçi tablosunu kontrol edin.",
    },
}


# Audit additions; both catalogs remain structurally identical.
TRANSLATIONS["en"]['precision_note'] = 'Use at most two decimal places for money. Values with extra precision are rejected.'
TRANSLATIONS["tr"]['precision_note'] = 'Para tutarlarında en fazla iki ondalık basamak kullanın. Daha hassas değerler reddedilir.'
TRANSLATIONS["en"]['load_sample'] = 'Load sample data (replaces table)'
TRANSLATIONS["tr"]['load_sample'] = 'Örnek verileri yükle (tabloyu değiştirir)'
TRANSLATIONS["en"]['stale_result'] = 'Inputs changed. Optimize again to see a current plan.'
TRANSLATIONS["tr"]['stale_result'] = 'Girdiler değişti. Güncel plan için yeniden optimize edin.'
TRANSLATIONS["en"]['comparison_unavailable'] = 'The deadline-free comparison could not be verified.'
TRANSLATIONS["tr"]['comparison_unavailable'] = 'Teslim süresi sınırı olmayan karşılaştırma doğrulanamadı.'
TRANSLATIONS["en"]['run_what_if'] = 'Calculate demand scenarios'
TRANSLATIONS["tr"]['run_what_if'] = 'Talep senaryolarını hesapla'
TRANSLATIONS["en"]['row_id'] = 'Offer ID'
TRANSLATIONS["tr"]['row_id'] = 'Teklif kimliği'
TRANSLATIONS["en"]['solver_status'] = 'Solution status'
TRANSLATIONS["tr"]['solver_status'] = 'Çözüm durumu'
TRANSLATIONS["en"]['status_optimal'] = 'Proven optimal'
TRANSLATIONS["tr"]['status_optimal'] = 'Optimumluğu kanıtlandı'
TRANSLATIONS["en"]['status_feasible'] = 'Feasible; optimum unproven'
TRANSLATIONS["tr"]['status_feasible'] = 'Uygulanabilir; optimumluğu kanıtlanmadı'
TRANSLATIONS["en"]['error.money_finite'] = 'Money fields must contain finite numeric values.'
TRANSLATIONS["tr"]['error.money_finite'] = 'Para alanları geçerli ve sonlu sayılar içermelidir.'
TRANSLATIONS["en"]['error.money_precision'] = 'Money fields support at most two decimal places; correct the value explicitly.'
TRANSLATIONS["tr"]['error.money_precision'] = 'Para alanları en fazla iki ondalık basamak destekler; değeri açıkça düzeltin.'
TRANSLATIONS["en"]['error.numeric_limit'] = 'Supported limits exceeded: 100 offers, 10,000,000 units per field, 1,000,000 days, 1,000,000,000 per money field, and combined integer cost below 2^60 cents.'
TRANSLATIONS["tr"]['error.numeric_limit'] = 'Desteklenen sınırlar aşıldı: 100 teklif, miktar alanı başına 10.000.000 adet, 1.000.000 gün, para alanı başına 1.000.000.000 ve birleşik maliyet için 2^60 kuruş.'
TRANSLATIONS["en"]['error.name_length'] = 'Supplier names are limited to 500 characters.'
TRANSLATIONS["tr"]['error.name_length'] = 'Tedarikçi adı en fazla 500 karakter olabilir.'
TRANSLATIONS["en"]['error.row_id'] = 'Offer IDs must be unique. Reload the input table.'
TRANSLATIONS["tr"]['error.row_id'] = 'Teklif kimlikleri benzersiz olmalıdır. Girdi tablosunu yeniden yükleyin.'
TRANSLATIONS["en"]['error.time_limit'] = 'Solver time limit must be finite and positive.'
TRANSLATIONS["tr"]['error.time_limit'] = 'Çözücü süre sınırı sonlu ve pozitif olmalıdır.'
TRANSLATIONS["en"]['error.solver_unknown'] = 'No verified plan was found within the time limit. Infeasibility has not been proven. Try again or simplify the problem.'
TRANSLATIONS["tr"]['error.solver_unknown'] = 'Süre sınırında doğrulanmış plan bulunamadı. Uygulanamazlık kanıtlanmadı. Tekrar deneyin veya problemi sadeleştirin.'
TRANSLATIONS["en"]['error.model_invalid'] = 'The solver rejected the model. No plan is displayed; report this model error.'
TRANSLATIONS["tr"]['error.model_invalid'] = 'Çözücü modeli reddetti. Plan gösterilmedi; bu model hatasını bildirin.'
TRANSLATIONS["en"]['error.result_invalid'] = 'The result failed consistency checks and was withheld. Report this verification error.'
TRANSLATIONS["tr"]['error.result_invalid'] = 'Sonuç tutarlılık kontrolünden geçmedi ve gösterilmedi. Bu doğrulama hatasını bildirin.'
TRANSLATIONS["en"]['error.budget_minimum_unknown'] = 'The cash budget is infeasible under the active constraints, but the exact minimum budget was not proven within the time limit.'
TRANSLATIONS["tr"]['error.budget_minimum_unknown'] = 'Nakit bütçe etkin kısıtlar altında yetersiz; ancak gerekli kesin asgari bütçe süre sınırında kanıtlanamadı.'
TRANSLATIONS["en"]['error.integer_input'] = 'Quantity and day fields require finite whole numbers. Text, fractions and missing values are not accepted.'
TRANSLATIONS["tr"]['error.integer_input'] = 'Miktar ve gün alanları sonlu tam sayı olmalıdır. Metin, kesir ve eksik değer kabul edilmez.'
TRANSLATIONS["en"]['deadline_impact'] = 'Compared with the same policy without a deadline, this plan completes **{days_saved} days earlier** with **{premium} {currency}** additional cash cost.'
TRANSLATIONS["tr"]['deadline_impact'] = 'Aynı politikanın teslim süresi sınırı olmayan sonucuna kıyasla bu plan **{days_saved} gün daha erken** tamamlanır; ek nakit maliyet **{premium} {currency}** olur.'
TRANSLATIONS["en"]['deadline_impact_no_premium'] = 'Compared with the same policy without a deadline, this plan completes **{days_saved} days earlier** at the same cash cost.'
TRANSLATIONS["tr"]['deadline_impact_no_premium'] = 'Aynı politikanın teslim süresi sınırı olmayan sonucuna kıyasla bu plan aynı nakit maliyetle **{days_saved} gün daha erken** tamamlanır.'
TRANSLATIONS["en"]['deadline_saving'] = 'Compared with the same policy without a deadline, this plan completes **{days_saved} days earlier** and saves **{premium} {currency}** in cash cost.'
TRANSLATIONS["tr"]['deadline_saving'] = 'Aynı politikanın teslim süresi sınırı olmayan sonucuna kıyasla bu plan **{days_saved} gün daha erken** tamamlanır ve **{premium} {currency}** nakit tasarruf sağlar.'
TRANSLATIONS["en"]['error.moq_positive'] = '{name}: MOQ must be a non-negative whole number. Zero means no minimum, but a used offer must supply at least one unit.'
TRANSLATIONS["tr"]['error.moq_positive'] = '{name}: MOQ negatif olmayan bir tam sayı olmalıdır. Sıfır, alt sınır olmadığını belirtir; kullanılan teklif en az bir adet sağlamalıdır.'
TRANSLATIONS["en"]['error.budget_positive'] = 'Budget must be non-negative. A zero budget permits only free purchases.'
TRANSLATIONS["tr"]['error.budget_positive'] = 'Bütçe negatif olamaz. Sıfır bütçe yalnızca ücretsiz alımlara izin verir.'
TRANSLATIONS["en"]['model_limits'] = 'Lead times are estimated days after placing simultaneous orders. Completion means **all selected shipments** have arrived, including surplus. Earlier partial deliveries are not consumed by this model.\n\nFlat prices and one fixed freight charge per used offer are assumed. Existing stock, warehouse capacity, quantity discounts, taxes, exchange-rate risk, supplier reliability, shared or tiered freight, multi-product budgets and the workload of splitting orders are not modeled. All offers use one currency; changing its label does not convert values.\n\nMOQ zero means no minimum; capacity zero means no supply and requires MOQ zero. Free prices, free freight and same-day delivery are valid. Balanced mode accepts zero daily value and breaks equal scores by cash cost. Display percentages are rounded and may not sum to exactly 100%.'
TRANSLATIONS["tr"]['model_limits'] = 'Teslim süreleri, eşzamanlı sipariş verildikten sonraki tahmini gün sayılarıdır. Tamamlanma, fazla alım dahil **seçilen bütün sevkiyatların** ulaşmasıdır. Erken gelen kısmi teslimatların kullanımı modellenmez.\n\nSabit birim fiyat ve kullanılan teklif başına tek sabit nakliye ücreti varsayılır. Mevcut stok, depo kapasitesi, miktar indirimi, vergiler, kur riski, tedarikçi güvenilirliği, ortak veya kademeli nakliye, çok ürünlü bütçe ve sipariş bölmenin iş yükü modellenmez. Tek para birimi kullanılır; etiket değişimi kur dönüşümü yapmaz.\n\nMOQ sıfır, alt sınır olmadığını; kapasite sıfır, tedarik olmadığını belirtir ve MOQ sıfır olmalıdır. Ücretsiz ürün, ücretsiz nakliye ve aynı gün teslim geçerlidir. Dengeli politika sıfır günlük değeri kabul eder, eşit puanda nakit maliyeti kullanır. Görünen yüzdeler yuvarlanır ve toplamı tam %100 olmayabilir.'

TRANSLATIONS["en"]["scenario_policy"] = "Active policy: {policy}. Points are sampled independently; the line is not an interpolation guarantee."
TRANSLATIONS["tr"]["scenario_policy"] = "Etkin politika: {policy}. Noktalar bağımsız örneklemlerdir; çizgi ara talepler için sonuç garantisi değildir."

TRANSLATIONS["en"]["comparison_unproven"] = "At least one comparison plan is only feasible; no proven deadline impact is claimed."
TRANSLATIONS["tr"]["comparison_unproven"] = "Karşılaştırılan planlardan en az birinin optimumluğu kanıtlanmadı; kesin teslim süresi etkisi iddia edilmez."


def translate(language: str, key: str, **values: Any) -> str:
    language_map = TRANSLATIONS.get(language, TRANSLATIONS["en"])
    template = language_map.get(key, TRANSLATIONS["en"].get(key, key))
    return template.format(**values)


def format_number(
    language: str,
    value: Decimal | float | int,
    *,
    decimals: int = 0,
) -> str:
    formatted = f"{value:,.{decimals}f}"
    if language == "tr":
        formatted = formatted.replace(",", "_").replace(".", ",").replace("_", ".")
    return formatted


def format_percent(language: str, value: Decimal | float, *, decimals: int = 1) -> str:
    percentage = format_number(language, value * 100, decimals=decimals)
    return f"%{percentage}" if language == "tr" else f"{percentage}%"
