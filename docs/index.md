# AgentTrustLab

AgentTrustLab is the independent trust, evaluation, and security layer for the agentic ecosystem—**Pytest for AI agents**.

It converts agent behavior into stable evidence: typed inputs and outputs, policy decisions, metric scores, repeatability signals, and portable reports. Framework adapters are intentionally thin so verification logic is not coupled to orchestration logic.

## Quick start

```bash
pip install agenttrustlab
agenttrust run examples/basic_suite.py --repetitions 3
```

Start with deterministic simulated tools. Introduce live model and tool integrations only in explicitly labeled integration suites with bounded budgets and credentials isolated from untrusted content.

## Principles

1. Verification is independent from orchestration.
2. Every verdict is explainable and serializable.
3. Tests are deterministic by default and uncertainty is measured.
4. Untrusted agent output never becomes authority.
5. Adapters normalize observations; policies decide trust.

