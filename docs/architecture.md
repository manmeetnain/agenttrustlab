# Architecture

AgentTrustLab separates scenario intent, execution, verification evidence and presentation. It tests existing agents and does not become their workflow engine.

```text
YAML / Python scenario
          │
          ▼
Versioned ScenarioFile ── expand adversarial variants ── JSON Schema
          │
          ▼
EvaluationCase + RunConfig
          │
          ▼
EvaluationEngine ─── ToolRegistry ─── state / rollback journal
          │
          ▼
AgentAdapter boundary
  plain Python / OpenAI / MCP / framework integrations
          │
          ▼
AgentResult + normalized trace
          │
          ├── policy decisions
          ├── trace assertions and diffs
          ├── deterministic scoring
          └── release profile gates
          │
          ▼
EvaluationReport + signed EvidenceManifest
          ├── Rich CLI / pytest
          ├── JSON / HTML / Markdown
          ├── SQLite / FastAPI
          └── local evidence cockpit
```

## Stable boundaries

- **Scenario contracts** describe intended behavior without framework dependencies.
- **Adapters** normalize execution but never decide trust.
- **The engine** owns seeds, timeout, repetitions, isolation and determinism comparison.
- **Policies and assertions** generate explicit, versioned reasons.
- **Profiles** turn objective measurements into explainable release gates.
- **Evidence manifests** bind reports to policy, corpus, configuration and limitations.
- **Presentation layers** consume serialized reports and never invent verdict data.

All core contracts are immutable and reject unknown fields. Optional framework, observability, signing and server dependencies remain outside the minimal verification kernel where practical.
