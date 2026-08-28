import asyncio
from types import SimpleNamespace

from agenttrustlab import EvaluationCase, ToolRegistry
from agenttrustlab.conformance import check_adapter
from agenttrustlab.framework_adapters import (
    AutoGenAdapter,
    CrewAIAdapter,
    GoogleADKAdapter,
    LangGraphAdapter,
    MCPAdapter,
    PydanticAIAdapter,
    SmolagentsAdapter,
)


class Graph:
    async def ainvoke(self, value):
        return {"messages": [*value["messages"], SimpleNamespace(content="ready")]}


class PydanticAgent:
    async def run(self, prompt):
        return SimpleNamespace(output=f"ready: {prompt}", usage=lambda: {"tokens": 3})


class MCPSession:
    async def call_tool(self, name, arguments):
        assert name == "agent.run"
        return SimpleNamespace(
            content=[SimpleNamespace(text=f"ready: {arguments['prompt']}")], isError=False
        )


class Crew:
    def kickoff(self, *, inputs):
        return SimpleNamespace(raw=f"ready: {inputs['prompt']}")


class AutoGenAgent:
    async def run(self, *, task):
        return SimpleNamespace(messages=[SimpleNamespace(content=f"ready: {task}")])


class SmolAgent:
    def run(self, prompt):
        return f"ready: {prompt}"


async def adk_events(prompt):
    yield SimpleNamespace(content=SimpleNamespace(parts=[SimpleNamespace(text=f"ready: {prompt}")]))


def test_langgraph_adapter_and_conformance() -> None:
    adapter = LangGraphAdapter(Graph())
    result = asyncio.run(adapter.run(EvaluationCase(id="lg", prompt="x"), ToolRegistry()))
    assert result.output == "ready"
    assert asyncio.run(check_adapter(adapter)) == ()


def test_pydantic_ai_adapter_and_conformance() -> None:
    adapter = PydanticAIAdapter(PydanticAgent())
    result = asyncio.run(adapter.run(EvaluationCase(id="pai", prompt="x"), ToolRegistry()))
    assert result.output == "ready: x"
    assert asyncio.run(check_adapter(adapter)) == ()


def test_mcp_adapter_and_conformance() -> None:
    adapter = MCPAdapter(MCPSession(), tool_name="agent.run")
    result = asyncio.run(adapter.run(EvaluationCase(id="mcp", prompt="x"), ToolRegistry()))
    assert result.output == "ready: x"
    assert result.metadata["is_error"] is False
    assert asyncio.run(check_adapter(adapter)) == ()


def test_remaining_framework_adapters_conform() -> None:
    adapters = (
        CrewAIAdapter(Crew()),
        AutoGenAdapter(AutoGenAgent()),
        SmolagentsAdapter(SmolAgent()),
        GoogleADKAdapter(adk_events),
    )
    for adapter in adapters:
        assert asyncio.run(check_adapter(adapter)) == ()
