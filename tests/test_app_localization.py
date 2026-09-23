"""AppTest interaction tests, including real data-editor widget delta events.

AppTest has no public editor mutation API in the pinned Streamlit version;
WidgetStates is used only for this unsupported editor interaction.
"""
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from moq_lab.i18n import translate

APP_PATH = Path(__file__).parents[1] / 'app.py'


def open_app(language='English'):
    app = AppTest.from_file(APP_PATH, default_timeout=20).run()
    if language != 'English':
        app.selectbox(key='language').select(language).run()
    assert not app.exception
    return app


def policy_selectbox(app):
    language = app.session_state['_active_language']
    return app.selectbox(key=f'optimization_mode_widget_{language}')


def edit_table(app, edits=None, added=None, deleted=None):
    states = app._tree.get_widget_states()
    editor_id = app.dataframe[0].proto.id
    # UnknownElement/data_editor is not included by get_widget_states.
    state = next((s for s in states.widgets if s.id == editor_id), None)
    if state is None:
        state = states.widgets.add()
        state.id = editor_id
    state.string_value = json.dumps({'edited_rows': edits or {}, 'added_rows': added or [],
                                    'deleted_rows': deleted or []})
    app._run(states)
    assert not app.exception
    return app


@pytest.mark.parametrize('language,other,code,other_code', [('English','Türkçe','en','tr'),('Türkçe','English','tr','en')])
def test_language_switch_preserves_edited_table_settings_and_result(language, other, code, other_code):
    app = open_app(language)
    edit_table(app, {'0':{'Supplier':'Özel, "Firma"; İşi','Lead time (days)':5200}})
    original = app.dataframe[0].value.copy()
    app.number_input(key='demand').set_value(1700)
    app.checkbox(key='enforce_budget').check().run()
    app.number_input(key='budget').set_value(2200).run()
    app.number_input(key='surplus_cost').set_value(1).run()
    app.selectbox(key='currency').select('EUR').run()
    app.button(key='optimize').click().run()
    assert not app.exception and app.success
    assert app.metric[0].value == ('1.895,00 EUR' if code == 'tr' else '1,895.00 EUR')
    app.selectbox(key='language').select(other).run()
    assert not app.exception and app.success
    assert app.dataframe[0].value.iloc[0]['Supplier'] == original.iloc[0]['Supplier']
    expected_examples = (
        ['Marmara Tedarik', 'Ege Paketleme']
        if other_code == 'tr' else ['Bora Supply', 'Cedar Works']
    )
    assert app.dataframe[0].value['Supplier'].tolist()[1:] == expected_examples
    assert app.checkbox(key='enforce_budget').value
    assert app.number_input(key='budget').value == 2200
    assert app.number_input(key='surplus_cost').value == 1
    assert app.number_input(key='deadline').value == 30
    assert app.selectbox(key='currency').value == 'EUR'
    assert app.metric[0].label == translate(other_code, 'total_cost')
    assert app.metric[1].value == ('9 gün' if other_code == 'tr' else '9 days')
    assert translate(other_code, 'supplier') in app.dataframe[1].value.columns
    assert app.get('download_button')[0].label == translate(other_code, 'download_csv')
    assert 'Özel' not in str(app.dataframe[1].value)
    specs = json.loads(app.get('plotly_chart')[0].proto.spec)
    assert 'Özel' not in json.dumps(specs, ensure_ascii=False)
    assert translate(other_code, 'supplier') in json.dumps(specs, ensure_ascii=False)


def test_language_switch_localizes_default_sample_policy_and_currency():
    app = open_app()
    policy_selectbox(app).select('balanced').run()
    assert policy_selectbox(app).options[2] == translate('en', 'mode_balanced')
    app.selectbox(key='language').select('Türkçe').run()
    assert app.dataframe[0].value['Supplier'].tolist() == ['Anadolu Ambalaj','Marmara Tedarik','Ege Paketleme']
    assert app.selectbox(key='currency').value == 'TRY'
    assert policy_selectbox(app).value == 'balanced'
    assert policy_selectbox(app).options[2] == translate('tr', 'mode_balanced')
    app.selectbox(key='language').select('English').run()
    assert app.dataframe[0].value['Supplier'].tolist() == ['Atlas Packaging','Bora Supply','Cedar Works']
    assert app.selectbox(key='currency').value == 'USD'
    assert policy_selectbox(app).value == 'balanced'
    assert policy_selectbox(app).options[2] == translate('en', 'mode_balanced')


def test_user_selected_currency_and_custom_supplier_name_survive_language_switch():
    app = open_app()
    app.selectbox(key='currency').select('EUR').run()
    edit_table(app, {'0': {'Supplier': 'My Custom Supplier'}})
    app.selectbox(key='language').select('Türkçe').run()
    assert app.selectbox(key='currency').value == 'EUR'
    assert app.dataframe[0].value['Supplier'].tolist() == [
        'My Custom Supplier', 'Marmara Tedarik', 'Ege Paketleme'
    ]


@pytest.mark.parametrize('language', ['English','Türkçe'])
def test_balanced_policy_and_settings_survive_language_and_policy_changes(language):
    app = open_app(language)
    policy_selectbox(app).select('balanced').run()
    app.number_input(key='delay_cost').set_value(10).run()
    app.button(key='optimize').click().run()
    assert not app.exception and app.success
    result = app.session_state['outcome'][1]
    assert result.time_value_cost == 90 and result.evaluated_cost == 1925
    policy_selectbox(app).select('fastest').run()
    assert not app.metric
    policy_selectbox(app).select('balanced').run()
    assert app.number_input(key='delay_cost').value == 10
    app.number_input(key='delay_cost').set_value(0).run()
    app.button(key='optimize').click().run()
    assert not app.exception and app.success


@pytest.mark.parametrize('change', ['demand','deadline','budget','surplus_cost','delay_cost','policy','price','name'])
def test_input_change_invalidates_previous_result(change):
    app = open_app()
    policy_selectbox(app).select('balanced').run()
    app.checkbox(key='enforce_budget').check().run()
    app.button(key='optimize').click().run()
    assert app.metric
    if change == 'policy': policy_selectbox(app).select('fastest').run()
    elif change == 'price': edit_table(app, {'0':{'Unit price':1.3}})
    elif change == 'name': edit_table(app, {'0':{'Supplier':'Renamed'}})
    else: app.number_input(key=change).set_value(app.number_input(key=change).value + 1).run()
    assert not app.exception and not app.metric
    assert any('Inputs changed' in item.value for item in app.info)


@pytest.mark.parametrize('language', ['English','Türkçe'])
def test_invalid_to_valid_and_translated_persistent_errors(language):
    app = open_app(language)
    app.checkbox(key='enforce_budget').check().run()
    app.number_input(key='budget').set_value(1).run()
    app.button(key='optimize').click().run()
    assert app.error and not app.metric and not app.exception
    other = 'Türkçe' if language == 'English' else 'English'
    app.selectbox(key='language').select(other).run()
    assert ('bütçe' in app.error[0].value if other == 'Türkçe' else 'budget' in app.error[0].value)
    app.checkbox(key='enforce_budget').uncheck().run()
    assert app.number_input(key='budget').value == 1
    app.button(key='optimize').click().run()
    assert app.success and app.metric and not app.error and not app.exception
    app.checkbox(key='enforce_deadline').uncheck().run()
    assert not app.metric
    app.selectbox(key='language').select(language).run()
    assert not app.checkbox(key='enforce_deadline').value


def test_add_delete_blank_partial_and_fractional_rows():
    app = open_app()
    edit_table(app, added=[{'Supplier':'İkinci','MOQ':0,'Unit price':1.0,'Shipping':0.0,
                            'Max capacity':None,'Lead time (days)':0}])
    assert len(app.dataframe[0].value) == 4
    added_id = app.dataframe[0].value.iloc[3]['_id']
    edit_table(app, deleted=[0])
    assert len(app.dataframe[0].value) == 3
    assert app.dataframe[0].value.iloc[2]['_id'] == added_id
    app.button(key='optimize').click().run()
    assert app.success
    edit_table(app, added=[{}])
    app.button(key='optimize').click().run()
    assert app.success and not app.exception
    edit_table(app, added=[{'Supplier':'Partial'}])
    app.button(key='optimize').click().run()
    assert app.error and not app.metric and not app.exception
    edit_table(app, deleted=[4])
    edit_table(app, {'0':{'MOQ':1.5}})
    app.button(key='optimize').click().run()
    assert app.error and not app.metric


@pytest.mark.parametrize('language', ['English','Türkçe'])
def test_reference_5200_days_and_no_deadline_comparison(language):
    app = open_app(language)
    slow_name = app.dataframe[0].value.iloc[0]['Supplier']
    edit_table(app, {'0':{'Lead time (days)':5200}})
    app.button(key='optimize').click().run()
    assert app.session_state['outcome'][1].total_cost == 1895
    assert app.session_state['outcome'][1].longest_lead_time_days == 9
    assert app.warning
    content = ' '.join(x.value for x in app.markdown)
    assert ('5.191' in content if language == 'Türkçe' else '5,191' in content)
    assert '60' in content
    assert slow_name not in str(app.dataframe[1].value)
    app.checkbox(key='enforce_deadline').uncheck().run()
    app.button(key='optimize').click().run()
    assert app.session_state['outcome'][1].total_cost == 1835
    assert app.session_state['outcome'][1].longest_lead_time_days == 5200


def test_what_if_displays_gaps_and_translates_hover():
    app = open_app('Türkçe')
    edit_table(app, {'0': {'Lead time (days)': 5200}})
    app.button(key='optimize').click().run()
    assert len(app.get('plotly_chart')) == 1
    app.checkbox(key='run_what_if').check().run()
    assert not app.exception
    assert len(app.get('plotly_chart')) == 2
    assert any('yalnızca' in c.value or 'altında' in c.value for c in app.caption)
    chart = json.loads(app.get('plotly_chart')[1].proto.spec)
    assert chart['data'][0]['connectgaps'] is False
    assert 'Talep' in json.dumps(chart, ensure_ascii=False)
    app.selectbox(key='language').select('English').run()
    chart = json.loads(app.get('plotly_chart')[1].proto.spec)
    assert 'Demand' in json.dumps(chart)
    assert not app.exception


def test_repeat_optimize_and_rerun_preserve_valid_result():
    app = open_app()
    for _ in range(5):
        app.button(key='optimize').click().run()
        assert app.success and app.session_state['outcome'][1].total_cost == 1835
    app.run()
    assert app.success and app.metric and not app.exception


def test_comparison_retains_all_settings_and_reruns_use_cached_data(monkeypatch):
    import streamlit as st
    import moq_lab.optimizer as optimizer
    st.cache_data.clear()
    real = optimizer.optimize_procurement
    calls = []
    def observe(*args, **kwargs):
        calls.append(kwargs.copy())
        return real(*args, **kwargs)
    monkeypatch.setattr(optimizer, 'optimize_procurement', observe)
    app = open_app()
    policy_selectbox(app).select('balanced').run()
    app.number_input(key='surplus_cost').set_value(2).run()
    app.number_input(key='delay_cost').set_value(4).run()
    app.checkbox(key='enforce_budget').check().run()
    app.button(key='optimize').click().run()
    assert len(calls) == 2
    constrained, comparison = calls
    assert constrained['optimization_mode'] == comparison['optimization_mode'] == 'balanced'
    assert constrained['delay_cost_per_day'] == comparison['delay_cost_per_day'] == 4
    assert constrained['surplus_cost_per_unit'] == comparison['surplus_cost_per_unit'] == 2
    assert constrained['budget_limit'] == comparison['budget_limit']
    assert constrained['max_lead_time_days'] == 30 and comparison['max_lead_time_days'] is None
    app.selectbox(key='language').select('Türkçe').run()
    assert len(calls) == 4
    app.selectbox(key='currency').select('EUR').run()
    app.button(key='optimize').click().run()
    assert len(calls) == 4
    assert not app.exception


@pytest.mark.parametrize('n', [1,10,50,100])
def test_many_supplier_ui_smoke(n):
    import pandas as pd
    rows = [{'Supplier':f'Firma {i}', 'MOQ':1, 'Unit price':float(f'{1+i/100:.2f}'), 'Shipping':0.,
             'Max capacity':2000, 'Lead time (days)':2, '_id':f'offer_{i}'} for i in range(n)]
    app = open_app()
    app.session_state['offers'] = pd.DataFrame(rows)
    app.session_state['editor_epoch'] += 1
    app.run()
    app.button(key='optimize').click().run()
    assert not app.exception and app.success
    assert app.session_state['outcome'][1].total_cost == 1700


@pytest.mark.parametrize('language', ['English','Türkçe'])
@pytest.mark.parametrize('code', ['solver_unknown','model_invalid','result_invalid'])
def test_solver_errors_are_localized_and_never_show_a_plan(monkeypatch, language, code):
    import streamlit as st
    import moq_lab.optimizer as optimizer
    from moq_lab.domain import SolverFailure
    st.cache_data.clear()
    def fail(*args, **kwargs): raise SolverFailure('internal detail withheld', code=code)
    monkeypatch.setattr(optimizer,'optimize_procurement',fail)
    app = open_app(language)
    app.button(key='optimize').click().run()
    lang = 'tr' if language == 'Türkçe' else 'en'
    assert app.error[0].value == translate(lang, 'error.'+code)
    assert not app.metric and not app.success and not app.exception
    assert 'internal detail' not in app.error[0].value
    st.cache_data.clear()


def test_feasible_result_and_comparison_do_not_claim_optimality(monkeypatch):
    import streamlit as st
    import moq_lab.optimizer as optimizer
    from dataclasses import replace
    st.cache_data.clear()
    original = optimizer.optimize_procurement
    def feasible(*args, **kwargs):
        return replace(original(*args, **kwargs), is_optimal=False, solver_status='FEASIBLE', secondary_status='UNKNOWN')
    monkeypatch.setattr(optimizer,'optimize_procurement',feasible)
    app = open_app()
    app.button(key='optimize').click().run()
    assert not app.success and app.metric and not app.exception
    assert app.warning[0].value == translate('en','feasible_found')
    assert any(c.value == translate('en','comparison_unproven') for c in app.caption)
    st.cache_data.clear()


def test_large_totals_table_and_hover_keep_exact_cents():
    import pandas as pd
    app = open_app()
    app.session_state['offers'] = pd.DataFrame([{'Supplier':'Large','MOQ':1,'Unit price':999999999.99,
        'Shipping':.01,'Max capacity':None,'Lead time (days)':0,'_id':'large'}])
    app.session_state['editor_epoch'] += 1
    app.number_input(key='demand').set_value(10**7).run()
    app.button(key='optimize').click().run()
    assert not app.exception and app.success
    expected = '9,999,999,999,900,000.01 USD'
    assert app.dataframe[1].value.iloc[0]['Line total'] == expected
    assert expected in app.get('plotly_chart')[0].proto.spec
    assert any(expected in c.value for c in app.caption)


def test_unknown_solver_outcome_can_be_retried_without_cache_lock(monkeypatch):
    import streamlit as st
    import moq_lab.optimizer as optimizer
    from moq_lab.domain import SolverFailure
    st.cache_data.clear()
    real = optimizer.optimize_procurement
    attempts = []
    def first_unknown(*args, **kwargs):
        attempts.append(1)
        if len(attempts) == 1:
            raise SolverFailure('timeout', code='solver_unknown')
        return real(*args, **kwargs)
    monkeypatch.setattr(optimizer, 'optimize_procurement', first_unknown)
    app = open_app()
    app.button(key='optimize').click().run()
    assert app.error and not app.metric
    app.button(key='optimize').click().run()
    assert app.success and app.metric and not app.exception
    assert len(attempts) == 3  # retry main solve plus deadline counterfactual
    st.cache_data.clear()
