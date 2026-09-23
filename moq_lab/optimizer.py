from __future__ import annotations

from decimal import Decimal, DecimalException, ROUND_HALF_UP
from dataclasses import replace
from math import isfinite
from time import perf_counter
from typing import Iterable, Literal

from ortools.sat.python import cp_model

from .domain import (
    InfeasibleProblem,
    InvalidProblem,
    OptimizationResult,
    PurchaseLine,
    Supplier,
    SolverFailure,
)

OptimizationMode = Literal["lowest_cost", "fastest", "balanced"]
VALID_MODES: frozenset[str] = frozenset({"lowest_cost", "fastest", "balanced"})
MONEY_SCALE = 100
_CENT = Decimal("0.01")


def _as_decimal(value: Decimal | str | float) -> Decimal:
    try:
        raw = Decimal(str(value))
        if not raw.is_finite():
            raise InvalidProblem("Money must be finite.", code="money_finite")
        if abs(raw) > Decimal("1000000000"):
            raise InvalidProblem("Money exceeds the supported limit.", code="numeric_limit")
        rounded = raw.quantize(_CENT, rounding=ROUND_HALF_UP)
        if raw != rounded:
            raise InvalidProblem("Use at most two decimal places.", code="money_precision")
        return rounded
    except (DecimalException, ValueError, TypeError) as exc:
        if isinstance(exc, InvalidProblem):
            raise
        raise InvalidProblem("Invalid money value.", code="money_finite") from exc


def _as_cents(value: Decimal | str | float) -> int:
    return int(_as_decimal(value) * MONEY_SCALE)


def _validate(
    demand: int,
    suppliers: tuple[Supplier, ...],
    *,
    optimization_mode: str,
    max_lead_time_days: int | None,
    budget_limit: Decimal | str | float | None,
    surplus_cost_per_unit: Decimal | str | float,
    delay_cost_per_day: Decimal | str | float,
) -> None:
    if not isinstance(demand, int) or isinstance(demand, bool) or demand <= 0:
        raise InvalidProblem("Demand must be a positive whole number.", code="demand_positive")
    if not suppliers:
        raise InvalidProblem("Add at least one supplier.", code="add_supplier")
    if optimization_mode not in VALID_MODES:
        raise InvalidProblem(
            f"Unknown optimization mode: {optimization_mode!r}.",
            code="optimization_mode",
        )
    if max_lead_time_days is not None and (
        not isinstance(max_lead_time_days, int)
        or isinstance(max_lead_time_days, bool)
        or max_lead_time_days < 0
    ):
        raise InvalidProblem(
            "Maximum lead time must be a non-negative whole number.",
            code="max_lead_time_nonnegative",
        )
    if budget_limit is not None and _as_decimal(budget_limit) < 0:
        raise InvalidProblem("Budget limit must be non-negative.", code="budget_positive")
    if _as_decimal(surplus_cost_per_unit) < 0:
        raise InvalidProblem(
            "Surplus handling cost cannot be negative.",
            code="surplus_cost_nonnegative",
        )
    if _as_decimal(delay_cost_per_day) < 0:
        raise InvalidProblem(
            "Daily delay cost cannot be negative.",
            code="delay_cost_nonnegative",
        )
    if demand > 10**7 or len(suppliers) > 100:
        raise InvalidProblem("Supported size exceeded.", code="numeric_limit")
    if max_lead_time_days is not None and max_lead_time_days > 10**6:
        raise InvalidProblem("Supported lead time exceeded.", code="numeric_limit")
    ids: set[str] = set()
    for supplier in suppliers:
        if not isinstance(supplier.name, str) or not supplier.name.strip():
            raise InvalidProblem("Every supplier needs a name.", code="supplier_name")
        name = supplier.name.strip()
        if len(name) > 500:
            raise InvalidProblem("Supplier name exceeds 500 characters.", code="name_length")
        if not isinstance(supplier.row_id, str) or supplier.row_id in ids:
            raise InvalidProblem("Supplier row IDs must be unique.", code="row_id")
        ids.add(supplier.row_id)
        if not isinstance(supplier.moq, int) or isinstance(supplier.moq, bool) or supplier.moq < 0:
            raise InvalidProblem(
                f"{name}: MOQ must be a non-negative whole number.",
                code="moq_positive",
                name=name,
            )
        if _as_decimal(supplier.unit_price) < 0:
            raise InvalidProblem(
                f"{name}: unit price cannot be negative.",
                code="unit_price_negative",
                name=name,
            )
        if _as_decimal(supplier.shipping_cost) < 0:
            raise InvalidProblem(
                f"{name}: shipping cost cannot be negative.",
                code="shipping_negative",
                name=name,
            )
        if supplier.max_capacity is not None:
            if not isinstance(supplier.max_capacity, int) or isinstance(supplier.max_capacity, bool):
                raise InvalidProblem(
                    f"{name}: maximum capacity must be a whole number.",
                    code="capacity_integer",
                    name=name,
                )
            if supplier.max_capacity < supplier.moq:
                raise InvalidProblem(
                    f"{name}: maximum capacity cannot be below MOQ.",
                    code="capacity_below_moq",
                    name=name,
                )
        if (
            not isinstance(supplier.lead_time_days, int)
            or isinstance(supplier.lead_time_days, bool)
            or supplier.lead_time_days < 0
        ):
            raise InvalidProblem(
                f"{name}: lead time must be a non-negative whole number.",
                code="lead_time_nonnegative",
                name=name,
            )
        if (supplier.moq > 10**7 or supplier.lead_time_days > 10**6
                or (supplier.max_capacity is not None and supplier.max_capacity > 10**7)):
            raise InvalidProblem("Supported size exceeded.", code="numeric_limit")



def _upper_bound(demand: int, supplier: Supplier) -> int:
    # With non-negative costs, an optimum exists with x_i <= max(demand, MOQ_i).
    needed = max(demand, supplier.moq)
    return needed if supplier.max_capacity is None else min(supplier.max_capacity, needed)


def _eligible_capacity(
    demand: int,
    suppliers: tuple[Supplier, ...],
    max_lead_time_days: int | None,
) -> tuple[tuple[Supplier, ...], int]:
    eligible = tuple(
        supplier
        for supplier in suppliers
        if max_lead_time_days is None or supplier.lead_time_days <= max_lead_time_days
    )
    capacity = sum(
        _upper_bound(demand, supplier)
        for supplier in eligible
    )
    return eligible, capacity


def _solver(time_limit_seconds: float) -> cp_model.CpSolver:
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 42
    return solver


def optimize_procurement(
    demand: int,
    suppliers: Iterable[Supplier],
    *,
    optimization_mode: OptimizationMode = "lowest_cost",
    max_lead_time_days: int | None = None,
    budget_limit: Decimal | str | float | None = None,
    surplus_cost_per_unit: Decimal | str | float = Decimal("0"),
    delay_cost_per_day: Decimal | str | float = Decimal("0"),
    time_limit_seconds: float = 5.0,
) -> OptimizationResult:
    """Optimize a one-product purchasing plan under operational constraints.

    Modes are lexicographic where appropriate:
    - lowest_cost: minimize procurement plus surplus handling cost, then lead time.
    - fastest: minimize plan lead time, then procurement plus surplus handling cost.
    - balanced: minimize cost plus the monetary value of elapsed days, then cash purchasing cost.

    The plan lead time is the slowest selected supplier because the full demand is
    considered available only when every selected shipment has arrived.
    """

    start = perf_counter()
    if isinstance(time_limit_seconds, bool) or not isinstance(time_limit_seconds, (int, float)) or not isfinite(time_limit_seconds) or time_limit_seconds <= 0:
        raise InvalidProblem("Time limit must be finite and positive.", code="time_limit")
    offers = tuple(replace(s, row_id=s.row_id or f"row_{i}") for i, s in enumerate(suppliers))
    _validate(
        demand,
        offers,
        optimization_mode=optimization_mode,
        max_lead_time_days=max_lead_time_days,
        budget_limit=budget_limit,
        surplus_cost_per_unit=surplus_cost_per_unit,
        delay_cost_per_day=delay_cost_per_day,
    )

    eligible, available = _eligible_capacity(demand, offers, max_lead_time_days)
    if not eligible:
        raise InfeasibleProblem(
            "No supplier can meet the delivery deadline.",
            code="no_supplier_within_deadline",
            max_lead_time_days=max_lead_time_days or 0,
        )
    if available < demand:
        if max_lead_time_days is not None:
            raise InfeasibleProblem(
                "Supplier capacity within the delivery deadline is below demand.",
                code="deadline_capacity_shortfall",
                available=available,
                demand=demand,
                shortage=demand - available,
                max_lead_time_days=max_lead_time_days,
            )
        raise InfeasibleProblem(
            f"Total supplier capacity is {available:,}, below demand of {demand:,}.",
            code="capacity_below_demand",
            available=available,
            demand=demand,
        )

    cost_bound = sum(_as_cents(s.unit_price) * _upper_bound(demand, s) + _as_cents(s.shipping_cost) for s in offers)
    cost_bound += _as_cents(surplus_cost_per_unit) * sum(_upper_bound(demand, s) for s in offers)
    cost_bound += _as_cents(delay_cost_per_day) * max(s.lead_time_days for s in offers)
    if cost_bound > 2**60:
        raise InvalidProblem("Combined integer arithmetic limit exceeded.", code="numeric_limit")
    model = cp_model.CpModel()
    quantities: list[cp_model.IntVar] = []
    selected: list[cp_model.IntVar] = []
    upper_bounds: list[int] = []

    for index, supplier in enumerate(offers):
        upper_bound = _upper_bound(demand, supplier)
        upper_bounds.append(upper_bound)
        quantity = model.new_int_var(0, upper_bound, f"quantity_{index}")
        is_selected = model.new_bool_var(f"selected_{index}")

        model.add(quantity >= max(1, supplier.moq) * is_selected)
        model.add(quantity <= upper_bound * is_selected)
        if max_lead_time_days is not None and supplier.lead_time_days > max_lead_time_days:
            model.add(is_selected == 0)
        quantities.append(quantity)
        selected.append(is_selected)

    total_quantity = sum(quantities)
    max_surplus = max(0, sum(upper_bounds) - demand)
    surplus = model.new_int_var(0, max_surplus, "surplus")
    model.add(total_quantity >= demand)
    model.add(surplus == total_quantity - demand)

    max_possible_lead = max(supplier.lead_time_days for supplier in eligible)
    plan_lead_time = model.new_int_var(0, max_possible_lead, "plan_lead_time")
    model.add_max_equality(plan_lead_time, [s.lead_time_days * selected[i] for i, s in enumerate(offers)])

    product_cost_expr = sum(
        _as_cents(supplier.unit_price) * quantities[index]
        for index, supplier in enumerate(offers)
    )
    shipping_cost_expr = sum(
        _as_cents(supplier.shipping_cost) * selected[index]
        for index, supplier in enumerate(offers)
    )
    procurement_cost_expr = product_cost_expr + shipping_cost_expr
    surplus_cost_expr = _as_cents(surplus_cost_per_unit) * surplus
    base_decision_cost_expr = procurement_cost_expr + surplus_cost_expr
    time_value_expr = _as_cents(delay_cost_per_day) * plan_lead_time

    if budget_limit is not None:
        model.add(procurement_cost_expr <= _as_cents(budget_limit))

    if optimization_mode == "fastest":
        primary_objective = plan_lead_time
        secondary_objective = base_decision_cost_expr
    elif optimization_mode == "balanced":
        primary_objective = base_decision_cost_expr + time_value_expr
        secondary_objective = procurement_cost_expr
    else:
        primary_objective = base_decision_cost_expr
        secondary_objective = plan_lead_time

    phase_limit = time_limit_seconds / 2
    model.minimize(primary_objective)
    first_solver = _solver(phase_limit)
    model_seconds = perf_counter() - start
    solve_start = perf_counter()
    first_status = first_solver.solve(model)

    if first_status == cp_model.MODEL_INVALID:
        raise SolverFailure("Solver rejected the model.", code="model_invalid")
    if first_status == cp_model.UNKNOWN:
        raise SolverFailure("Time limit reached without a verified plan.", code="solver_unknown")
    if first_status == cp_model.INFEASIBLE:
        if budget_limit is not None:
            minimum_plan = optimize_procurement(
                demand, offers, optimization_mode="lowest_cost",
                max_lead_time_days=max_lead_time_days, time_limit_seconds=time_limit_seconds,
            )
            if minimum_plan.primary_status != "OPTIMAL":
                raise InfeasibleProblem("Budget infeasible; exact minimum not proven.", code="budget_minimum_unknown")
            if minimum_plan.total_cost <= _as_decimal(budget_limit):
                raise SolverFailure("Infeasibility diagnosis contradicts a feasible plan.", code="result_invalid")
            raise InfeasibleProblem(
                "Budget is below the minimum feasible procurement cost.", code="budget_too_low",
                budget=_as_decimal(budget_limit), minimum_cost=minimum_plan.total_cost,
                shortfall=minimum_plan.total_cost - _as_decimal(budget_limit),
            )
        raise InfeasibleProblem("No supplier combination can meet the requested constraints.", code="no_combination")

    final_solver = first_solver
    final_status = first_status
    second_status = cp_model.UNKNOWN
    if first_status == cp_model.OPTIMAL:
        best_primary = first_solver.value(primary_objective)
        model.add(primary_objective == best_primary)
        model.minimize(secondary_objective)
        second_solver = _solver(phase_limit)
        second_status = second_solver.solve(model)
        if second_status in (cp_model.MODEL_INVALID, cp_model.INFEASIBLE):
            raise SolverFailure("Lexicographic model is inconsistent.", code="model_invalid")
        final_status = second_status
        if second_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            final_solver = second_solver
            final_status = second_status

    lines: list[PurchaseLine] = []
    product_cost = Decimal("0.00")
    shipping_cost = Decimal("0.00")

    for index, supplier in enumerate(offers):
        quantity = final_solver.value(quantities[index])
        if quantity == 0:
            continue
        unit_price = _as_decimal(supplier.unit_price)
        line_product_cost = unit_price * quantity
        line_shipping = _as_decimal(supplier.shipping_cost)
        product_cost += line_product_cost
        shipping_cost += line_shipping
        lines.append(
            PurchaseLine(
                supplier=supplier.name.strip(),
                quantity=quantity,
                unit_price=unit_price,
                product_cost=line_product_cost,
                shipping_cost=line_shipping,
                line_total=line_product_cost + line_shipping,
                lead_time_days=supplier.lead_time_days,
                row_id=supplier.row_id,
            )
        )

    purchased = sum(line.quantity for line in lines)
    purchased_surplus = purchased - demand
    total_cost = product_cost + shipping_cost
    plan_lead = max(line.lead_time_days for line in lines)
    handling_cost = _as_decimal(surplus_cost_per_unit) * purchased_surplus
    time_cost = (
        _as_decimal(delay_cost_per_day) * plan_lead
        if optimization_mode == "balanced"
        else Decimal("0.00")
    )
    evaluated_cost = total_cost + handling_cost + time_cost
    lines.sort(key=lambda line: (-line.quantity, line.supplier.casefold()))

    result = OptimizationResult(
        is_optimal=first_status == cp_model.OPTIMAL and final_status == cp_model.OPTIMAL,
        optimization_mode=optimization_mode,
        max_lead_time_days=max_lead_time_days,
        budget_limit=None if budget_limit is None else _as_decimal(budget_limit),
        demand=demand,
        total_quantity=purchased,
        surplus=purchased_surplus,
        product_cost=product_cost.quantize(_CENT),
        shipping_cost=shipping_cost.quantize(_CENT),
        total_cost=total_cost.quantize(_CENT),
        surplus_handling_cost=handling_cost.quantize(_CENT),
        time_value_cost=time_cost.quantize(_CENT),
        evaluated_cost=evaluated_cost.quantize(_CENT),
        cost_per_purchased_unit=(total_cost / purchased).quantize(_CENT, rounding=ROUND_HALF_UP),
        effective_cost_per_required_unit=(total_cost / demand).quantize(_CENT, rounding=ROUND_HALF_UP),
        longest_lead_time_days=plan_lead,
        allocation=tuple(lines),
        solver_status="OPTIMAL" if first_status == cp_model.OPTIMAL and second_status == cp_model.OPTIMAL else "FEASIBLE",
        primary_status=first_solver.status_name(first_status),
        secondary_status=first_solver.status_name(second_status),
        primary_value=final_solver.value(primary_objective),
        secondary_value=final_solver.value(secondary_objective),
        model_seconds=model_seconds,
        solver_seconds=perf_counter() - solve_start,
    )

    from .verification import verify_result
    verify_result(result, offers, surplus_cost_per_unit, delay_cost_per_day)
    return result
