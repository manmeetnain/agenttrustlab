"""Optional duck-typed adapters for popular agent runtimes.

Framework packages remain optional; adapters consume their public runtime shapes.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterable, Callable
from typing import Any

from agenttrustlab.contracts import AgentResult, EvaluationCase
from agenttrustlab.tools import ToolRegistry


def _content(value: Any) -> str:
    if isinstance(value, str):
        return value
    content = getattr(value, "content", None)
    if isinstance(content, str):
        return content
    text = getattr(value, "text", None)
    if isinstance(text, str):
        return text
    return str(value)


class LangGraphAdapter:
    name = "langgraph"

    def __init__(
        self,
        graph: Any,
        *,
        input_factory: Callable[[str], Any] | None = None,
        output_factory: Callable[[Any], str] | None = None,
    ) -> None:
        self.graph = graph
        self.input_factory = input_factory or (
            lambda prompt: {"messages": [{"role": "user", "content": prompt}]}
        )
        self.output_factory = output_factory or self._default_output

    @staticmethod
    def _default_output(value: Any) -> str:
        if isinstance(value, dict) and value.get("messages"):
            return _content(value["messages"][-1])
        return _content(value)

    async def run(self, case: EvaluationCase, tools: ToolRegistry) -> AgentResult:
        del tools
        value = self.graph.ainvoke(self.input_factory(case.prompt))
        if inspect.isawaitable(value):
            value = await value
        return AgentResult(output=self.output_factory(value), metadata={"framework": "langgraph"})


class PydanticAIAdapter:
    name = "pydantic-ai"

    def __init__(self, agent: Any) -> None:
        self.agent = agent

    async def run(self, case: EvaluationCase, tools: ToolRegistry) -> AgentResult:
        del tools
        value = self.agent.run(case.prompt)
        if inspect.isawaitable(value):
            value = await value
        output = getattr(value, "output", getattr(value, "data", value))
        usage_method = getattr(value, "usage", None)
        usage = usage_method() if callable(usage_method) else usage_method
        return AgentResult(
            output=_content(output),
            metadata={"framework": "pydantic-ai", "usage": str(usage) if usage else None},
        )


class MCPAdapter:
    """Evaluate an MCP-exposed agent tool through a connected client session."""

    name = "mcp"

    def __init__(self, session: Any, *, tool_name: str, prompt_argument: str = "prompt") -> None:
        self.session = session
        self.tool_name = tool_name
        self.prompt_argument = prompt_argument

    async def run(self, case: EvaluationCase, tools: ToolRegistry) -> AgentResult:
        del tools
        response = self.session.call_tool(
            self.tool_name, arguments={self.prompt_argument: case.prompt}
        )
        if inspect.isawaitable(response):
            response = await response
        blocks = getattr(response, "content", ())
        output = "\n".join(_content(block) for block in blocks)
        return AgentResult(
            output=output,
            metadata={
                "framework": "mcp",
                "tool_name": self.tool_name,
                "is_error": bool(getattr(response, "isError", False)),
            },
        )


class CrewAIAdapter:
    """Evaluate a CrewAI ``Crew`` through its stable ``kickoff`` surface."""

    name = "crewai"

    def __init__(self, crew: Any, *, input_name: str = "prompt") -> None:
        self.crew = crew
        self.input_name = input_name

    async def run(self, case: EvaluationCase, tools: ToolRegistry) -> AgentResult:
        del tools
        value = self.crew.kickoff(inputs={self.input_name: case.prompt})
        if inspect.isawaitable(value):
            value = await value
        return AgentResult(
            output=_content(getattr(value, "raw", value)), metadata={"framework": "crewai"}
        )


class AutoGenAdapter:
    """Evaluate a modern AutoGen agent through ``run(task=...)``."""

    name = "autogen"

    def __init__(self, agent: Any) -> None:
        self.agent = agent

    async def run(self, case: EvaluationCase, tools: ToolRegistry) -> AgentResult:
        del tools
        value = self.agent.run(task=case.prompt)
        if inspect.isawaitable(value):
            value = await value
        messages = getattr(value, "messages", ())
        output = _content(messages[-1]) if messages else _content(value)
        return AgentResult(output=output, metadata={"framework": "autogen"})


class SmolagentsAdapter:
    """Evaluate a smolagents agent through its ``run`` API."""

    name = "smolagents"

    def __init__(self, agent: Any) -> None:
        self.agent = agent

    async def run(self, case: EvaluationCase, tools: ToolRegistry) -> AgentResult:
        del tools
        value = self.agent.run(case.prompt)
        if inspect.isawaitable(value):
            value = await value
        return AgentResult(output=_content(value), metadata={"framework": "smolagents"})


class GoogleADKAdapter:
    """Evaluate Google ADK via an application-owned asynchronous event stream."""

    name = "google-adk"

    def __init__(self, invoke: Callable[[str], AsyncIterable[Any]]) -> None:
        self.invoke = invoke

    async def run(self, case: EvaluationCase, tools: ToolRegistry) -> AgentResult:
        del tools
        parts: list[str] = []
        async for event in self.invoke(case.prompt):
            content = getattr(event, "content", None)
            for part in getattr(content, "parts", ()):
                text = _content(part)
                if text:
                    parts.append(text)
        return AgentResult(output="\n".join(parts), metadata={"framework": "google-adk"})
