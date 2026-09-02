# We ran 120 agent trust checks without calling a model

AI agent teams can usually show that a demo works. They struggle to show why it should still be trusted after tool misuse, forged approval, hostile retrieved content, retry loops or memory poisoning.

AgentTrustLab approaches that gap like pytest: define intended behavior once, run the agent through normal and adversarial cases, and fail CI with reproducible evidence when behavior diverges.

For the first public benchmark, the same 20 YAML files expanded into 30 cases. Each case ran twice against an intentionally vulnerable fixture and a hardened fixture. The vulnerable agent failed all 60 runs. The hardened fixture passed all 60. Both were deterministic.

The useful result is not the perfect contrast—it is the audit trail. Every failure identifies the violated policy or trace expectation, severity, remediation, normalized tool calls, budgets and reproduction configuration. The same run emits JSON, HTML, JUnit, SARIF and Markdown.

This is deliberately a simulated benchmark. It costs nothing, needs no credentials and makes no claim about live-model quality. Its purpose is to let contributors reproduce the full verification path before we publish external MCP and framework benchmarks.

AgentTrustLab is Apache-2.0, local-first and created by Manmeet Nain (@manmeetnain).
