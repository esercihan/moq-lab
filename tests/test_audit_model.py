from dataclasses import replace
from decimal import Decimal
import pytest
from ortools.sat.python import cp_model
import moq_lab.optimizer as opt
from moq_lab.domain import Supplier, InvalidProblem, InfeasibleProblem, SolverFailure
from moq_lab.verification import verify_result


@pytest.mark.parametrize('field,value', [
    ('moq', -1), ('moq', 1.5), ('moq', True), ('max_capacity', -1),
    ('max_capacity', 1.2), ('lead_time_days', -1), ('lead_time_days', float('inf')),
    ('unit_price', '-0.01'), ('shipping_cost', '-1'), ('unit_price', 'NaN'),
    ('shipping_cost', 'Infinity'), ('unit_price', 'abc'), ('name', ''), ('name', '   '),
    ('name', None), ('name', 'x'*501), ('moq', 10**8), ('max_capacity', 10**8),
    ('lead_time_days', 10**7), ('unit_price', '1000000001'),
    ('unit_price', '1.005'), ('unit_price', '1.015'), ('unit_price', '-.001'),
])
def test_invalid_supplier_inputs(field, value):
    with pytest.raises(InvalidProblem):
        opt.optimize_procurement(5, [replace(Supplier('A', 1, '1'), **{field: value})])


@pytest.mark.parametrize('demand', [0, -1, 1.5, True, float('nan'), 10**8])
def test_invalid_demand(demand):
    with pytest.raises(InvalidProblem):
        opt.optimize_procurement(demand, [Supplier('A', 1, '1')])


@pytest.mark.parametrize('settings', [
    {'budget_limit': '-.01'}, {'budget_limit':'NaN'}, {'surplus_cost_per_unit': '-1'},
    {'delay_cost_per_day': '-1'}, {'delay_cost_per_day': 'Infinity'},
    {'max_lead_time_days': -1}, {'max_lead_time_days': 1.5}, {'max_lead_time_days':10**7},
    {'optimization_mode':'invalid'}, {'time_limit_seconds':0}, {'time_limit_seconds':float('inf')}
])
def test_invalid_settings(settings):
    with pytest.raises(InvalidProblem):
        opt.optimize_procurement(1, [Supplier('A', 1, '1')], **settings)


def test_empty_and_too_many_offers():
    with pytest.raises(InvalidProblem): opt.optimize_procurement(1, [])
    with pytest.raises(InvalidProblem): opt.optimize_procurement(1, [Supplier('A', 0, 0)] * 101)


@pytest.mark.parametrize('price', ['.01', '.10', '.95', '999.99'])
def test_cents_and_budget_boundary(price):
    suppliers = [Supplier('A', 1, price, '.01')]
    exact = Decimal(price)*3 + Decimal('.01')
    result = opt.optimize_procurement(3, suppliers, budget_limit=exact)
    assert result.total_cost == exact
    with pytest.raises(InfeasibleProblem) as exc:
        opt.optimize_procurement(3, suppliers, budget_limit=exact-Decimal('.01'))
    assert exc.value.details['minimum_cost'] == exact
    assert exc.value.details['shortfall'] == Decimal('.01')


def test_zero_business_semantics():
    result = opt.optimize_procurement(1, [Supplier('closed', 0, 0, max_capacity=0),
                                            Supplier('free', 0, 0, lead_time_days=0)],
                                      budget_limit=0, optimization_mode='balanced', delay_cost_per_day=0)
    assert result.total_cost == result.longest_lead_time_days == 0
    assert len(result.allocation) == 1 and result.allocation[0].supplier == 'free'
    with pytest.raises(InfeasibleProblem):
        opt.optimize_procurement(1, [Supplier('closed', 0, 0, max_capacity=0)])
    with pytest.raises(InvalidProblem):
        opt.optimize_procurement(1, [Supplier('contradiction', 1, 0, max_capacity=0)])


def test_balanced_cash_tiebreak_distinct_from_base_cost():
    # Both scores 10: slow plan base 5+time5, fast plan base10+time0.
    # Slow plan cash2 < fast cash10, but handling3 makes the distinction explicit.
    suppliers = [Supplier('slow bulk', 2, '1', lead_time_days=5),
                 Supplier('fast', 1, '10', lead_time_days=0)]
    r = opt.optimize_procurement(1, suppliers, optimization_mode='balanced', surplus_cost_per_unit='3', delay_cost_per_day='1')
    assert r.evaluated_cost == 10 and r.total_cost == 2
    # Construct equal scores where base-cost secondary would choose the opposite.
    suppliers = [Supplier('surplus cash cheap', 2, '1', lead_time_days=0),
                 Supplier('cash costly', 1, '4', lead_time_days=1)]
    r = opt.optimize_procurement(1, suppliers, optimization_mode='balanced', surplus_cost_per_unit='3', delay_cost_per_day='1')
    assert r.evaluated_cost == 5 and r.total_cost == 2


def test_duplicate_names_do_not_merge_identity_or_shipping():
    r = opt.optimize_procurement(4, [Supplier('same', 1, 1, 2, 2), Supplier('same', 1, 2, 3, 2)])
    assert len({line.row_id for line in r.allocation}) == 2
    assert r.shipping_cost == 5 and r.total_cost == 11


def test_unused_name_or_lead_has_no_effect():
    offers = [Supplier('used', 1, 1, lead_time_days=2), Supplier('unused', 1, 3, lead_time_days=500)]
    before = opt.optimize_procurement(4, offers)
    after = opt.optimize_procurement(4, [offers[0], replace(offers[1], name='başka', lead_time_days=9999)])
    assert before.total_cost == after.total_cost
    assert before.longest_lead_time_days == after.longest_lead_time_days == 2


def test_deadline_equality_and_budget_penalty_separation():
    r = opt.optimize_procurement(1, [Supplier('A', 2, 1, lead_time_days=3)],
                                 max_lead_time_days=3, budget_limit=2, surplus_cost_per_unit=1000,
                                 optimization_mode='balanced', delay_cost_per_day=10000)
    assert r.total_cost == 2 and r.evaluated_cost == 31002


def test_overflow_guard():
    with pytest.raises(InvalidProblem) as e:
        opt.optimize_procurement(10**7, [Supplier(str(i), 0, 10**9) for i in range(100)])
    assert e.value.code == 'numeric_limit'


def scripted_solver(monkeypatch, statuses):
    original = opt._solver
    sequence = iter(statuses)
    class Wrapper:
        def __init__(self, limit): self.real = original(limit); self.status = next(sequence)
        def solve(self, model): self.real.solve(model); return self.status
        def value(self, expression): return self.real.value(expression)
        def status_name(self, status): return self.real.status_name(status)
    monkeypatch.setattr(opt, '_solver', Wrapper)


@pytest.mark.parametrize('status,code', [(cp_model.UNKNOWN, 'solver_unknown'), (cp_model.MODEL_INVALID, 'model_invalid')])
def test_solver_failure_never_fabricates_budget_reason(monkeypatch, status, code):
    scripted_solver(monkeypatch, [status])
    with pytest.raises(SolverFailure) as e:
        opt.optimize_procurement(1, [Supplier('A', 1, 1)], budget_limit=5)
    assert e.value.code == code


@pytest.mark.parametrize('statuses', [[cp_model.FEASIBLE], [cp_model.OPTIMAL, cp_model.FEASIBLE], [cp_model.OPTIMAL, cp_model.UNKNOWN]])
def test_incomplete_lexicographic_proof_is_only_feasible(monkeypatch, statuses):
    scripted_solver(monkeypatch, statuses)
    result = opt.optimize_procurement(1, [Supplier('A', 1, 1)])
    assert not result.is_optimal and result.solver_status == 'FEASIBLE'


def test_unproven_minimum_is_not_reported_as_exact(monkeypatch):
    scripted_solver(monkeypatch, [cp_model.INFEASIBLE, cp_model.FEASIBLE])
    with pytest.raises(InfeasibleProblem) as e:
        opt.optimize_procurement(1, [Supplier('A', 1, 1)], budget_limit=0)
    assert e.value.code == 'budget_minimum_unknown'
    assert 'minimum_cost' not in e.value.details


@pytest.mark.parametrize('field,value', [('total_quantity', 9), ('total_cost', Decimal(100)),
    ('longest_lead_time_days', 5), ('primary_value', 999), ('surplus', -1), ('is_optimal', False)])
def test_recomputation_rejects_corruption(field, value):
    offers = [Supplier('A', 1, 1, row_id='a')]
    result = opt.optimize_procurement(1, offers)
    with pytest.raises(SolverFailure): verify_result(replace(result, **{field:value}), offers, 0, 0)


def test_actual_tiny_time_limit_has_honest_unknown_status():
    offers = [Supplier(str(i), 1, str(1+i%7), max_capacity=100, lead_time_days=i%20) for i in range(100)]
    with pytest.raises(SolverFailure) as e:
        opt.optimize_procurement(1700, offers, time_limit_seconds=0.000001, budget_limit=100000)
    assert e.value.code == 'solver_unknown'


def test_large_valid_money_preserves_cents_beyond_float_precision():
    from moq_lab.data_io import export_csv
    r = opt.optimize_procurement(10**7, [Supplier('Large', 1, '999999999.99', '.01')])
    expected = Decimal('9999999999900000.01')
    assert r.total_cost == expected
    assert b'9999999999900000.01' in export_csv(r, 'en', 'USD')


def test_demand_increase_requires_new_quantity():
    offers = [Supplier('A', 0, 1)]
    old = opt.optimize_procurement(4, offers)
    new = opt.optimize_procurement(5, offers)
    assert old.total_quantity == 4 and new.total_quantity == 5
