import asyncio

import pytest

from agenttrustlab import EvaluationCase, EvaluationEngine, ExpectedOutcome, PlainPythonAdapter
from agenttrustlab.profiles import COMMUNITY_BALANCED
from agenttrustlab.pytest_plugin import assert_report


def make_report(output: str):
    return asyncio.run(
        EvaluationEngine().evaluate(
            PlainPythonAdapter(lambda case, tools: output),
            [EvaluationCase(id="gate", prompt="x", expected=ExpectedOutcome(contains=("ok",)))],
        )
    )


def test_assert_report_returns_passing_verdict() -> None:
    assert assert_report(make_report("ok"), COMMUNITY_BALANCED).status == "passed"


def test_assert_report_produces_pytest_failure() -> None:
    with pytest.raises(pytest.fail.Exception, match="release blocked"):
        assert_report(make_report("bad"), COMMUNITY_BALANCED)
