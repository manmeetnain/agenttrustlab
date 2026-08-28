"""Transparent, deterministic scoring."""

from __future__ import annotations

from agenttrustlab.contracts import AgentResult, EvaluationCase, MetricScore, ScoreCard


def _fraction(matches: list[bool]) -> float:
    return sum(matches) / len(matches) if matches else 1.0


def score_result(case: EvaluationCase, result: AgentResult, latency_ms: float) -> ScoreCard:
    expected = case.expected
    text = result.output.casefold()
    correctness = _fraction([term.casefold() in text for term in expected.contains])
    exclusions = _fraction([term.casefold() not in text for term in expected.excludes])
    used = {call.name for call in result.tool_calls}
    tools = _fraction([name in used for name in expected.required_tools])
    evidence = (
        min(len(result.evidence) / expected.min_evidence, 1.0) if expected.min_evidence else 1.0
    )
    cost = 1.0 if expected.max_cost_usd is None or result.cost_usd <= expected.max_cost_usd else 0.0
    latency = (
        1.0 if expected.max_latency_ms is None or latency_ms <= expected.max_latency_ms else 0.0
    )
    metrics = (
        MetricScore(name="correctness", value=correctness, weight=3),
        MetricScore(name="exclusions", value=exclusions, weight=2),
        MetricScore(name="tool_use", value=tools, weight=2),
        MetricScore(name="evidence", value=evidence),
        MetricScore(name="cost", value=cost),
        MetricScore(name="latency", value=latency),
    )
    total = sum(m.value * m.weight for m in metrics) / sum(m.weight for m in metrics)
    return ScoreCard(metrics=metrics, total=total, passed=all(m.value == 1 for m in metrics))
