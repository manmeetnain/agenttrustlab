# Framework adapters

Adapters translate framework behavior into `AgentResult`; they never decide whether behavior is trusted.

## Compatibility matrix

| Integration | Maturity | Current normalized surface |
|---|---|---|
| Plain Python | Verified | Sync/async output and complete `AgentResult` |
| OpenAI Agents SDK | Conformant foundation | Output, tool calls/results, usage and guardrail metadata |
| LangGraph | Experimental | Async graph input/output |
| Pydantic AI | Experimental | Agent output and usage |
| MCP | Conformant foundation | MCP v2 text/structured results and errors |
| CrewAI | Experimental | Crew kickoff raw output |
| AutoGen | Experimental | Final task message |
| Google ADK | Experimental | Session-owned event text |
| smolagents | Experimental | Sync/async run output |

Experimental means that the adapter boundary exists and passes minimal normalized-output fixtures. It does not yet promise trace parity, bounded cancellation or compatibility with every framework release.

## Compatibility policy

Adapters are duck typed so installing AgentTrustLab never installs an orchestration framework. Promotion requires increasingly strong evidence:

1. **Experimental:** normalized result fixture.
2. **Conformant:** output, error, timeout, cancellation and tool-trace fixtures.
3. **Verified:** pinned real-framework CI.
4. **Benchmark-grade:** published reproducible benchmark usage.

Framework-specific details remain metadata while portable policies consume stable contracts.

## Launch-critical dependencies

The `openai` extra is tested against the real `openai-agents>=0.22,<1` result contract. AgentTrustLab delegates orchestration to `Runner.run`, then normalizes final output, tool calls, tool results, usage, guardrail results and approval interruptions. Deterministic conformance does not call a paid model; live-model tests belong in credentialed, budget-limited integration suites.

The `mcp` extra targets MCP Python SDK `>=2.1,<3`. It accepts standard text content and MCP v2 structured content. A structured payload shaped as an `AgentResult` preserves tool calls and evidence; protocol `isError` results become engine-visible errors rather than successful text. MCP v1 `FastMCP` examples are intentionally not presented as current v2 support.
