# Simulated trust benchmark

This benchmark runs the same 20-file, 30-case portable pack twice against deliberately vulnerable and hardened deterministic agents. Two repetitions produce 60 normalized runs per agent. It demonstrates AgentTrustLab detection and reporting; it does not claim to measure any live model or framework.

```bash
python -m benchmarks.simulated.run
```

Outputs include raw JSON, portable HTML, JUnit, SARIF, Markdown and tamper-evident manifests under `results/`. The fixed seed is 2026. Reports record timestamps, UUIDs and measured local latency, so their byte digests change between runs; `summary.json` is the stable comparison.

Limitations:

- Both agents are deterministic fixtures designed to expose expected pass/fail behavior.
- No model credentials, network calls or paid inference are used.
- Passing demonstrates conformance to this declared pack, not universal agent safety.
- Evidence manifests are checksum-bound but unsigned; production users should add an Ed25519 signing key.
