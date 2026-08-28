"""Framework adapters. AgentTrustLab controls evaluation, never orchestration."""

from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable

from agenttrustlab.contracts import AgentResult, EvaluationCase, ToolCall, ToolResult
from agenttrustlab.tools import ToolRegistry


@runtime_checkable
class AgentAdapter(Protocol):
    name: str

    async def run(self, case: EvaluationCase, tools: ToolRegistry) -> AgentResult: ...


AgentFunction = Callable[
    [EvaluationCase, ToolRegistry], AgentResult | Awaitable[AgentResult] | str | Awaitable[str]
]


class PlainPythonAdapter:
    name = "plain-python"

    def __init__(self, agent: AgentFunction) -> None:
        self.agent = agent

    async def run(self, case: EvaluationCase, tools: ToolRegistry) -> AgentResult:
        value: Any = self.agent(case, tools)
        if inspect.isawaitable(value):
            value = await value
        if isinstance(value, str):
            return AgentResult(output=value)
        if not isinstance(value, AgentResult):
            raise TypeError("plain-Python agents must return str or AgentResult")
        return value


class OpenAIAgentsAdapter:
    """Optional adapter for an ``agents.Agent`` instance.

    Importing AgentTrustLab does not require the OpenAI Agents SDK.
    """

    name = "openai-agents"

    def __init__(self, agent: Any, *, runner: Any | None = None) -> None:
        try:
            from agents import Runner
        except ImportError as exc:
            raise ImportError("Install AgentTrustLab with the 'openai' extra") from exc
        self.agent = agent
        self.runner = runner or Runner

    async def run(self, case: EvaluationCase, tools: ToolRegistry) -> AgentResult:
        del tools  # SDK tools belong to the wrapped agent; traces are normalized below.
        run = await self.runner.run(self.agent, case.prompt)
        output = str(run.final_output)
        calls: list[ToolCall] = []
        results: list[ToolResult] = []
        for item in run.new_items:
            item_type = getattr(item, "type", "")
            if item_type == "tool_call_item":
                raw = item.raw_item
                raw_arguments = (
                    raw.get("arguments", {})
                    if isinstance(raw, dict)
                    else getattr(raw, "arguments", {})
                )
                if isinstance(raw_arguments, str):
                    try:
                        arguments = json.loads(raw_arguments)
                    except json.JSONDecodeError:
                        arguments = {"_raw": raw_arguments}
                elif isinstance(raw_arguments, dict):
                    arguments = dict(raw_arguments)
                else:
                    arguments = {"_value": raw_arguments}
                calls.append(
                    ToolCall(
                        id=str(item.call_id or f"call-{len(calls)}"),
                        name=str(item.tool_name or "unknown"),
                        arguments=arguments,
                    )
                )
            elif item_type == "tool_call_output_item":
                results.append(
                    ToolResult(
                        call_id=str(item.call_id or f"call-{len(results)}"),
                        output=item.output,
                    )
                )
        usage = {
            "requests": sum(response.usage.requests for response in run.raw_responses),
            "input_tokens": sum(response.usage.input_tokens for response in run.raw_responses),
            "output_tokens": sum(response.usage.output_tokens for response in run.raw_responses),
            "total_tokens": sum(response.usage.total_tokens for response in run.raw_responses),
        }
        metadata = {
            "sdk_result_type": type(run).__name__,
            "usage": usage,
            "input_guardrails": len(run.input_guardrail_results),
            "output_guardrails": len(run.output_guardrail_results),
            "tool_input_guardrails": len(run.tool_input_guardrail_results),
            "tool_output_guardrails": len(run.tool_output_guardrail_results),
            "interruptions": len(getattr(run, "interruptions", ())),
        }
        return AgentResult(
            output=output,
            tool_calls=tuple(calls),
            tool_results=tuple(results),
            metadata=metadata,
        )
