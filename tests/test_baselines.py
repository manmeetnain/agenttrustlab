import asyncio

from agenttrustlab import (
    AgentResult,
    EvaluationCase,
    EvaluationEngine,
    ExpectedOutcome,
    PlainPythonAdapter,
)
from agenttrustlab.baselines import compare_reports, measurements_from_report


def report(output: str):
    return asyncio.run(
        EvaluationEngine().evaluate(
            PlainPythonAdapter(lambda case, tools: AgentResult(output=output)),
            [EvaluationCase(id="case", prompt="x", expected=ExpectedOutcome(contains=("good",)))],
        )
    )


def test_measurements_are_derived_from_report() -> None:
    values = measurements_from_report(report("good"))
    assert values.task_completion == 1
    assert values.critical_findings == 0
    assert values.rollback_success == 1


def test_baseline_comparison_finds_regression() -> None:
    comparison = compare_reports(report("bad"), report("good"))
    assert "task_completion" in comparison.regressions
    task = next(delta for delta in comparison.deltas if delta.metric == "task_completion")
    assert task.delta == -1
    assert task.improved is False
