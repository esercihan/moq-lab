from decimal import Decimal

from moq_lab.domain import Supplier
from moq_lab.insights import analyze_decision, detect_lead_time_outliers, detect_price_outliers
from moq_lab.optimizer import optimize_procurement


def screenshot_scenario() -> tuple[int, list[Supplier]]:
    return (
        1700,
        [
            Supplier("Atlas Packaging", 500, "1.20", "35", 1000, 5),
            Supplier("Bora Supply", 1000, "5000.95", "60", 1200, 9),
            Supplier("Cedar Works", 250, "1.35", "20", 500, 3),
        ],
    )


def test_flags_extreme_price_without_blocking_it() -> None:
    _, suppliers = screenshot_scenario()

    outliers = detect_price_outliers(suppliers)

    assert len(outliers) == 1
    assert outliers[0].supplier == "Bora Supply"
    assert outliers[0].unit_price == Decimal("5000.95")
    assert outliers[0].reference_price == Decimal("1.275")
    assert outliers[0].multiple == Decimal("3922.3")


def test_explains_capacity_driven_moq_commitment() -> None:
    demand, suppliers = screenshot_scenario()
    result = optimize_procurement(demand, suppliers)

    insights = analyze_decision(demand, suppliers, result)

    critical = insights.critical_suppliers[0]
    assert critical.supplier == "Bora Supply"
    assert critical.capacity_without_supplier == 1500
    assert critical.shortage_without_supplier == 200
    assert critical.moq == 1000
    assert critical.minimum_commitment == 1000


def test_identifies_supplier_that_dominates_total_cost() -> None:
    demand, suppliers = screenshot_scenario()
    result = optimize_procurement(demand, suppliers)

    dominant = analyze_decision(demand, suppliers, result).dominant_cost

    assert dominant is not None
    assert dominant.supplier == "Bora Supply"
    assert dominant.amount == Decimal("5001010.00")
    assert dominant.share == Decimal("1.000")


def test_normal_prices_do_not_raise_outlier_warning() -> None:
    suppliers = [Supplier("A", 10, "1.00"), Supplier("B", 10, "1.20"), Supplier("C", 10, "1.40")]

    assert detect_price_outliers(suppliers) == ()


def test_uncapped_alternative_prevents_capacity_critical_claim() -> None:
    suppliers = [Supplier("A", 10, "1.00"), Supplier("B", 10, "2.00", max_capacity=100)]
    result = optimize_procurement(50, suppliers)

    insights = analyze_decision(50, suppliers, result)

    assert insights.critical_suppliers == ()


def test_flags_extreme_lead_time_and_reports_deadline_exclusion() -> None:
    suppliers = [
        Supplier("Anadolu", 500, "1.20", max_capacity=1000, lead_time_days=5200),
        Supplier("Marmara", 1000, "0.95", max_capacity=1200, lead_time_days=9),
        Supplier("Ege", 250, "1.35", max_capacity=500, lead_time_days=3),
    ]
    result = optimize_procurement(1700, suppliers, max_lead_time_days=30)

    outliers = detect_lead_time_outliers(suppliers)
    insights = analyze_decision(
        1700,
        suppliers,
        result,
        max_lead_time_days=30,
    )

    assert len(outliers) == 1
    assert outliers[0].supplier == "Anadolu"
    assert outliers[0].reference_days == Decimal("6")
    assert outliers[0].multiple == Decimal("866.7")
    assert [(item.supplier, item.lead_time_days) for item in insights.deadline_exclusions] == [
        ("Anadolu", 5200)
    ]
    assert {item.supplier for item in insights.critical_suppliers} == {"Marmara", "Ege"}
