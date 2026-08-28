"""Pytest integration and fixtures."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from agenttrustlab.adapters import PlainPythonAdapter
from agenttrustlab.contracts import EvaluationCase, EvaluationReport, RunConfig
from agenttrustlab.engine import EvaluationEngine


@pytest.fixture
def agenttrust_evaluate() -> Callable[..., EvaluationReport]:
    def evaluate(
        agent: Any, cases: list[EvaluationCase], config: RunConfig | None = None
    ) -> EvaluationReport:
        import asyncio

        return asyncio.run(EvaluationEngine().evaluate(PlainPythonAdapter(agent), cases, config))

    return evaluate
