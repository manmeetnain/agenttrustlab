# Getting started

AgentTrustLab is local-first. A hosted account is not required.

## Install

```bash
python -m pip install 'agenttrustlab[server]'
```

Initialize and validate a YAML scenario workspace:

```bash
agenttrust init
agenttrust validate scenarios/
agenttrust run scenarios/ --target agenttrust-target.yml
```

`init` creates a reviewable scenario, editor-compatible JSON Schema, target declaration and small example agent. The run command expands inherited adversarial variants, executes the declared target and applies output, policy and trace gates. It writes JSON, portable HTML and a tamper-evident evidence manifest.

The target file deliberately contains configuration rather than executable YAML:

```yaml
version: "1"
target:
  adapter: plain-python
  entrypoint: agent.py:agent
```

Entrypoints are resolved relative to the target file. Only code you trust should be executed.

Create `agenttrust_suite.py`:

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

Python suites remain supported. Run one plus all built-in adversarial variants:

```bash
agenttrust run agenttrust_suite.py \
  --attacks \
  --profile balanced \
  --store agenttrustlab.db
```

Outputs include JSON, portable HTML, a tamper-evident evidence manifest, a policy verdict and a CI-compatible exit code.

## Inspect locally

```bash
AGENTTRUST_DB=agenttrustlab.db agenttrust serve
```

Open `http://127.0.0.1:8787`. The dashboard and SQLite database stay on the local machine.

## Use with pytest

The plugin provides `agenttrust_evaluate`, `agenttrust_profile` and `agenttrust_assert` fixtures:

```python
def test_release(agenttrust_evaluate, agenttrust_assert):
    report = agenttrust_evaluate(agent, cases)
    agenttrust_assert(report)
```

Select the stricter profile with `pytest --agenttrust-profile high-impact`.
