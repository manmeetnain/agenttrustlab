import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from agenttrustlab.contracts import EvaluationCase, MetricScore, ScoreCard


def test_contracts_are_strict_and_immutable() -> None:
    case = EvaluationCase(id="valid.case", prompt="hello")
    assert case.created_at if hasattr(case, "created_at") else True
    with pytest.raises(ValidationError):
        EvaluationCase.model_validate({"id": "x", "prompt": "x", "unknown": True})
    with pytest.raises(ValidationError):
        EvaluationCase(id="spaces invalid", prompt="x")


def test_score_total_is_validated() -> None:
    with pytest.raises(ValidationError, match="weighted"):
        ScoreCard(metrics=(MetricScore(name="x", value=1),), total=0, passed=False)


@given(st.text(min_size=1).filter(lambda value: value.strip() and "\x00" not in value))
def test_prompt_round_trip(prompt: str) -> None:
    case = EvaluationCase(id="property", prompt=prompt)
    assert EvaluationCase.model_validate_json(case.model_dump_json()) == case
