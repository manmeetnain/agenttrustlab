# Compatibility roadmap

Adapters are accepted only when they preserve trace evidence, expose tool calls, normalize errors, support bounded cancellation, and pass the shared conformance suite.

| Framework | Status | Target |
|---|---|---|
| Plain Python | supported | v0.1 |
| OpenAI Agents SDK | initial adapter | v0.1 |
| LangGraph | planned | v0.2 |
| Pydantic AI | planned | v0.2 |
| MCP | planned | v0.2 |
| CrewAI | planned | v0.3 |
| AutoGen | planned | v0.3 |
| Google ADK | planned | v0.3 |
| smolagents | planned | v0.3 |

Rollback evaluation in v0.2 will use a framework-neutral transaction journal: snapshot, action, invariant check, compensating action, post-rollback check. AgentTrustLab will verify the protocol without becoming the workflow engine.

