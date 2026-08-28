# Active security testing

`--attacks` creates deterministic variants of every declared case. The built-in corpus currently exercises all OWASP Top 10 for Agentic Applications 2026 classes and an explicit MITRE ATLAS exfiltration scenario.

| Control | Built-in scenario |
|---|---|
| ASI01 Agent Goal Hijack | indirect instruction override |
| ASI02 Tool Misuse | destructive argument escalation |
| ASI03 Identity & Privilege Abuse | forged administrator authority |
| ASI04 Agentic Supply Chain | poisoned tool metadata |
| ASI05 Unexpected Code Execution | instruction-bearing shell payload |
| ASI06 Memory & Context Poisoning | persistent privilege mutation |
| ASI07 Insecure Inter-Agent Communication | spoofed supervisor message |
| ASI08 Cascading Failures | unbounded recursive retry |
| ASI09 Human-Agent Trust Exploitation | fabricated audit approval |
| ASI10 Rogue Agents | action concealment request |

Mappings provide traceability, not OWASP, MITRE, NIST or ISO certification. Passing means the agent satisfied the declared cases and policy in the recorded environment.

## Safe execution

Start with simulated tools. Live test environments must use least-privilege credentials, synthetic data, bounded budgets and reversible operations. AgentTrustLab does not sandbox arbitrary Python or convert a production account into a safe test environment.

## Evidence requirements

Every security result retains its attack ID, kind, canonical control, severity, original prompt and mutated prompt. Evidence manifests bind the report digest to the adapter, profile, corpus, runtime platform and known limitations.

