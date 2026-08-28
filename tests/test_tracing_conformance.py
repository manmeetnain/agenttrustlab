import asyncio

from agenttrustlab import AgentResult, EvaluationCase, EvaluationEngine, PlainPythonAdapter
from agenttrustlab.conformance import check_adapter
from agenttrustlab.contracts import Evidence, ToolCall, ToolResult
from agenttrustlab.tracing import TraceKind, emit_report_spans, normalize_result


def test_normalized_trace_has_stable_sequence() -> None:
    result = AgentResult(
        output="done",
        tool_calls=(ToolCall(id="1", name="lookup"),),
        tool_results=(ToolResult(call_id="1", output="ok"),),
        evidence=(Evidence(source="record", content="verified"),),
    )
    events = normalize_result(result)
    assert [event.sequence for event in events] == list(range(4))
    assert [event.kind for event in events] == [
        TraceKind.AGENT,
        TraceKind.TOOL_CALL,
        TraceKind.TOOL_RESULT,
        TraceKind.EVIDENCE,
    ]


def test_plain_python_adapter_conforms() -> None:
    failures = asyncio.run(check_adapter(PlainPythonAdapter(lambda case, tools: "ready")))
    assert failures == ()


def test_conformance_reports_adapter_failure() -> None:
    def broken(case, tools):
        raise RuntimeError("broken")

    failures = asyncio.run(check_adapter(PlainPythonAdapter(broken)))
    assert "RuntimeError" in failures[0]


def test_otel_export_accepts_report() -> None:
    report = asyncio.run(
        EvaluationEngine().evaluate(
            PlainPythonAdapter(lambda case, tools: "ready"), [EvaluationCase(id="otel", prompt="x")]
        )
    )
    emit_report_spans(report)
