"""Run with: agenttrust run examples/basic_suite.py"""

from agenttrustlab import AgentResult, EvaluationCase, ExpectedOutcome


def agent(case: EvaluationCase, tools: object) -> AgentResult:
    del tools
    return AgentResult(output="The verified answer is 4.")


cases = [
    EvaluationCase(
        id="math.addition",
        prompt="What is 2 + 2?",
        expected=ExpectedOutcome(contains=("4",), excludes=("5",), max_cost_usd=0.001),
    )
]
