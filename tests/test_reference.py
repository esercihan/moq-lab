"""Independent exhaustive oracle: no optimizer helpers or solver model reused."""
from decimal import Decimal
from itertools import product
from random import Random

import pytest
from moq_lab.domain import Supplier, InfeasibleProblem
from moq_lab.optimizer import optimize_procurement


def enumerate_optimum(demand, suppliers, mode, deadline, budget, handling, daily):
    choices = []
    for s in suppliers:
        cap = s.max_capacity if s.max_capacity is not None else demand + s.moq
        choices.append([0] + list(range(max(1, s.moq), cap + 1)))
    best = None
    for quantities in product(*choices):
        if sum(quantities) < demand:
            continue
        used = [(s, q) for s, q in zip(suppliers, quantities) if q]
        days = max(s.lead_time_days for s, q in used)
        if deadline is not None and days > deadline:
            continue
        cash = sum(Decimal(s.unit_price) * q + Decimal(s.shipping_cost) for s, q in used)
        if budget is not None and cash > budget:
            continue
        base = cash + handling * (sum(quantities) - demand)
        score = {'lowest_cost': (base, days), 'fastest': (days, base),
                 'balanced': (base + daily * days, cash)}[mode]
        if best is None or score < best:
            best = score
    return best


def cases():
    rng = Random(29481)
    for case in range(120):
        offers = []
        for i in range(rng.randint(1, 5)):
            moq = rng.randint(0, 4)
            cap = rng.randint(moq, 5)
            if case % 13 == 0:
                cap = None
            offers.append(Supplier('İşletme' if i % 2 else 'same', moq,
                                   Decimal(rng.randint(0, 15)) / 100,
                                   Decimal(rng.randint(0, 10)) / 100,
                                   cap, rng.randint(0, 6)))
        yield rng.randint(1, 6), offers, rng.choice([None, 0, 3, 6]), rng.choice([None, Decimal('.15'), Decimal('.40'), Decimal('2')]), Decimal(rng.randint(0, 5))/100, Decimal(rng.randint(0, 7))/100


@pytest.mark.parametrize('mode', ['lowest_cost', 'fastest', 'balanced'])
@pytest.mark.parametrize('case', list(cases()), ids=lambda c: '')
def test_against_independent_enumeration(case, mode):
    demand, offers, deadline, budget, handling, daily = case
    expected = enumerate_optimum(demand, offers, mode, deadline, budget, handling, daily)
    kwargs = dict(optimization_mode=mode, max_lead_time_days=deadline, budget_limit=budget,
                  surplus_cost_per_unit=handling, delay_cost_per_day=daily)
    if expected is None:
        with pytest.raises(InfeasibleProblem):
            optimize_procurement(demand, offers, **kwargs)
        return
    result = optimize_procurement(demand, offers, **kwargs)
    assert result.is_optimal and result.solver_status == 'OPTIMAL'
    cash = sum(line.line_total for line in result.allocation)
    qty = sum(line.quantity for line in result.allocation)
    lead = max(line.lead_time_days for line in result.allocation)
    assert cash == result.total_cost
    assert qty == result.total_quantity and qty >= demand
    assert result.surplus == qty - demand
    assert lead == result.longest_lead_time_days
    assert result.shipping_cost == sum(line.shipping_cost for line in result.allocation)
    assert result.product_cost == sum(line.product_cost for line in result.allocation)
    for line in result.allocation:
        index = int(line.row_id.split('_')[1])
        offer = offers[index]
        assert type(line.quantity) is int and line.quantity >= max(1, offer.moq)
        assert offer.max_capacity is None or line.quantity <= offer.max_capacity
        assert deadline is None or line.lead_time_days <= deadline
        assert line.product_cost == offer.unit_price * line.quantity
        assert line.shipping_cost == offer.shipping_cost
        assert line.line_total == line.product_cost + line.shipping_cost
    base = cash + handling * (qty-demand)
    actual = {'lowest_cost': (base, lead), 'fastest': (lead, base),
              'balanced': (base + daily*lead, cash)}[mode]
    assert actual == expected
    scaled = (int(actual[0] * (1 if mode == 'fastest' else 100)),
              int(actual[1] * (1 if mode == 'lowest_cost' else 100)))
    assert (result.primary_value, result.secondary_value) == scaled
    if budget is not None:
        assert cash <= budget


@pytest.mark.parametrize('seed', range(15))
def test_feasibility_monotonicity_and_repeatability(seed):
    rng = Random(seed)
    offers = [Supplier(str(i), 1, str(rng.randint(1, 10)), max_capacity=10,
                       lead_time_days=rng.randint(1, 8)) for i in range(4)]
    result = optimize_procurement(12, offers)
    kwargs = dict(budget_limit=result.total_cost, max_lead_time_days=result.longest_lead_time_days)
    exact = optimize_procurement(12, offers, **kwargs)
    relaxed = optimize_procurement(12, offers, budget_limit=result.total_cost + 10,
                                   max_lead_time_days=result.longest_lead_time_days + 1)
    repeated = optimize_procurement(12, offers, **kwargs)
    assert exact.total_cost == result.total_cost
    assert relaxed.total_cost <= exact.total_cost
    assert (exact.primary_value, exact.secondary_value) == (repeated.primary_value, repeated.secondary_value)
