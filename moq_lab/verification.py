"""Recalculate a solver result before exposing it to the user."""
from decimal import Decimal, ROUND_HALF_UP
from .domain import SolverFailure


def verify_result(result, offers, surplus_cost, delay_cost):
    def check(condition):
        if not condition:
            raise SolverFailure("Result failed independent consistency checks.", code="result_invalid")

    lookup = {s.row_id: s for s in offers}
    seen = set()
    cash = Decimal(0)
    product = Decimal(0)
    shipping = Decimal(0)
    quantity = 0
    lead = 0
    for line in result.allocation:
        check(line.row_id in lookup and line.row_id not in seen)
        seen.add(line.row_id)
        s = lookup[line.row_id]
        check(type(line.quantity) is int and line.quantity >= max(1, s.moq))
        check(s.max_capacity is None or line.quantity <= s.max_capacity)
        check(result.max_lead_time_days is None or s.lead_time_days <= result.max_lead_time_days)
        check(line.supplier == s.name.strip() and line.lead_time_days == s.lead_time_days)
        p = Decimal(str(s.unit_price))
        f = Decimal(str(s.shipping_cost))
        check(line.unit_price == p and line.product_cost == p * line.quantity)
        check(line.shipping_cost == f and line.line_total == p * line.quantity + f)
        quantity += line.quantity
        product += p * line.quantity
        shipping += f
        cash += p * line.quantity + f
        lead = max(lead, s.lead_time_days)
    check(quantity >= result.demand and quantity == result.total_quantity)
    check(result.surplus == quantity - result.demand)
    check(result.total_cost == cash and result.product_cost == product and result.shipping_cost == shipping)
    check(result.longest_lead_time_days == lead)
    check(result.budget_limit is None or cash <= result.budget_limit)
    handling = Decimal(str(surplus_cost)) * (quantity - result.demand)
    time = Decimal(str(delay_cost)) * lead if result.optimization_mode == "balanced" else Decimal(0)
    check(result.surplus_handling_cost == handling and result.time_value_cost == time)
    check(result.evaluated_cost == cash + handling + time)
    base = int((cash + handling) * 100)
    expected = {"lowest_cost": (base, lead), "fastest": (lead, base),
                "balanced": (int((cash + handling + time) * 100), int(cash * 100))}[result.optimization_mode]
    check((result.primary_value, result.secondary_value) == expected)
    check(result.is_optimal == (result.primary_status == result.secondary_status == "OPTIMAL"))
    check(result.solver_status == ("OPTIMAL" if result.is_optimal else "FEASIBLE"))
    check(result.cost_per_purchased_unit == (cash / quantity).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
    check(result.effective_cost_per_required_unit == (cash / result.demand).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
