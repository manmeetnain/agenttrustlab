"""Pytest integration and fixtures."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from agenttrustlab.adapters import PlainPythonAdapter
from agenttrustlab.baselines import measurements_from_report
from agenttrustlab.contracts import EvaluationCase, EvaluationReport, RunConfig
from agenttrustlab.engine import EvaluationEngine
from agenttrustlab.profiles import COMMUNITY_BALANCED, COMMUNITY_HIGH_IMPACT, ReleaseProfile
from agenttrustlab.verdicts import GateStatus, ReleaseVerdict, evaluate_release


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("agenttrustlab")
    group.addoption(
        "--agenttrust-profile",
        choices=("balanced", "high-impact"),
        default="balanced",
        help="AgentTrustLab release policy profile.",
    )


def assert_report(report: EvaluationReport, profile: ReleaseProfile) -> ReleaseVerdict:
    verdict = evaluate_release(measurements_from_report(report), profile)
    if verdict.status == GateStatus.BLOCKED:
        failures = ", ".join(
            f"{check.metric}={check.observed} requires {check.requirement}"
            for check in verdict.blockers
        )
        pytest.fail(f"AgentTrustLab release blocked: {failures}", pytrace=False)
    return verdict


@pytest.fixture
def agenttrust_evaluate() -> Callable[..., EvaluationReport]:
    def evaluate(
        agent: Any, cases: list[EvaluationCase], config: RunConfig | None = None
    ) -> EvaluationReport:
        import asyncio

        return asyncio.run(EvaluationEngine().evaluate(PlainPythonAdapter(agent), cases, config))

    return evaluate


@pytest.fixture
def agenttrust_profile(request: pytest.FixtureRequest) -> ReleaseProfile:
    selected = request.config.getoption("--agenttrust-profile")
    return COMMUNITY_HIGH_IMPACT if selected == "high-impact" else COMMUNITY_BALANCED


@pytest.fixture
def agenttrust_assert(
    agenttrust_profile: ReleaseProfile,
) -> Callable[[EvaluationReport], ReleaseVerdict]:
    return lambda report: assert_report(report, agenttrust_profile)
