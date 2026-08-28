# Threat model

## Protected assets

System/developer instructions, credentials, private tool output, persistent memory, filesystem and network authority, evaluation integrity, budget, and report provenance.

## Trust boundaries

Agent input and output are untrusted. Retrieved content and tool responses may contain instructions. Framework traces are observations, not verdicts. Adapter code is privileged and reviewed. CI release credentials are isolated behind protected GitHub environments.

## Initial threats and controls

| Threat | v0.1 control | Planned hardening |
|---|---|---|
| Prompt injection | deterministic output patterns and attack cases | taint tracking and injection corpus |
| Tool abuse | allow/deny expectations; simulated tools | capability policies and argument schemas |
| Memory poisoning | protected-key integrity check | typed diffs, lineage, rollback protocol |
| Evidence fabrication | evidence count and structured sources | source validation and citation entailment |
| Cost/latency exhaustion | per-case thresholds and timeout | suite budgets and cancellation trees |
| Nondeterminism | seeded repetitions and result fingerprinting | statistical confidence intervals |
| Report tampering | immutable contracts and CI artifacts | signing and attestations |

## Non-goals for v0.1

The project does not sandbox arbitrary Python, prove universal safety, execute destructive rollback against live services, or treat string-pattern detection as comprehensive injection defense. Live-agent suites must use least-privilege credentials and isolated test environments.

