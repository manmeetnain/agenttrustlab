"""Framework-neutral trace normalization and optional OpenTelemetry export."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agenttrustlab.contracts import AgentResult, EvaluationReport


class TraceKind(StrEnum):
    AGENT = "agent"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    EVIDENCE = "evidence"
    POLICY = "policy"


class TraceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    sequence: int = Field(ge=0)
    kind: TraceKind
    name: str
    attributes: dict[str, Any] = Field(default_factory=dict)


def normalize_result(result: AgentResult) -> tuple[TraceEvent, ...]:
    events: list[TraceEvent] = [
        TraceEvent(
            sequence=0,
            kind=TraceKind.AGENT,
            name="agent.output",
            attributes={"output": result.output, "cost_usd": result.cost_usd},
        )
    ]
    for call in result.tool_calls:
        events.append(
            TraceEvent(
                sequence=len(events),
                kind=TraceKind.TOOL_CALL,
                name=call.name,
                attributes={"call_id": call.id, "arguments": call.arguments},
            )
        )
    for tool_result in result.tool_results:
        events.append(
            TraceEvent(
                sequence=len(events),
                kind=TraceKind.TOOL_RESULT,
                name="tool.result",
                attributes={
                    "call_id": tool_result.call_id,
                    "error": tool_result.error,
                    "latency_ms": tool_result.latency_ms,
                },
            )
        )
    for evidence in result.evidence:
        events.append(
            TraceEvent(
                sequence=len(events),
                kind=TraceKind.EVIDENCE,
                name=evidence.source,
                attributes={"content": evidence.content, **evidence.metadata},
            )
        )
    return tuple(events)


def emit_report_spans(report: EvaluationReport) -> None:
    """Export report/run spans when the OpenTelemetry extra is installed."""
    try:
        from opentelemetry import trace
    except ImportError as exc:
        raise ImportError("Install AgentTrustLab with the 'otel' extra") from exc
    tracer = trace.get_tracer("agenttrustlab", "0.1.0")
    with tracer.start_as_current_span("agenttrustlab.evaluate") as root:
        root.set_attribute("agenttrustlab.report_id", str(report.id))
        root.set_attribute("agenttrustlab.adapter", report.adapter)
        root.set_attribute("agenttrustlab.passed", report.passed)
        for run in report.runs:
            with tracer.start_as_current_span("agenttrustlab.case") as span:
                span.set_attribute("agenttrustlab.case_id", run.case_id)
                span.set_attribute("agenttrustlab.status", run.status.value)
                span.set_attribute("agenttrustlab.latency_ms", run.latency_ms)
