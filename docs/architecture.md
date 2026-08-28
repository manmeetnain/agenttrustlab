# Architecture and milestones

## v0.1 architecture

```text
EvaluationCase + RunConfig
          │
          ▼
  EvaluationEngine ─── ToolRegistry (simulated, no side effects)
          │
          ▼
 AgentAdapter boundary ─── plain Python / OpenAI Agents SDK
          │
          ▼
 AgentResult → SafetyPolicy → ScoreCard → EvaluationReport
                                             ├── JSON
                                             ├── HTML
                                             ├── Rich CLI
                                             └── pytest
```

Contracts are immutable and reject unknown fields. The engine owns timeouts, seeds, repetitions, failure isolation, and determinism comparison. Adapters do not decide whether behavior is acceptable. Policies generate explicit violations; scoring is deterministic and transparent.

## Milestones

- **M0 — Foundation:** packaging, governance, typed contracts, CI and documentation.
- **M1 — Working verification slice (v0.1):** execution, two adapters, simulated tools, policy/scoring, CLI, pytest and reports.
- **M2 — Attack and state lab:** injection corpora, taint/provenance, memory diffing, rollback transaction protocol, replay traces.
- **M3 — Ecosystem adapters:** LangGraph, CrewAI, AutoGen, Pydantic AI, Google ADK, smolagents and MCP conformance kits.
- **M4 — Observability and scale:** OpenTelemetry spans, distributed suites, FastAPI result service, statistical regression gates.
- **M5 — Trust profiles:** signed reports, policy packs, supply-chain attestations and benchmark governance.

OpenTelemetry and FastAPI are optional dependencies until M4; keeping them out of the kernel preserves a small and safe default installation.

