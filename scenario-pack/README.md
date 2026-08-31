# AgentTrustLab core scenario pack

Twenty portable cases exercise correctness, tool selection, argument integrity, confirmation, prompt injection, exfiltration, privilege abuse, memory poisoning, supply chain, code execution, inter-agent spoofing, retry and loop control, cost, latency, evidence, human trust, transparency, determinism and rollback.

Validate the complete pack:

```bash
agenttrust validate scenario-pack/core
```

Run it against a compatible declared target:

```bash
agenttrust run scenario-pack/core --target agenttrust-target.yml
```

The pack defines expected behavior; target adapters must expose the named tools and normalized evidence appropriate to each case. Standards tags provide traceability, not certification.
