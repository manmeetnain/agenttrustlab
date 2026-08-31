from pathlib import Path

from agenttrustlab.scenarios import (
    discover_scenarios,
    expand_scenario,
    load_scenario,
)

PACK = Path(__file__).parents[1] / "scenario-pack" / "core"


def test_core_pack_contains_twenty_valid_unique_scenarios() -> None:
    paths = discover_scenarios((PACK,))
    assert len(paths) == 20
    scenarios = [load_scenario(path).scenario for path in paths]
    assert len({scenario.id for scenario in scenarios}) == 20
    assert all(scenario.tags for scenario in scenarios)


def test_core_pack_expands_stably_and_covers_product_risks() -> None:
    scenarios = [load_scenario(path).scenario for path in discover_scenarios((PACK,))]
    expanded = [case for scenario in scenarios for case in expand_scenario(scenario)]
    assert len(expanded) >= 30
    tags = set().union(*(scenario.tags for scenario in scenarios))
    assert {
        "prompt-injection",
        "argument-integrity",
        "memory-integrity",
        "confirmation",
        "cost",
        "latency",
        "evidence",
        "determinism",
        "rollback",
    } <= tags
