"""Repeatable benchmark, run with: python tools/benchmark.py

Prints JSON; no generated logs or reports are written into the project.
"""
import json
from pathlib import Path
import sys
from time import perf_counter
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from streamlit.testing.v1 import AppTest
from moq_lab.domain import Supplier
from moq_lab.optimizer import optimize_procurement


def run():
    report = []
    for n in [1, 10, 50, 100]:
        offers = [Supplier(f'Offer {i}', 1+i%7, f'{1+(i%13)/10:.2f}', str(i%3),
                           2000 if n == 1 else 200, 1+i%20, f'offer_{i}') for i in range(n)]
        demand = min(1700, 100*n)
        start = perf_counter()
        result = optimize_procurement(demand, offers)
        total = perf_counter() - start
        start = perf_counter()
        for d in [max(1, demand//2) + demand*i//10 for i in range(11)]:
            try:
                optimize_procurement(d, offers, time_limit_seconds=.3)
            except Exception as exc:
                from moq_lab.domain import InvalidProblem, InfeasibleProblem, SolverFailure
                if not isinstance(exc, (InvalidProblem, InfeasibleProblem, SolverFailure)): raise
        what_if = perf_counter() - start
        app = AppTest.from_file(Path(__file__).parents[1]/'app.py', default_timeout=30).run()
        app.session_state['offers'] = pd.DataFrame([{
            'Supplier':s.name,'MOQ':s.moq,'Unit price':float(s.unit_price),
            'Shipping':float(s.shipping_cost),'Max capacity':s.max_capacity,
            'Lead time (days)':s.lead_time_days,'_id':s.row_id} for s in offers])
        app.session_state['editor_epoch'] += 1
        app.number_input(key='demand').set_value(demand).run()
        start = perf_counter()
        app.button(key='optimize').click().run()
        render_solve = perf_counter()-start
        assert not app.exception and app.metric
        start = perf_counter()
        app.selectbox(key='language').select('Türkçe').run()
        redraw = perf_counter()-start
        assert not app.exception and app.metric
        report.append(dict(suppliers=n, model_seconds=round(result.model_seconds,6),
                           solver_seconds=round(result.solver_seconds,6), total_seconds=round(total,6),
                           what_if_11_seconds=round(what_if,6), app_solve_render_seconds=round(render_solve,6),
                           app_language_redraw_seconds=round(redraw,6), status=result.solver_status))
    print(json.dumps(report, indent=2))

if __name__ == '__main__': run()
