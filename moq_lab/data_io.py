"""Strict table parsing and spreadsheet-safe, locale-aware exports."""
import csv
import io
import re
from decimal import Decimal, InvalidOperation
import pandas as pd
from .domain import InvalidProblem, Supplier
from .i18n import translate


def whole(value):
    if isinstance(value, (str, bool)):
        raise InvalidProblem("Whole number required.", code="integer_input")
    try:
        d = Decimal(str(value))
        if not d.is_finite() or d != d.to_integral_value():
            raise ValueError()
        return int(d)
    except (ValueError, TypeError, InvalidOperation):
        raise InvalidProblem("Whole number required.", code="integer_input") from None


def dataframe_to_suppliers(frame):
    result = []
    for index, row in frame.iterrows():
        user_cells = row.drop(labels=["_id"], errors="ignore")
        if all(pd.isna(v) or (isinstance(v, str) and not v.strip()) for v in user_cells):
            continue
        name = row.get("Supplier")
        if not isinstance(name, str) or not name.strip():
            raise InvalidProblem("Every supplier needs a name.", code="supplier_name")
        capacity = row.get("Max capacity")
        row_id = row.get("_id")
        result.append(Supplier(
            name=name, moq=whole(row.get("MOQ")), unit_price=row.get("Unit price"),
            shipping_cost=row.get("Shipping"),
            max_capacity=None if capacity is None or pd.isna(capacity) else whole(capacity),
            lead_time_days=whole(row.get("Lead time (days)")),
            row_id=str(row_id) if pd.notna(row_id) else f"row_{index}",
        ))
    return result


def safe_csv_text(value):
    text = str(value)
    # Ignore leading controls/whitespace when detecting spreadsheet expressions.
    stripped = text.lstrip(' \t\r\n\v\f\ufeff')
    if stripped.startswith(('=', '+', '-', '@')) or text.startswith(('\t', '\r', '\n')):
        return "'" + text
    return text


def markdown_text(value):
    text = str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return re.sub(r'([\\`*_{}\[\]()#+.!|~>\-])', r'\\\1', text).replace('\n', ' ').replace('\r', ' ')


def export_csv(result, language, currency):
    tx = lambda k: translate(language, k)
    out = io.StringIO(newline='')
    writer = csv.writer(out, delimiter=';' if language == 'tr' else ',')
    keys = ['row_id', 'supplier', 'quantity', 'unit_price', 'product_cost', 'shipping',
            'line_total', 'cost_share', 'lead_time_days', 'currency', 'decision_policy', 'demand',
            'purchased', 'surplus', 'longest_lead_time', 'total_cost', 'surplus_handling_cost',
            'time_value_cost', 'evaluated_cost', 'solver_status', 'max_lead_time', 'budget_limit']
    writer.writerow([tx(k) for k in keys])
    def money(x):
        value = format(x, '.2f')
        return value.replace('.', ',') if language == 'tr' else value
    for line in result.allocation:
        share = line.line_total / result.total_cost * 100 if result.total_cost else Decimal(0)
        share_text = format(share, '.6f')
        if language == 'tr':
            share_text = share_text.replace('.', ',')
        writer.writerow([safe_csv_text(line.row_id), safe_csv_text(line.supplier), line.quantity,
                         money(line.unit_price), money(line.product_cost), money(line.shipping_cost),
                         money(line.line_total), share_text, line.lead_time_days, currency,
                         tx('mode_' + result.optimization_mode), result.demand, result.total_quantity,
                         result.surplus, result.longest_lead_time_days, money(result.total_cost),
                         money(result.surplus_handling_cost), money(result.time_value_cost),
                         money(result.evaluated_cost), tx('status_' + result.solver_status.lower()),
                         '' if result.max_lead_time_days is None else result.max_lead_time_days,
                         '' if result.budget_limit is None else money(result.budget_limit)])
    return out.getvalue().encode('utf-8-sig')
