"""Framework adapters. AgentTrustLab controls evaluation, never orchestration."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable

from agenttrustlab.contracts import AgentResult, EvaluationCase
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
        return AgentResult(output=output, metadata={"sdk_result_type": type(run).__name__})
