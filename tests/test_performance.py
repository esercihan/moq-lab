"""Broad smoke limits detect runaway solves rather than machine-speed jitter."""
from time import perf_counter
import pytest
from moq_lab.domain import Supplier
from moq_lab.optimizer import optimize_procurement


def offers_for(n):
    return [Supplier(f'Offer {i}', 1 + i%7, str(1 + (i%13)/10), str(i%3),
                     200 if n > 1 else 2000, 1+i%20) for i in range(n)]


@pytest.mark.parametrize('n', [1, 10, 50, 100])
def test_performance_smoke(n):
    start = perf_counter()
    offers = offers_for(n)
    demand = min(1700, 100*n)
    result = optimize_procurement(demand, offers, time_limit_seconds=2)
    assert result.total_quantity >= demand
    assert result.model_seconds >= 0 and result.solver_seconds >= 0
    assert perf_counter() - start < 15
