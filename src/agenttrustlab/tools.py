"""Deterministic simulated tools used to test agent behavior without side effects."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Mapping
from time import perf_counter
from typing import Any

from agenttrustlab.contracts import ToolCall, ToolResult

ToolHandler = Callable[[dict[str, Any]], Any | Awaitable[Any]]


class SimulatedTool:
    def __init__(self, name: str, handler: ToolHandler, *, description: str = "") -> None:
        if not name:
            raise ValueError("tool name cannot be empty")
        self.name, self.handler, self.description = name, handler, description

    async def invoke(self, call: ToolCall) -> ToolResult:
        start = perf_counter()
        try:
            output = self.handler(call.arguments)
            if inspect.isawaitable(output):
                output = await output
            return ToolResult(
                call_id=call.id, output=output, latency_ms=(perf_counter() - start) * 1000
            )
        except Exception as exc:  # tools intentionally model failures
            return ToolResult(
                call_id=call.id,
                error=f"{type(exc).__name__}: {exc}",
                latency_ms=(perf_counter() - start) * 1000,
            )


class ToolRegistry:
    def __init__(self, tools: Mapping[str, SimulatedTool] | None = None) -> None:
        self._tools = dict(tools or {})

    def register(self, tool: SimulatedTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"duplicate tool: {tool.name}")
        self._tools[tool.name] = tool

    async def invoke(self, call: ToolCall) -> ToolResult:
        tool = self._tools.get(call.name)
        if tool is None:
            return ToolResult(call_id=call.id, error=f"unknown tool: {call.name}")
        return await tool.invoke(call)

    @property
    def names(self) -> frozenset[str]:
        return frozenset(self._tools)
