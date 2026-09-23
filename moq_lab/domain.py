from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Supplier:
    """A supplier offer for one product."""

    name: str
    moq: int
    unit_price: Decimal | str | float
    shipping_cost: Decimal | str | float = Decimal("0")
    max_capacity: int | None = None
    lead_time_days: int = 0
    row_id: str = ""


@dataclass(frozen=True, slots=True)
class PurchaseLine:
    supplier: str
    quantity: int
    unit_price: Decimal
    product_cost: Decimal
    shipping_cost: Decimal
    line_total: Decimal
    lead_time_days: int
    row_id: str = ""


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    is_optimal: bool
    optimization_mode: str
    max_lead_time_days: int | None
    budget_limit: Decimal | None
    demand: int
    total_quantity: int
    surplus: int
    product_cost: Decimal
    shipping_cost: Decimal
    total_cost: Decimal
    surplus_handling_cost: Decimal
    time_value_cost: Decimal
    evaluated_cost: Decimal
    cost_per_purchased_unit: Decimal
    effective_cost_per_required_unit: Decimal
    longest_lead_time_days: int
    allocation: tuple[PurchaseLine, ...]
    solver_status: str = "OPTIMAL"
    primary_status: str = "OPTIMAL"
    secondary_status: str = "OPTIMAL"
    primary_value: int = 0
    secondary_value: int = 0
    model_seconds: float = 0.0
    solver_seconds: float = 0.0


class InvalidProblem(ValueError):
    """Raised when the procurement problem contains invalid inputs."""

    def __init__(self, message: str, *, code: str = "invalid_input", **details: object) -> None:
        super().__init__(message)
        self.code = code
        self.details = details


class InfeasibleProblem(RuntimeError):
    """Raised when no supplier combination can meet demand."""

    def __init__(self, message: str, *, code: str = "no_combination", **details: object) -> None:
        super().__init__(message)
        self.code = code
        self.details = details


class SolverFailure(RuntimeError):
    """An unknown, invalid, or unverifiable solver outcome, not infeasibility."""

    def __init__(self, message: str, *, code: str = "solver_unknown", **details: object):
        super().__init__(message)
        self.code = code
        self.details = details
