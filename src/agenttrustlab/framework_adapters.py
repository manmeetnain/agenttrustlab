"""Optional duck-typed adapters for popular agent runtimes.

Framework packages remain optional; adapters consume their public runtime shapes.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
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
