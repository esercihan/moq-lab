import csv
import io
from decimal import Decimal
import pandas as pd
import pytest
from moq_lab.data_io import dataframe_to_suppliers, export_csv, markdown_text, safe_csv_text
from moq_lab.domain import Supplier, InvalidProblem
from moq_lab.optimizer import optimize_procurement
from moq_lab.i18n import translate, TRANSLATIONS


@pytest.mark.parametrize('name', ['Çığ,İş','A;B','A"B','A\nB','<script>alert(1)</script>',
    '[click](https://example.com)', '=1+1', '+SUM(A1)', '-1+1', '@SUM(A1)', ' \t=1+1', '\n=1+1'])
@pytest.mark.parametrize('language', ['en','tr'])
def test_csv_preserves_data_with_safe_text_and_exact_totals(name, language):
    r = optimize_procurement(3, [Supplier(name, 5, '.95', '.10', lead_time_days=9)],
                             optimization_mode='balanced', delay_cost_per_day='1.10',
                             surplus_cost_per_unit='.25', budget_limit='4.85')
    payload = export_csv(r, language, 'TRY')
    assert payload.startswith(b'\xef\xbb\xbf')
    rows = list(csv.DictReader(io.StringIO(payload.decode('utf-8-sig')),
                              delimiter=';' if language == 'tr' else ','))
    assert len(rows) == 1
    tx = lambda k: translate(language,k)
    row = rows[0]
    assert row[tx('supplier')] == safe_csv_text(name.strip())
    money = lambda k: Decimal(row[tx(k)].replace(',', '.'))
    assert money('line_total') == money('product_cost') + money('shipping') == r.total_cost
    assert money('total_cost') == Decimal('4.85')
    assert money('surplus_handling_cost') == Decimal('.50')
    assert money('evaluated_cost') == r.evaluated_cost
    assert row[tx('currency')] == 'TRY'
    assert row[tx('decision_policy')] == tx('mode_balanced')
    assert int(row[tx('demand')]) == 3
    assert int(row[tx('purchased')]) == 5
    assert int(row[tx('surplus')]) == 2
    assert int(row[tx('longest_lead_time')]) == 9


def frame(**changes):
    row = {'Supplier':'A','MOQ':1,'Unit price':1.,'Shipping':0.,'Max capacity':None,'Lead time (days)':1}
    row.update(changes)
    return pd.DataFrame([row])


@pytest.mark.parametrize('field,value', [('MOQ',1.5),('MOQ',None),('MOQ','1'),
    ('Lead time (days)',float('nan')),('Max capacity',1.2),('Supplier',None),('Supplier',' ')])
def test_table_rejects_partial_fractional_text_and_missing_fields(field,value):
    with pytest.raises(InvalidProblem): dataframe_to_suppliers(frame(**{field:value}))


def test_blank_row_ignored_and_empty_capacity_unlimited():
    rows = pd.DataFrame([frame().iloc[0].to_dict(), {}])
    parsed = dataframe_to_suppliers(rows)
    assert len(parsed) == 1 and parsed[0].max_capacity is None
    assert optimize_procurement(10, parsed).total_quantity == 10


def test_markdown_is_literal_and_formula_prefix_is_preserved_only_in_export():
    assert markdown_text('[x](url)') == r'\[x\]\(url\)'
    assert '<' not in markdown_text('<b>hey</b>')
    for name in ['=1','+1','-1','@1','  =1','\t=1']:
        assert safe_csv_text(name) == "'" + name
    assert safe_csv_text('normal') == 'normal'


def test_translation_placeholder_parity_and_no_fallback_for_errors():
    from string import Formatter
    assert set(TRANSLATIONS['en']) == set(TRANSLATIONS['tr'])
    for key in TRANSLATIONS['en']:
        fields = lambda s: {name for _,name,_,_ in Formatter().parse(s) if name is not None}
        assert fields(TRANSLATIONS['en'][key]) == fields(TRANSLATIONS['tr'][key])
