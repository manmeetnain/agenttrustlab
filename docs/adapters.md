# Framework adapters

Adapters translate framework behavior into `AgentResult`; they never decide whether behavior is trusted.

## Supported

- Plain Python: synchronous or asynchronous functions returning `str` or `AgentResult`.
- OpenAI Agents SDK: final output, tool calls, tool results, token usage, guardrail counts and interruptions.
- LangGraph: asynchronous compiled-graph invocation with configurable input/output normalization.
- Pydantic AI: asynchronous agent runs with output and usage preservation.
- MCP: connected-session invocation of an MCP-exposed agent tool.

Every adapter must pass the shared conformance contract: non-empty identity, bounded invocation, normalized `AgentResult`, tool-call identity and failure isolation. Framework-specific details remain available as metadata while policies consume portable contracts.

## Planned

CrewAI, AutoGen, Google ADK and smolagents are the next compatibility tier. An adapter is not labelled supported until it passes conformance and trace-parity fixtures in CI.
