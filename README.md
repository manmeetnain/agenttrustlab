# AgentTrustLab

**Pytest for AI agents.** AgentTrustLab is an independent, framework-neutral verification layer for testing agent correctness, task completion, tool use, evidence, safety, prompt-injection resistance, memory integrity, cost, latency, determinism, and rollback behavior.

Created and maintained by **Manmeet Nain** ([@manmeetnain](https://github.com/manmeetnain)).

> v0.1 is an early, security-minded foundation. It is not an agent framework and does not orchestrate production agents.

## Why it exists

Agent frameworks optimize for building and running agents. AgentTrustLab verifies whether those agents can be trusted. Tests use stable Pydantic contracts; adapters translate framework-specific runs into a common result; policies and scorers remain independent.

```bash
python -m pip install agenttrustlab
agenttrust run examples/basic_suite.py
```

```python
from agenttrustlab import EvaluationCase, ExpectedOutcome


def agent(case, tools):
    return "The verified answer is 4."


cases = [
    EvaluationCase(
        id="math.addition",
        prompt="What is 2 + 2?",
        expected=ExpectedOutcome(contains=("4",)),
    )
]
```

The command produces a concise terminal result plus `agenttrust-report.json` and a professional, portable HTML report.

Create reviewable YAML scenarios without writing framework code:

```bash
agenttrust init
agenttrust validate scenarios/
```

YAML contract version 1 includes expected output, ordered or unordered tool traces, explicit argument matchers, execution budgets and inherited adversarial variants. See the [scenario guide](docs/scenarios.md).

Launch the optional local evidence explorer:

```bash
python -m pip install 'agenttrustlab[server]'
agenttrust serve
```

The web product remains local-first: reports, policies and evidence do not require a hosted AgentTrustLab account.

## v0.1 scope

- Strict, versionable Pydantic contracts
- Seeded, time-bounded deterministic execution
- Plain Python, OpenAI Agents SDK, LangGraph, CrewAI, AutoGen, Pydantic AI,
  Google ADK, smolagents and MCP adapters
- Side-effect-free simulated tool registry
- Safety, injection, forbidden-tool, and protected-memory policies
- Correctness, tool, evidence, cost, and latency scoring
- Typer/Rich CLI and pytest fixture
- JSON and dependency-free HTML reports
- Standards-mapped attack cases, rollback verification and tamper-evident manifests
- Optional FastAPI evidence explorer at `agenttrust serve`
- Python 3.11–3.13 CI, property tests, typing, lint, coverage, package validation
- Trusted Publishing-compatible release workflow and GitHub Pages documentation

See the [architecture](docs/architecture.md), [threat model](docs/threat-model.md), and [roadmap](docs/roadmap.md).

## Status and security

No evaluation can prove that an agent is safe in every environment. AgentTrustLab provides reproducible evidence under declared cases and policies. Report security issues privately through GitHub Security Advisories; do not open public issues for vulnerabilities.

Licensed under Apache-2.0.
