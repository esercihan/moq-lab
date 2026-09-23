from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import median
from typing import Iterable

from .domain import OptimizationResult, Supplier


@dataclass(frozen=True, slots=True)
class PriceOutlier:
    supplier: str
    unit_price: Decimal
    reference_price: Decimal
    multiple: Decimal


@dataclass(frozen=True, slots=True)
class LeadTimeOutlier:
    supplier: str
    lead_time_days: int
    reference_days: Decimal | None
    multiple: Decimal | None


@dataclass(frozen=True, slots=True)
class DeadlineExclusion:
    supplier: str
    lead_time_days: int
    max_lead_time_days: int


@dataclass(frozen=True, slots=True)
class CriticalSupplier:
    supplier: str
    capacity_without_supplier: int
    shortage_without_supplier: int
    moq: int
    minimum_commitment: int


@dataclass(frozen=True, slots=True)
class DominantCost:
    supplier: str
    amount: Decimal
    share: Decimal


@dataclass(frozen=True, slots=True)
class DecisionInsights:
    price_outliers: tuple[PriceOutlier, ...]
    lead_time_outliers: tuple[LeadTimeOutlier, ...]
    deadline_exclusions: tuple[DeadlineExclusion, ...]
    critical_suppliers: tuple[CriticalSupplier, ...]
    dominant_cost: DominantCost | None


def _price(value: Decimal | str | float) -> Decimal:
    return Decimal(str(value))


def detect_price_outliers(
    suppliers: Iterable[Supplier], *, multiple_threshold: Decimal = Decimal("5")
) -> tuple[PriceOutlier, ...]:
    """Flag prices far above the median of the other positive offers.

    The warning is intentionally advisory. A legitimate specialist supplier can
    be expensive, so outliers remain valid inputs and are never blocked.
    """

    offers = tuple(suppliers)
    outliers: list[PriceOutlier] = []
    for index, supplier in enumerate(offers):
        comparisons = [
            _price(other.unit_price)
            for other_index, other in enumerate(offers)
            if other_index != index and _price(other.unit_price) > 0
        ]
        if not comparisons:
            continue
        reference = median(comparisons)
        unit_price = _price(supplier.unit_price)
        if reference > 0 and unit_price >= reference * multiple_threshold:
            outliers.append(
                PriceOutlier(
                    supplier=supplier.name.strip(),
                    unit_price=unit_price,
                    reference_price=reference,
                    multiple=(unit_price / reference).quantize(Decimal("0.1")),
                )
            )
    return tuple(outliers)


def detect_lead_time_outliers(
    suppliers: Iterable[Supplier],
    *,
    multiple_threshold: Decimal = Decimal("5"),
    absolute_threshold_days: int = 365,
) -> tuple[LeadTimeOutlier, ...]:
    """Flag unusually long lead times without rejecting the offer."""

    offers = tuple(suppliers)
    outliers: list[LeadTimeOutlier] = []
    for index, supplier in enumerate(offers):
        comparisons = [
            Decimal(other.lead_time_days)
            for other_index, other in enumerate(offers)
            if other_index != index and other.lead_time_days > 0
        ]
        reference = median(comparisons) if comparisons else None
        multiple = (
            (Decimal(supplier.lead_time_days) / reference).quantize(Decimal("0.1"))
            if reference and reference > 0
            else None
        )
        ratio_outlier = multiple is not None and multiple >= multiple_threshold
        absolute_outlier = supplier.lead_time_days >= absolute_threshold_days
        if ratio_outlier or absolute_outlier:
            outliers.append(
                LeadTimeOutlier(
                    supplier=supplier.name.strip(),
                    lead_time_days=supplier.lead_time_days,
                    reference_days=reference,
                    multiple=multiple,
                )
            )
    return tuple(outliers)


def analyze_decision(
    demand: int,
    suppliers: Iterable[Supplier],
    result: OptimizationResult,
    *,
    max_lead_time_days: int | None = None,
) -> DecisionInsights:
    offers = tuple(suppliers)
    eligible_offers = tuple(
        supplier
        for supplier in offers
        if max_lead_time_days is None or supplier.lead_time_days <= max_lead_time_days
    )
    selected_ids = {line.row_id for line in result.allocation}
    critical: list[CriticalSupplier] = []

    for index, supplier in enumerate(offers):
        if supplier not in eligible_offers or (supplier.row_id or f"row_{index}") not in selected_ids:
            continue
        others = [other for j, other in enumerate(offers) if j != index and other in eligible_offers]
        if any(other.max_capacity is None for other in others):
            continue
        capacity_without = sum(other.max_capacity or 0 for other in others)
        if capacity_without >= demand:
            continue
        shortage = demand - capacity_without
        critical.append(
            CriticalSupplier(
                supplier=supplier.name.strip(),
                capacity_without_supplier=capacity_without,
                shortage_without_supplier=shortage,
                moq=supplier.moq,
                minimum_commitment=max(shortage, supplier.moq),
            )
        )

    dominant: DominantCost | None = None
    if result.total_cost > 0 and result.allocation:
        largest = max(result.allocation, key=lambda line: line.line_total)
        share = largest.line_total / result.total_cost
        if share >= Decimal("0.80"):
            dominant = DominantCost(
                supplier=largest.supplier,
                amount=largest.line_total,
                share=share.quantize(Decimal("0.001")),
            )

    return DecisionInsights(
        price_outliers=detect_price_outliers(offers),
        lead_time_outliers=detect_lead_time_outliers(offers),
        deadline_exclusions=tuple(
            DeadlineExclusion(
                supplier=supplier.name.strip(),
                lead_time_days=supplier.lead_time_days,
                max_lead_time_days=max_lead_time_days,
            )
            for supplier in offers
            if max_lead_time_days is not None
            and supplier.lead_time_days > max_lead_time_days
        ),
        critical_suppliers=tuple(critical),
        dominant_cost=dominant,
    )
