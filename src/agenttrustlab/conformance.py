"""Shared behavioral contract for every framework adapter."""

from __future__ import annotations

from agenttrustlab.adapters import AgentAdapter
from agenttrustlab.contracts import AgentResult, EvaluationCase
from agenttrustlab.tools import ToolRegistry


async def check_adapter(adapter: AgentAdapter) -> tuple[str, ...]:
    """Return conformance failures instead of raising on the first mismatch."""
    failures: list[str] = []
    if not adapter.name.strip():
        failures.append("adapter name is empty")
    case = EvaluationCase(id="agenttrust.conformance", prompt="Return the word ready.")
    try:
        result = await adapter.run(case, ToolRegistry())
    except Exception as exc:
        return (f"adapter raised {type(exc).__name__}: {exc}",)
    if not isinstance(result, AgentResult):
        failures.append("adapter did not return AgentResult")
    elif not result.output:
        failures.append("adapter returned empty output")
    return tuple(failures)
