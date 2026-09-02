# Product and execution roadmap

AgentTrustLab combines a deep, framework-neutral verification kernel with a focused adoption wedge: reviewable YAML scenarios, trace-level failure explanations, public benchmarks and CI-ready regression tests.

## Product promise

Define intended behavior once, run normal and adversarial cases against an agent or MCP server, and receive reproducible evidence showing exactly where the behavior diverged.

AgentTrustLab does not orchestrate agents and does not claim that a passing suite proves universal safety.

## Compatibility maturity

Integrations use evidence-backed maturity labels:

| Level | Requirement |
|---|---|
| Experimental | Produces a normalized result through a documented boundary |
| Conformant | Passes output, error, timeout, cancellation and tool-trace fixtures |
| Verified | Runs in CI against a pinned real framework release |
| Benchmark-grade | Used in a published, independently reproducible benchmark |

Current status:

| Integration | Status | Next proof |
|---|---|---|
| Plain Python | Verified | Expand real-world target fixtures |
| OpenAI Agents SDK | Conformant foundation | Pinned real-SDK matrix and cancellation |
| LangGraph | Experimental | Real graph trace-parity suite |
| Pydantic AI | Experimental | Real agent usage and trace suite |
| MCP | Experimental | Protocol fixture and public benchmark |
| CrewAI | Experimental | Real crew trace suite |
| AutoGen | Experimental | Real agent trace suite |
| Google ADK | Experimental | Real session/event suite |
| smolagents | Experimental | Real tool trace suite |

## Delivery milestones

### M0 — Truthful foundation

- Public compatibility maturity model
- Versioned claims tied to executable evidence
- Public threat model, trust model and limitations
- PyPI soft release after Trusted Publisher authorization

### M1 — Scenario specification

- Versioned YAML contracts
- Safe bounded loading
- JSON Schema for editors and CI
- Adversarial variants with explicit inheritance
- `agenttrust init`, `agenttrust validate` and `agenttrust schema`
- YAML-to-engine translation parity
- Declarative plain-Python target execution

### M2 — Trace assertion engine

- Ordered and unordered expected traces
- Exact, containment, regex, type and presence argument matchers
- Optional, forbidden, missing, unexpected and duplicate calls
- Deterministic expected-versus-observed trace diffs

### M3 — Behavioral safeguards

- Confirmation-before-irreversible-action rules
- Maximum step and retry budgets
- Loop and cascading-failure detection
- Argument hallucination checks
- Cost, latency, state and rollback invariants

Status: confirmation ordering, step/retry budgets, repeated-call loop detection and strict argument integrity are implemented. Richer state invariants remain ongoing.

### M4 — Launch-depth execution targets

Deep, real-dependency verification for:

1. MCP
2. OpenAI Agents SDK
3. Plain Python

Broader adapters remain experimental until they pass the same evidence gates.

### M5 — Practical scenario pack

At least 20 complete cases spanning tool selection, argument integrity, confirmation, injection, exfiltration, memory, privilege, supply chain, inter-agent messages, retries, cost, latency and rollback.

Status: the versioned 20-case core pack is shipped and validated in CI.

### M6 — Audit-grade reporting

- Markdown executive and engineering report
- Trace diffs and reproduction commands
- Severity and remediation guidance
- JUnit and SARIF interoperability
- Signed evidence and cockpit integration

Status: JSON, HTML, JUnit XML, SARIF 2.1.0, Markdown, signed evidence and the local cockpit are implemented. Severity-specific remediation guidance remains ongoing.

### M7 — Public benchmark and launch

- One recognizable, safe and reproducible target
- Published scenarios, raw signed evidence and limitations
- Independent reproduction command
- Findings article and 90-second demonstration
- Five targeted design-partner or paid-audit conversations

Status: the credential-free simulated benchmark, raw evidence, methodology, findings article, demo script and outreach kit are shipped. A recognizable external MCP target and real outreach conversations remain post-publication validation work.

## Release strategy

- **v0.1.0 — Foundation:** soft PyPI release of the stable verification kernel.
- **v0.2.0 — Flagship:** behavioral safeguards, 20-case pack, deep MCP/OpenAI verification and first public benchmark.

## 90-day operating rhythm

- Weeks 1–2: scenario specification and trace assertions
- Weeks 3–4: behavioral safeguards, MCP depth and scenario pack
- Weeks 5–6: benchmark, findings article, demonstration and focused outreach
- Weeks 7–8: onboarding fixes and design-partner feedback
- Day 60: usage, conversation and revenue checkpoint
- Weeks 9–13: paid audit conversion, second benchmark, talk/webinar and retrospective

Every week should produce one meaningful product improvement, one evidence-based content asset and one focused outreach action.
