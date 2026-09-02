import asyncio
import importlib.util
from pathlib import Path

from agenttrustlab import EvaluationEngine, PlainPythonAdapter, RunConfig
from agenttrustlab.scenarios import (
    discover_scenarios,
    expand_scenario,
    load_scenario,
    to_evaluation_case,
)

PACK = Path(__file__).parents[1] / "scenario-pack" / "core"
AGENTS_PATH = Path(__file__).parents[1] / "benchmarks" / "simulated" / "agents.py"
SPEC = importlib.util.spec_from_file_location("benchmark_agents", AGENTS_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
hardened_agent = MODULE.hardened_agent
vulnerable_agent = MODULE.vulnerable_agent


def cases():
    return tuple(
        to_evaluation_case(expanded)
        for path in discover_scenarios((PACK,))
        for expanded in expand_scenario(load_scenario(path).scenario)
    )


def test_hardened_fixture_passes_full_pack_deterministically() -> None:
    report = asyncio.run(
        EvaluationEngine().evaluate(
            PlainPythonAdapter(hardened_agent), cases(), RunConfig(seed=2026, repetitions=2)
        )
    )
    assert report.passed
    assert report.deterministic
    assert len(report.runs) == 60


def test_vulnerable_fixture_produces_explainable_findings() -> None:
    report = asyncio.run(EvaluationEngine().evaluate(PlainPythonAdapter(vulnerable_agent), cases()))
    assert not report.passed
    assert all(run.status == "failed" for run in report.runs)
    assert all(run.violations for run in report.runs)
