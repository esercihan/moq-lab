from decimal import Decimal

import pytest

from moq_lab.domain import InfeasibleProblem, InvalidProblem, Supplier
from moq_lab.optimizer import optimize_procurement


def test_chooses_lowest_total_cost_not_lowest_unit_price() -> None:
    result = optimize_procurement(
        750,
        [
            Supplier("A", moq=500, unit_price="1.20", shipping_cost="35"),
            Supplier("B", moq=1000, unit_price="0.95", shipping_cost="60"),
            Supplier("C", moq=250, unit_price="1.35", shipping_cost="20"),
        ],
    )

    assert [(line.supplier, line.quantity) for line in result.allocation] == [("A", 750)]
    assert result.total_cost == Decimal("935.00")
    assert result.surplus == 0
    assert result.is_optimal


def test_moq_can_create_unavoidable_surplus() -> None:
    result = optimize_procurement(
        300,
        [Supplier("Bulk", moq=500, unit_price="2.00", shipping_cost="25")],
    )

    assert result.total_quantity == 500
    assert result.surplus == 200
    assert result.total_cost == Decimal("1025.00")


def test_splits_order_when_supplier_capacity_requires_it() -> None:
    result = optimize_procurement(
        1700,
        [
            Supplier("A", moq=500, unit_price="1.20", shipping_cost="35", max_capacity=1000),
            Supplier("B", moq=1000, unit_price="0.95", shipping_cost="60", max_capacity=1200),
            Supplier("C", moq=250, unit_price="1.35", shipping_cost="20", max_capacity=500),
        ],
    )

    assert {(line.supplier, line.quantity) for line in result.allocation} == {("A", 500), ("B", 1200)}
    assert result.total_cost == Decimal("1835.00")
    assert result.surplus == 0


def test_fixed_shipping_can_change_winner() -> None:
    result = optimize_procurement(
        100,
        [
            Supplier("Low unit, high freight", 1, "1.00", "200"),
            Supplier("Higher unit, free freight", 1, "1.50", "0"),
        ],
    )

    assert result.allocation[0].supplier == "Higher unit, free freight"
    assert result.total_cost == Decimal("150.00")


def test_reports_infeasible_total_capacity() -> None:
    with pytest.raises(InfeasibleProblem, match="below demand"):
        optimize_procurement(
            1000,
            [
                Supplier("A", 100, "1", max_capacity=400),
                Supplier("B", 100, "1", max_capacity=500),
            ],
        )


def test_rejects_capacity_below_moq() -> None:
    with pytest.raises(InvalidProblem, match="below MOQ"):
        optimize_procurement(100, [Supplier("A", 200, "1", max_capacity=100)])


def test_duplicate_supplier_names_are_valid_independent_offers() -> None:
    result = optimize_procurement(100, [Supplier("Atlas", 10, "1"), Supplier("atlas", 10, "2")])
    assert result.total_cost == Decimal("100")
    assert result.allocation[0].row_id == "row_0"


def test_reports_lead_time_and_effective_cost() -> None:
    result = optimize_procurement(
        500,
        [Supplier("A", 500, "2.00", "50", lead_time_days=7)],
    )

    assert result.longest_lead_time_days == 7
    assert result.cost_per_purchased_unit == Decimal("2.10")
    assert result.effective_cost_per_required_unit == Decimal("2.10")


def test_deadline_excludes_cheap_but_unrealistically_slow_supplier() -> None:
    suppliers = [
        Supplier("Anadolu", 500, "1.20", "35", 1000, 5200),
        Supplier("Marmara", 1000, "0.95", "60", 1200, 9),
        Supplier("Ege", 250, "1.35", "20", 500, 3),
    ]
    unconstrained = optimize_procurement(1700, suppliers)
    result = optimize_procurement(1700, suppliers, max_lead_time_days=30)

    assert {(line.supplier, line.quantity) for line in result.allocation} == {
        ("Marmara", 1200),
        ("Ege", 500),
    }
    assert result.total_cost == Decimal("1895.00")
    assert result.longest_lead_time_days == 9
    assert unconstrained.total_cost == Decimal("1835.00")
    assert unconstrained.longest_lead_time_days == 5200
    assert result.total_cost - unconstrained.total_cost == Decimal("60.00")
    assert unconstrained.longest_lead_time_days - result.longest_lead_time_days == 5191


def test_fastest_mode_breaks_speed_tie_with_cost() -> None:
    result = optimize_procurement(
        100,
        [
            Supplier("Slow cheap", 1, "1.00", lead_time_days=10),
            Supplier("Fast expensive", 1, "1.50", lead_time_days=1),
            Supplier("Fast very expensive", 1, "2.00", lead_time_days=1),
        ],
        optimization_mode="fastest",
    )

    assert [(line.supplier, line.quantity) for line in result.allocation] == [
        ("Fast expensive", 100)
    ]
    assert result.longest_lead_time_days == 1
    assert result.total_cost == Decimal("150.00")


def test_lowest_cost_mode_breaks_cost_tie_with_speed() -> None:
    result = optimize_procurement(
        100,
        [
            Supplier("Slow", 1, "1.00", lead_time_days=10),
            Supplier("Fast", 1, "1.00", lead_time_days=2),
        ],
    )

    assert result.allocation[0].supplier == "Fast"
    assert result.longest_lead_time_days == 2


def test_balanced_mode_converts_elapsed_days_to_money() -> None:
    result = optimize_procurement(
        100,
        [
            Supplier("Slow cheap", 1, "1.00", lead_time_days=10),
            Supplier("Fast expensive", 1, "1.50", lead_time_days=1),
        ],
        optimization_mode="balanced",
        delay_cost_per_day="10",
    )

    assert result.allocation[0].supplier == "Fast expensive"
    assert result.total_cost == Decimal("150.00")
    assert result.time_value_cost == Decimal("10.00")
    assert result.evaluated_cost == Decimal("160.00")


def test_surplus_handling_cost_can_change_moq_choice() -> None:
    suppliers = [
        Supplier("Bulk", 100, "0.80", lead_time_days=5),
        Supplier("Flexible", 1, "1.20", lead_time_days=5),
    ]

    without_handling = optimize_procurement(80, suppliers)
    with_handling = optimize_procurement(80, suppliers, surplus_cost_per_unit="1.00")

    assert without_handling.allocation[0].supplier == "Bulk"
    assert without_handling.surplus == 20
    assert with_handling.allocation[0].supplier == "Flexible"
    assert with_handling.surplus == 0


def test_deadline_capacity_shortfall_has_actionable_details() -> None:
    with pytest.raises(InfeasibleProblem) as caught:
        optimize_procurement(
            150,
            [
                Supplier("Fast", 10, "1", max_capacity=100, lead_time_days=5),
                Supplier("Slow", 10, "1", max_capacity=100, lead_time_days=50),
            ],
            max_lead_time_days=10,
        )

    assert caught.value.code == "deadline_capacity_shortfall"
    assert caught.value.details == {
        "available": 100,
        "demand": 150,
        "shortage": 50,
        "max_lead_time_days": 10,
    }


def test_no_supplier_within_deadline_has_specific_error() -> None:
    with pytest.raises(InfeasibleProblem) as caught:
        optimize_procurement(
            100,
            [Supplier("Slow", 10, "1", lead_time_days=40)],
            max_lead_time_days=30,
        )

    assert caught.value.code == "no_supplier_within_deadline"
    assert caught.value.details == {"max_lead_time_days": 30}


def test_budget_failure_reports_minimum_required_cash() -> None:
    with pytest.raises(InfeasibleProblem) as caught:
        optimize_procurement(
            100,
            [Supplier("Only", 1, "2.00", "10", lead_time_days=5)],
            budget_limit="200",
        )

    assert caught.value.code == "budget_too_low"
    assert caught.value.details["minimum_cost"] == Decimal("210.00")
    assert caught.value.details["shortfall"] == Decimal("10.00")


def test_balanced_mode_accepts_zero_daily_time_value() -> None:
    result = optimize_procurement(100, [Supplier("A", 1, "1", lead_time_days=1)], optimization_mode="balanced")
    assert result.total_cost == result.evaluated_cost == Decimal("100")
