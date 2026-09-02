# Public simulated benchmark

The first public benchmark demonstrates the verification layer itself without credentials or paid inference. The same 20 scenario files expand into 30 canonical and adversarial cases and run twice against two deterministic agents.

| Agent | Passed | Failed | Deterministic |
|---|---:|---:|---:|
| Intentionally vulnerable | 0 / 60 | 60 / 60 | Yes |
| Hardened contract fixture | 60 / 60 | 0 / 60 | Yes |

Reproduce it:

```bash
git clone https://github.com/manmeetnain/agenttrustlab.git
cd agenttrustlab
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python -m benchmarks.simulated.run
```

The output bundle includes JSON, portable HTML, JUnit XML, SARIF, Markdown and checksum-bound evidence manifests. The stable comparison is `benchmarks/simulated/results/summary.json`.

## What the result proves

- One portable pack can detect tool, evidence, policy, budget and behavioral divergence.
- Findings remain deterministic across repetitions.
- A hardened implementation can satisfy the same declared contracts.
- CI and human reviewers receive formats appropriate to their workflow.

## What it does not prove

The agents are fixtures, not live models. This benchmark measures AgentTrustLab's detection and reporting path, not universal safety, model quality or framework superiority. A second benchmark will target a recognizable external MCP server after target selection and responsible disclosure review.
