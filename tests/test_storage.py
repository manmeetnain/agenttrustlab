import asyncio

from agenttrustlab import EvaluationCase, EvaluationEngine, PlainPythonAdapter
from agenttrustlab.storage import ReportStore


def make_report():
    return asyncio.run(
        EvaluationEngine().evaluate(
            PlainPythonAdapter(lambda case, tools: "ok"),
            [EvaluationCase(id="stored", prompt="x")],
        )
    )


def test_report_store_round_trip_and_replace(tmp_path) -> None:
    store = ReportStore(tmp_path / "reports.db")
    report = make_report()
    assert store.put(report) == str(report.id)
    assert store.put(report) == str(report.id)
    assert store.get(str(report.id)) == report
    assert store.get("missing") is None
    assert store.list()[0]["passed"] == 1
