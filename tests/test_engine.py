import asyncio

from agenttrustlab import (
    AgentResult,
    EvaluationCase,
    EvaluationEngine,
    ExpectedOutcome,
    PlainPythonAdapter,
    RunConfig,
    ToolCall,
)
from agenttrustlab.contracts import RunStatus


def run(coro):
    return asyncio.run(coro)


def test_passing_case_and_determinism() -> None:
    async def agent(case, tools):
        return AgentResult(output="Paris", cost_usd=0.01)

    case = EvaluationCase(
        id="capital",
        prompt="Capital of France?",
        expected=ExpectedOutcome(contains=("Paris",), max_cost_usd=0.02),
    )
    report = run(
        EvaluationEngine().evaluate(PlainPythonAdapter(agent), [case], RunConfig(repetitions=2))
    )
    assert report.passed
    assert report.deterministic
    assert len(report.runs) == 2


def test_failure_and_policy_violation() -> None:
    def agent(case, tools):
        return AgentResult(
            output="wrong", tool_calls=(ToolCall(id="1", name="delete", arguments={}),)
        )

    case = EvaluationCase(
        id="safe",
        prompt="answer",
        expected=ExpectedOutcome(contains=("right",), forbidden_tools=("delete",)),
    )
    report = run(EvaluationEngine().evaluate(PlainPythonAdapter(agent), [case]))
    assert report.runs[0].status == RunStatus.FAILED
    assert "forbidden tool" in report.runs[0].violations[0]


def test_timeout_is_isolated() -> None:
    async def agent(case, tools):
        await asyncio.sleep(0.05)
        return "late"

    report = run(
        EvaluationEngine().evaluate(
            PlainPythonAdapter(agent),
            [EvaluationCase(id="timeout", prompt="x")],
            RunConfig(timeout_seconds=0.001),
        )
    )
    assert report.runs[0].status == RunStatus.ERROR
    assert report.runs[0].error == "agent timed out"


def test_adapter_error_is_recorded() -> None:
    def agent(case, tools):
        return object()

    report = run(
        EvaluationEngine().evaluate(
            PlainPythonAdapter(agent), [EvaluationCase(id="bad", prompt="x")]
        )
    )
    assert report.runs[0].status == RunStatus.ERROR
