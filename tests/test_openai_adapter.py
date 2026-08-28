import asyncio
from types import SimpleNamespace

from agenttrustlab import EvaluationCase, ToolRegistry
from agenttrustlab.adapters import OpenAIAgentsAdapter


class FakeRunner:
    @staticmethod
    async def run(agent, prompt):
        del agent, prompt
        usage = SimpleNamespace(requests=1, input_tokens=10, output_tokens=4, total_tokens=14)
        call = SimpleNamespace(
            type="tool_call_item",
            raw_item={"arguments": '{"order_id":"A1"}'},
            call_id="call-1",
            tool_name="lookup_order",
        )
        result = SimpleNamespace(
            type="tool_call_output_item", call_id="call-1", output={"status": "ok"}
        )
        return SimpleNamespace(
            final_output="complete",
            new_items=[call, result],
            raw_responses=[SimpleNamespace(usage=usage)],
            input_guardrail_results=[],
            output_guardrail_results=[],
            tool_input_guardrail_results=[],
            tool_output_guardrail_results=[],
            interruptions=[],
        )


def test_openai_adapter_normalizes_tools_usage_and_guardrails() -> None:
    adapter = OpenAIAgentsAdapter(object(), runner=FakeRunner)
    result = asyncio.run(adapter.run(EvaluationCase(id="sdk", prompt="x"), ToolRegistry()))
    assert result.output == "complete"
    assert result.tool_calls[0].name == "lookup_order"
    assert result.tool_calls[0].arguments == {"order_id": "A1"}
    assert result.tool_results[0].output == {"status": "ok"}
    assert result.metadata["usage"]["total_tokens"] == 14
