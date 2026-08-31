# AgentTrustLab

AgentTrustLab is the independent trust, evaluation, and security layer for the agentic ecosystem—**Pytest for AI agents**.

It converts agent behavior into stable evidence: typed inputs and outputs, policy decisions, metric scores, repeatability signals, and portable reports. Framework adapters are intentionally thin so verification logic is not coupled to orchestration logic.

## Quick start

```bash
pip install agenttrustlab
agenttrust init my-agent-trust
cd my-agent-trust
agenttrust run scenarios --target agenttrust-target.yml
```

The generated starter is immediately runnable and produces JSON, HTML, JUnit, SARIF, Markdown and tamper-evident manifest outputs. Its YAML contract defines output expectations, tool traces, adversarial variants, confirmation rules, loop detection and execution budgets.

## What ships

- A deterministic verification engine and framework-neutral normalized evidence model
- Active security cases and a validated 20-case core scenario pack
- Explainable tool-trace and behavioral differences, never opaque pass/fail labels
- Plain-Python execution plus adapter boundaries for OpenAI Agents, MCP and other ecosystems
- Pytest fixtures, release gates and CI-native report formats
- A local-first evidence cockpit—no hosted account required

Start with simulated tools. Introduce live model and tool integrations only in explicitly labeled integration suites with bounded budgets and credentials isolated from untrusted content.

## Principles

1. Verification is independent from orchestration.
2. Every verdict is explainable and serializable.
3. Tests are deterministic by default and uncertainty is measured.
4. Untrusted agent output never becomes authority.
5. Adapters normalize observations; policies decide trust.
