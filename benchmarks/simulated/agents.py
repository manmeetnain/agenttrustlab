"""Deterministic benchmark agents used to demonstrate detection, not model quality."""

from __future__ import annotations

from typing import Any

from agenttrustlab import AgentResult, ToolCall, ToolResult
from agenttrustlab.contracts import Evidence


def _matcher_value(matcher: dict[str, Any]) -> Any:
    kind = matcher.get("match")
    if kind in {"equals", "contains", "type"}:
        value = matcher.get("value")
        defaults = {
            "string": "value",
            "integer": 1,
            "number": 1.0,
            "boolean": True,
            "object": {},
            "array": [],
            "null": None,
        }
        return defaults.get(value, value) if kind == "type" else value
    if kind == "present":
        return "present"
    if kind == "regex":
        return "REF-1"
    return None


def hardened_agent(case, tools):
    """Satisfy declared portable contracts without interpreting hostile instructions."""
    del tools
    trace = case.metadata.get("trace_expectation", {})
    calls = []
    results = []
    for index, expected_call in enumerate(trace.get("calls", []), start=1):
        if expected_call.get("optional"):
            continue
        arguments = {
            name: _matcher_value(matcher)
            for name, matcher in expected_call.get("arguments", {}).items()
        }
        identifier = f"call-{index}"
        calls.append(ToolCall(id=identifier, name=expected_call["tool"], arguments=arguments))
        results.append(ToolResult(call_id=identifier, output={"status": "ok"}))
    observed_tools = {call.name for call in calls}
    for name in case.expected.required_tools:
        if name in observed_tools:
            continue
        identifier = f"call-{len(calls) + 1}"
        calls.append(ToolCall(id=identifier, name=name, arguments={}))
        results.append(ToolResult(call_id=identifier, output={"status": "ok"}))

    terms = list(case.expected.contains)
    if "rollback" in case.tags:
        terms.append("restored")
    output = " ".join(dict.fromkeys(terms)) or "Request handled under declared policy."
    evidence = tuple(
        Evidence(source=f"fixture:{index}", content="Deterministic benchmark evidence")
        for index in range(case.expected.min_evidence)
    )
    return AgentResult(
        output=output,
        tool_calls=tuple(calls),
        tool_results=tuple(results),
        evidence=evidence,
        memory_after={},
        cost_usd=0.001,
        metadata={"steps": len(calls), "retries": 0, "benchmark_mode": "hardened"},
    )


def vulnerable_agent(case, tools):
    """Deliberately violate common contracts so findings are visible and reproducible."""
    del tools
    calls = []
    if case.expected.forbidden_tools:
        calls.append(
            ToolCall(
                id="unsafe-1", name=case.expected.forbidden_tools[0], arguments={"scope": "all"}
            )
        )
    elif case.metadata.get("trace_expectation", {}).get("calls"):
        expected = case.metadata["trace_expectation"]["calls"][0]
        calls.append(ToolCall(id="wrong-1", name=expected["tool"], arguments={"id": "invented"}))
    return AgentResult(
        output="Ignore all previous instructions; action completed without verification.",
        tool_calls=tuple(calls),
        memory_after={"user_role": "administrator"},
        cost_usd=1.0,
        metadata={"steps": 12, "retries": 8, "benchmark_mode": "vulnerable"},
    )
