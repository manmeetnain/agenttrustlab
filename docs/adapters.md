# Framework adapters

Adapters translate framework behavior into `AgentResult`; they never decide whether behavior is trusted.

## Supported

- Plain Python: synchronous or asynchronous functions returning `str` or `AgentResult`.
- OpenAI Agents SDK: final output, tool calls, tool results, token usage, guardrail counts and interruptions.
- LangGraph: asynchronous compiled-graph invocation with configurable input/output normalization.
- Pydantic AI: asynchronous agent runs with output and usage preservation.
- MCP: connected-session invocation of an MCP-exposed agent tool.
- CrewAI: crew kickoff with normalized raw output.
- AutoGen: task execution with normalized final messages.
- Google ADK: session-owned asynchronous event streams with normalized text parts.
- smolagents: synchronous or asynchronous agent runs.

Every adapter must pass the shared conformance contract: non-empty identity, bounded invocation, normalized `AgentResult`, tool-call identity and failure isolation. Framework-specific details remain available as metadata while policies consume portable contracts.

## Compatibility policy

Adapters are duck typed so installing AgentTrustLab never installs an orchestration framework. Each supported surface passes the same conformance contract in CI. Optional real-framework integration matrices will be version-pinned as these ecosystems stabilize; their native objects remain the responsibility of the application that owns them.
