from __future__ import annotations

from decimal import Decimal, DecimalException
from hashlib import sha256
from uuid import uuid4
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from moq_lab.domain import InfeasibleProblem, InvalidProblem, Supplier, SolverFailure
from moq_lab.data_io import dataframe_to_suppliers, export_csv, markdown_text
from moq_lab.i18n import SUPPORTED_LANGUAGES, format_number, format_percent, translate
from moq_lab.insights import analyze_decision
from moq_lab.optimizer import OptimizationMode, optimize_procurement


st.set_page_config(page_title="MOQ Lab", page_icon="📦", layout="wide")
st.markdown(
    """
    <style>
      .block-container {max-width: 1180px; padding-top: 2.2rem;}
      [data-testid="stMetric"] {
        background: rgba(49, 51, 63, 0.06);
        border: 1px solid rgba(49, 51, 63, 0.12);
        border-radius: 14px;
        padding: 14px 16px;
      }
      .subtle {color: #667085; margin-top: -0.7rem;}
      [data-testid="stMetricValue"] {font-size: clamp(1.1rem, 2vw, 2rem);}
      [data-testid="stMetricValue"] > div {white-space: normal; overflow-wrap: anywhere;}
    </style>
    """,
    unsafe_allow_html=True,
)

language_name = st.sidebar.selectbox(
    "Language / Dil",
    options=list(SUPPORTED_LANGUAGES),
    index=0,
    key="language",
)
language = SUPPORTED_LANGUAGES[language_name]
previous_language = st.session_state.get("_active_language", language)
language_changed = previous_language != language


def tx(key: str, **values: object) -> str:
    return translate(language, key, **{k: markdown_text(v) if k in {"supplier", "name"} else v for k, v in values.items()})


st.title("📦 MOQ Lab")
st.markdown(f'<p class="subtle">{tx("subtitle")}</p>', unsafe_allow_html=True)

DEFAULT_OFFERS = {
    "en": pd.DataFrame(
        [
            {"Supplier": "Atlas Packaging", "MOQ": 500, "Unit price": 1.20, "Shipping": 35.00, "Max capacity": 1000, "Lead time (days)": 5},
            {"Supplier": "Bora Supply", "MOQ": 1000, "Unit price": 0.95, "Shipping": 60.00, "Max capacity": 1200, "Lead time (days)": 9},
            {"Supplier": "Cedar Works", "MOQ": 250, "Unit price": 1.35, "Shipping": 20.00, "Max capacity": 500, "Lead time (days)": 3},
        ]
    ),
    "tr": pd.DataFrame(
        [
            {"Supplier": "Anadolu Ambalaj", "MOQ": 500, "Unit price": 1.20, "Shipping": 35.00, "Max capacity": 1000, "Lead time (days)": 5},
            {"Supplier": "Marmara Tedarik", "MOQ": 1000, "Unit price": 0.95, "Shipping": 60.00, "Max capacity": 1200, "Lead time (days)": 9},
            {"Supplier": "Ege Paketleme", "MOQ": 250, "Unit price": 1.35, "Shipping": 20.00, "Max capacity": 500, "Lead time (days)": 3},
        ]
    ),
}

DEFAULT_CURRENCIES = {"en": "USD", "tr": "TRY"}


@st.cache_data(show_spinner=False, max_entries=256)
def cached_outcome(demand, suppliers, **settings):
    try:
        return optimize_procurement(demand, suppliers, **settings), None
    except (InvalidProblem, InfeasibleProblem) as exc:
        return None, (type(exc).__name__, exc.code, exc.details)


def cached_optimize(demand, suppliers, **settings):
    result, error = cached_outcome(demand, suppliers, **settings)
    if error:
        error_type, code, details = error
        cls = {"InvalidProblem": InvalidProblem, "InfeasibleProblem": InfeasibleProblem,
               "SolverFailure": SolverFailure}[error_type]
        raise cls(code, code=code, **details)
    return result


def load_sample():
    frame = DEFAULT_OFFERS[language].copy()
    frame["_id"] = [uuid4().hex[:12] for _ in range(len(frame))]
    st.session_state["offers"] = frame
    st.session_state["_sample_name_language"] = language
    st.session_state["editor_epoch"] = st.session_state.get("editor_epoch", 0) + 1
    st.session_state.pop("outcome", None)


def relocalize_sample_supplier_names(target_language: str) -> bool:
    """Translate untouched built-in names while preserving user-entered names."""
    source_language = st.session_state.get("_sample_name_language")
    if source_language not in DEFAULT_OFFERS or source_language == target_language:
        return False

    source_names = DEFAULT_OFFERS[source_language]["Supplier"].tolist()
    target_names = DEFAULT_OFFERS[target_language]["Supplier"].tolist()
    translations = dict(zip(source_names, target_names, strict=True))
    frame = st.session_state["offers"].copy()
    localized_names = frame["Supplier"].map(lambda name: translations.get(name, name))
    changed = not localized_names.equals(frame["Supplier"])
    if changed:
        frame["Supplier"] = localized_names
        st.session_state["offers"] = frame
        st.session_state["editor_epoch"] = st.session_state.get("editor_epoch", 0) + 1
        st.session_state["_reoptimize_after_locale_change"] = "outcome" in st.session_state
    st.session_state["_sample_name_language"] = target_language
    return changed


def commit_editor(key):
    delta = st.session_state[key]
    frame = st.session_state["offers"].copy()
    for row, edits in delta.get("edited_rows", {}).items():
        for col, value in edits.items():
            if col != "_id":
                frame.loc[int(row), col] = value
    frame = frame.drop(index=delta.get("deleted_rows", []))
    additions = delta.get("added_rows", [])
    if additions:
        new = pd.DataFrame([{**row, "_id": uuid4().hex[:12]} for row in additions])
        frame = pd.concat([frame, new], ignore_index=True)
    st.session_state["offers"] = frame.reset_index(drop=True)
    st.session_state["editor_epoch"] += 1


if "offers" not in st.session_state:
    load_sample()
elif language_changed:
    relocalize_sample_supplier_names(language)

if language_changed and not st.session_state.get("_currency_user_modified", False):
    st.session_state["currency"] = DEFAULT_CURRENCIES[language]
elif "currency" not in st.session_state:
    st.session_state["currency"] = DEFAULT_CURRENCIES[language]

st.session_state["_active_language"] = language


def mark_currency_modified() -> None:
    st.session_state["_currency_user_modified"] = True


def sync_optimization_mode(widget_key: str) -> None:
    st.session_state["_optimization_mode_code"] = st.session_state[widget_key]


def compact_money(amount: Decimal, currency: str) -> tuple[str, bool]:
    absolute = abs(amount)
    if absolute >= Decimal("1000000000"):
        value = format_number(language, amount / Decimal("1000000000"), decimals=2)
        return f"{value}B {currency}", True
    if absolute >= Decimal("1000000"):
        value = format_number(language, amount / Decimal("1000000"), decimals=2)
        return f"{value}M {currency}", True
    return f"{format_number(language, amount, decimals=2)} {currency}", False


def format_share(amount: Decimal, total: Decimal) -> str:
    if total <= 0 or amount <= 0:
        return "%0,0" if language == "tr" else "0.0%"
    share = amount / total
    if share < Decimal("0.001"):
        return "<%0,1" if language == "tr" else "<0.1%"
    return format_percent(language, share)


def localized_error_details(details: dict[str, object], currency: str) -> dict[str, object]:
    localized: dict[str, object] = {"currency": currency}
    money_keys = {"budget", "minimum_cost", "shortfall"}
    for key, value in details.items():
        if key in money_keys and isinstance(value, (int, float, Decimal)):
            localized[key] = format_number(language, value, decimals=2)
        elif isinstance(value, int):
            localized[key] = format_number(language, value)
        else:
            localized[key] = value
    return localized


POLICY_CODES: tuple[OptimizationMode, ...] = ("lowest_cost", "fastest", "balanced")

if "_optimization_mode_code" not in st.session_state:
    legacy_mode = st.session_state.get("optimization_mode", "lowest_cost")
    st.session_state["_optimization_mode_code"] = (
        legacy_mode if legacy_mode in POLICY_CODES else "lowest_cost"
    )

policy_widget_key = f"optimization_mode_widget_{language}"
if language_changed or policy_widget_key not in st.session_state:
    st.session_state[policy_widget_key] = st.session_state["_optimization_mode_code"]

with st.sidebar:
    st.header(tx("purchase_request"))
    demand = st.number_input(tx("required_quantity"), min_value=1, value=1700, step=50, max_value=10**7, key="demand")
    currency = st.selectbox(
        tx("currency"),
        ["USD", "EUR", "TRY", "GBP"],
        key="currency",
        on_change=mark_currency_modified,
    )
    optimization_mode: OptimizationMode = st.selectbox(
        tx("decision_policy"),
        POLICY_CODES,
        format_func=lambda mode: tx(f"mode_{mode}"),
        key=policy_widget_key,
        on_change=sync_optimization_mode,
        args=(policy_widget_key,),
    )
    st.caption(tx(f"mode_help_{optimization_mode}"))

    enforce_deadline = st.checkbox(tx("enforce_deadline"), value=True, key="enforce_deadline")
    deadline_value = st.number_input(tx("max_lead_time"), min_value=0, max_value=10**6,
                                    value=30, step=1, key="deadline", disabled=not enforce_deadline)
    max_lead_time_days = int(deadline_value) if enforce_deadline else None
    with st.expander(tx("advanced_settings")):
        surplus_cost_per_unit = st.number_input(tx("surplus_cost_per_unit"), min_value=0.0,
            value=0.0, step=0.10, help=tx("surplus_cost_help"), key="surplus_cost")
        delay_value = st.number_input(tx("delay_cost_per_day"), min_value=0.0,
            value=10.0, step=1.0, help=tx("delay_cost_help"), key="delay_cost",
            disabled=optimization_mode != "balanced")
        delay_cost_per_day = delay_value if optimization_mode == "balanced" else 0.0
        enforce_budget = st.checkbox(tx("enforce_budget"), value=False, key="enforce_budget")
        budget_value = st.number_input(tx("budget_limit"), min_value=0.0, value=2000.0,
            step=100.0, key="budget", disabled=not enforce_budget)
        budget_limit = budget_value if enforce_budget else None

st.subheader(tx("supplier_offers"))
st.caption(tx("sample_data_caption"))
edited_offers = st.data_editor(
    st.session_state["offers"],
    num_rows="dynamic",
    width="stretch",
    hide_index=True,
    column_config={
        "_id": None,
        "Supplier": st.column_config.TextColumn(label=tx("supplier"), required=True),
        "MOQ": st.column_config.NumberColumn(label=tx("moq"), min_value=0, step=1, required=True),
        "Unit price": st.column_config.NumberColumn(label=tx("unit_price"), min_value=0.0, step=0.01, format="%.2f", required=True),
        "Shipping": st.column_config.NumberColumn(label=tx("shipping"), min_value=0.0, step=1.0, format="%.2f", required=True),
        "Max capacity": st.column_config.NumberColumn(label=tx("max_capacity"), min_value=0, step=1),
        "Lead time (days)": st.column_config.NumberColumn(label=tx("lead_time_days"), min_value=0, step=1, required=True),
    },
    key=f"supplier_editor_{st.session_state['editor_epoch']}_{language}",
    on_change=commit_editor,
    args=(f"supplier_editor_{st.session_state['editor_epoch']}_{language}",),
)

st.caption(tx("capacity_caption"))
st.caption(tx("precision_note"))
optimize_clicked = st.button(tx("optimize"), type="primary", width="stretch", key="optimize")
st.button(tx("load_sample"), on_click=load_sample, key="load_sample")
settings = dict(optimization_mode=optimization_mode, max_lead_time_days=max_lead_time_days,
                budget_limit=budget_limit, surplus_cost_per_unit=surplus_cost_per_unit,
                delay_cost_per_day=delay_cost_per_day)
fingerprint = sha256((edited_offers.to_json() + repr((demand, settings))).encode()).hexdigest()
reoptimize_after_locale_change = st.session_state.pop("_reoptimize_after_locale_change", False)
if ("outcome" in st.session_state and st.session_state["outcome"][0] != fingerprint
        and not reoptimize_after_locale_change):
    st.session_state.pop("outcome")
    st.info(tx("stale_result"))

if optimize_clicked or reoptimize_after_locale_change:
    try:
        suppliers = tuple(dataframe_to_suppliers(edited_offers))
        result = cached_optimize(int(demand), suppliers, **settings)
        st.session_state["outcome"] = (fingerprint, result, suppliers, None)
    except (InvalidProblem, InfeasibleProblem, SolverFailure) as exc:
        st.session_state["outcome"] = (fingerprint, None, (), (exc.code, exc.details))
    except (ValueError, TypeError, DecimalException):
        st.session_state["outcome"] = (fingerprint, None, (), ("invalid_input", {}))

if "outcome" in st.session_state:
    _, result, suppliers, error = st.session_state["outcome"]
    if error:
        st.error(tx(f"error.{error[0]}", **localized_error_details(error[1], currency)))
    else:
        insights = analyze_decision(
            int(demand),
            suppliers,
            result,
            max_lead_time_days=max_lead_time_days,
        )

        if result.is_optimal:
            st.success(tx(f"optimal_{optimization_mode}"))
        else:
            st.warning(tx("feasible_found"))

        for outlier in insights.price_outliers:
            st.warning(
                tx(
                    "outlier_warning",
                    supplier=outlier.supplier,
                    unit_price=format_number(language, outlier.unit_price, decimals=2),
                    currency=currency,
                    multiple=format_number(language, outlier.multiple, decimals=1),
                    reference_price=format_number(language, outlier.reference_price, decimals=2),
                )
            )
        for outlier in insights.lead_time_outliers:
            warning_key = (
                "lead_outlier_warning"
                if outlier.reference_days is not None and outlier.multiple is not None
                else "lead_outlier_warning_absolute"
            )
            st.warning(
                tx(
                    warning_key,
                    supplier=outlier.supplier,
                    lead_time=format_number(language, outlier.lead_time_days),
                    multiple=format_number(language, outlier.multiple or 0, decimals=1),
                    reference=format_number(language, outlier.reference_days or 0, decimals=1),
                )
            )
        for exclusion in insights.deadline_exclusions:
            st.info(
                tx(
                    "deadline_exclusion",
                    supplier=exclusion.supplier,
                    lead_time=format_number(language, exclusion.lead_time_days),
                    deadline=format_number(language, exclusion.max_lead_time_days),
                )
            )

        unconstrained = None
        if max_lead_time_days is not None:
            try:
                unconstrained = cached_optimize(
                    int(demand),
                    suppliers,
                    optimization_mode=optimization_mode,
                    max_lead_time_days=None,
                    budget_limit=budget_limit,
                    surplus_cost_per_unit=surplus_cost_per_unit,
                    delay_cost_per_day=delay_cost_per_day,
                )
            except (InvalidProblem, InfeasibleProblem, SolverFailure):
                st.info(tx("comparison_unavailable"))

        if unconstrained and (not unconstrained.is_optimal or not result.is_optimal):
            st.caption(tx("comparison_unproven"))

        if unconstrained and unconstrained.is_optimal and result.is_optimal and unconstrained.longest_lead_time_days > result.longest_lead_time_days:
            days_saved = unconstrained.longest_lead_time_days - result.longest_lead_time_days
            premium = result.total_cost - unconstrained.total_cost
            with st.container(border=True):
                st.markdown(f"#### {tx('deadline_impact_title')}")
                impact_key = "deadline_impact" if premium > 0 else ("deadline_saving" if premium < 0 else "deadline_impact_no_premium")
                st.markdown(
                    tx(
                        impact_key,
                        days_saved=format_number(language, days_saved),
                        premium=format_number(language, abs(premium), decimals=2),
                        currency=currency,
                    )
                )
                st.caption(
                    tx(
                        "unconstrained_reference",
                        cost=format_number(language, unconstrained.total_cost, decimals=2),
                        currency=currency,
                        days=format_number(language, unconstrained.longest_lead_time_days),
                    )
                )

        with st.container(border=True):
            st.markdown(f"#### {tx('why_plan')}")
            if insights.critical_suppliers:
                for critical in insights.critical_suppliers:
                    st.markdown(
                        "- "
                        + tx(
                            "critical_capacity",
                            supplier=critical.supplier,
                            capacity=format_number(language, critical.capacity_without_supplier),
                            shortage=format_number(language, critical.shortage_without_supplier),
                        )
                    )
                    if critical.moq > critical.shortage_without_supplier:
                        st.markdown(
                            "- "
                            + tx(
                                "moq_trigger",
                                shortage=format_number(language, critical.shortage_without_supplier),
                                supplier=critical.supplier,
                                moq=format_number(language, critical.moq),
                            )
                        )
                    st.caption(
                        tx(
                            "capacity_feasible",
                            supplier=critical.supplier,
                            capacity=format_number(language, critical.capacity_without_supplier),
                            shortage=format_number(language, critical.shortage_without_supplier),
                        )
                    )
            else:
                st.markdown(tx("no_critical"))
            if insights.dominant_cost:
                dominant = insights.dominant_cost
                st.markdown(
                    "- "
                    + tx(
                        "dominant_cost",
                        supplier=dominant.supplier,
                        share=format_percent(language, dominant.share),
                        amount=format_number(language, dominant.amount, decimals=2),
                        currency=currency,
                    )
                )

        total_value, total_abbreviated = compact_money(result.total_cost, currency)
        top_metrics = st.columns(3)
        top_metrics[0].metric(tx("total_cost"), total_value)
        if total_abbreviated:
            top_metrics[0].caption(
                tx("exact", amount=format_number(language, result.total_cost, decimals=2), currency=currency)
            )
        top_metrics[1].metric(
            tx("longest_lead_time"),
            tx("days", days=format_number(language, result.longest_lead_time_days)),
        )
        top_metrics[2].metric(tx("suppliers_used"), f"{len(result.allocation)}")

        bottom_metrics = st.columns(3)
        effective_value, effective_abbreviated = compact_money(
            result.effective_cost_per_required_unit, currency
        )
        bottom_metrics[0].metric(tx("effective_unit_cost"), effective_value)
        if effective_abbreviated:
            bottom_metrics[0].caption(
                tx(
                    "exact",
                    amount=format_number(language, result.effective_cost_per_required_unit, decimals=2),
                    currency=currency,
                )
            )
        bottom_metrics[1].metric(tx("purchased"), format_number(language, result.total_quantity))
        bottom_metrics[2].metric(tx("surplus"), format_number(language, result.surplus))

        context_notes: list[str] = []
        if max_lead_time_days is not None:
            context_notes.append(
                tx(
                    "deadline_slack",
                    days=format_number(
                        language, max_lead_time_days - result.longest_lead_time_days
                    ),
                )
            )
        if result.budget_limit is not None:
            context_notes.append(
                tx(
                    "budget_remaining",
                    amount=format_number(
                        language,
                        result.budget_limit - result.total_cost,
                        decimals=2,
                    ),
                    currency=currency,
                )
            )
        if context_notes:
            st.caption(" · ".join(context_notes))

        if result.surplus_handling_cost > 0 or optimization_mode == "balanced":
            with st.container(border=True):
                st.markdown(f"#### {tx('decision_cost_breakdown')}")
                decision_columns = st.columns(3)
                decision_columns[0].metric(
                    tx("surplus_handling_cost"),
                    f"{format_number(language, result.surplus_handling_cost, decimals=2)} {currency}",
                )
                decision_columns[1].metric(
                    tx("time_value_cost"),
                    f"{format_number(language, result.time_value_cost, decimals=2)} {currency}",
                )
                decision_columns[2].metric(
                    tx("evaluated_cost"),
                    f"{format_number(language, result.evaluated_cost, decimals=2)} {currency}",
                )
                st.caption(tx("cash_cost_note"))

        allocation = pd.DataFrame(
            [
                {
                    "Supplier": line.supplier,
                    "Row ID": line.row_id,
                    "Quantity": line.quantity,
                    "Unit price": float(line.unit_price),
                    "Product cost": float(line.product_cost),
                    "Shipping": float(line.shipping_cost),
                    "Line total": float(line.line_total),
                    "Cost share": format_share(line.line_total, result.total_cost),
                    "Lead time (days)": line.lead_time_days,
                }
                for line in result.allocation
            ]
        )
        localized_columns = {
            "Row ID": tx("row_id"),
            "Supplier": tx("supplier"),
            "Quantity": tx("quantity"),
            "Unit price": tx("unit_price"),
            "Product cost": tx("product_cost"),
            "Shipping": tx("shipping"),
            "Line total": tx("line_total"),
            "Cost share": tx("cost_share"),
            "Lead time (days)": tx("lead_time_days"),
        }
        display_allocation = allocation.rename(columns=localized_columns)
        for key, attr in (("unit_price", "unit_price"), ("product_cost", "product_cost"),
                          ("shipping", "shipping_cost"), ("line_total", "line_total")):
            display_allocation[tx(key)] = [format_number(language, getattr(line, attr), decimals=2)
                                           + f" {currency}" for line in result.allocation]

        left, right = st.columns([1.45, 1])
        with left:
            st.subheader(tx("recommended_allocation"))
            st.dataframe(
                display_allocation,
                hide_index=True,
                width="stretch",
                column_config={
                    tx("unit_price"): st.column_config.TextColumn(),
                    tx("product_cost"): st.column_config.TextColumn(),
                    tx("shipping"): st.column_config.TextColumn(),
                    tx("line_total"): st.column_config.TextColumn(),
                },
            )
            csv_data = export_csv(result, language, currency)
            st.download_button(
                tx("download_csv"),
                data=csv_data,
                file_name=tx("csv_filename"),
                mime="text/csv",
            )

        with right:
            st.subheader(tx("supplier_cost_contribution"))
            chart_allocation = allocation.copy()
            chart_allocation["Exact cost"] = [format_number(language, line.line_total, decimals=2)
                                              + f" {currency}" for line in result.allocation]
            repeated = chart_allocation["Supplier"].duplicated(keep=False)
            chart_allocation["Supplier"] = [escape(name) + (f" [{row_id}]" if duplicate else "")
                for name, row_id, duplicate in zip(allocation["Supplier"], allocation["Row ID"], repeated)]
            figure = px.bar(
                chart_allocation,
                x="Line total",
                y="Supplier",
                orientation="h",
                color="Supplier",
                text="Cost share",
                hover_data={"Line total": False, "Exact cost": True, "Quantity": ":,", "Cost share": True},
                labels={
                    "Exact cost": tx("line_total"),
                    "Line total": tx("cost_axis", currency=currency),
                    "Supplier": tx("supplier"),
                    "Quantity": tx("quantity"),
                    "Cost share": tx("cost_share"),
                },
            )
            figure.update_traces(textposition="outside", cliponaxis=False)
            figure.update_layout(
                showlegend=False,
                margin=dict(l=10, r=55, t=10, b=10),
                height=min(1600, max(260, 55 * len(allocation))),
                yaxis={"categoryorder": "total ascending"},
            )
            st.plotly_chart(figure, width="stretch")

        with st.expander(tx("what_if"), expanded=False):
            enabled = st.checkbox(tx("run_what_if"), key="run_what_if")
            if enabled:
                lower = max(1, int(demand * 0.5))
                upper = max(lower + 1, int(demand * 1.5))
                scenario_demands = [lower + (upper - lower) * i // 10 for i in range(11)]
                scenario_demands.append(int(demand))
                scenario_demands = sorted(set(scenario_demands))
                st.caption(tx("scenario_policy", policy=tx("mode_" + optimization_mode)))
    
                scenarios: list[dict[str, float | int]] = []
                unavailable = []
                for scenario_demand in scenario_demands:
                    try:
                        scenario = cached_optimize(
                            scenario_demand,
                            suppliers,
                            optimization_mode=optimization_mode,
                            max_lead_time_days=max_lead_time_days,
                            budget_limit=budget_limit,
                            surplus_cost_per_unit=surplus_cost_per_unit,
                            delay_cost_per_day=delay_cost_per_day,
                            time_limit_seconds=0.3,
                        )
                    except (InvalidProblem, InfeasibleProblem, SolverFailure) as exc:
                        unavailable.append(f"{scenario_demand}: " + tx(f"error.{exc.code}", **localized_error_details(exc.details, currency)))
                        scenarios.append({"Demand": scenario_demand, "Policy cost": None, "Exact cost": "", "Surplus": None, "Lead time": None})
                        continue
                    if not scenario.is_optimal:
                        unavailable.append(f"{scenario_demand}: " + tx("feasible_found"))
                    scenarios.append(
                        {
                            "Demand": scenario_demand,
                            "Policy cost": float(scenario.evaluated_cost),
                            "Exact cost": format_number(language, scenario.evaluated_cost, decimals=2) + f" {currency}",
                            "Surplus": scenario.surplus,
                            "Lead time": scenario.longest_lead_time_days,
                        }
                    )
    
                for note in unavailable:
                    st.caption(note)
                if scenarios:
                    scenario_frame = pd.DataFrame(scenarios)
                    cost_chart = px.line(
                        scenario_frame,
                        x="Demand",
                        y="Policy cost",
                        markers=True,
                        hover_data={"Policy cost": False, "Exact cost": True, "Surplus": True, "Lead time": True},
                        labels={
                            "Demand": tx("demand"),
                            "Exact cost": tx("evaluated_cost"),
                            "Policy cost": tx("evaluated_cost") + f" ({currency})",
                            "Surplus": tx("surplus"),
                            "Lead time": tx("longest_lead_time"),
                        },
                    )
                    cost_chart.update_traces(connectgaps=False)
                    cost_chart.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350)
                    for critical in insights.critical_suppliers:
                        threshold = critical.capacity_without_supplier
                        if lower <= threshold <= upper:
                            cost_chart.add_vline(
                                x=threshold,
                                line_dash="dash",
                                line_color="#D97706",
                                annotation_text=escape(translate(
                                    language, "threshold_annotation",
                                    supplier=critical.supplier,
                                    threshold=format_number(language, threshold),
                                )),
                                annotation_position="top left",
                            )
                    st.plotly_chart(cost_chart, width="stretch")
with st.expander(tx("how_model_works")):
    st.markdown(tx("model_explanation"))
    st.markdown(tx("model_limits"))
