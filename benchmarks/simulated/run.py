"""Generate the credential-free public comparison benchmark."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from agenttrustlab import EvaluationEngine, PlainPythonAdapter, RunConfig
from agenttrustlab.evidence import create_manifest
from agenttrustlab.reporting import write_html, write_json, write_junit, write_markdown, write_sarif
from agenttrustlab.scenarios import (
    discover_scenarios,
    expand_scenario,
    load_scenario,
    to_evaluation_case,
)
from benchmarks.simulated.agents import hardened_agent, vulnerable_agent

ROOT = Path(__file__).parents[2]
PACK = ROOT / "scenario-pack" / "core"
RESULTS = Path(__file__).parent / "results"


def _cases():
    return tuple(
        to_evaluation_case(expanded)
        for path in discover_scenarios((PACK,))
        for expanded in expand_scenario(load_scenario(path).scenario)
    )


def _write_bundle(name, report):
    write_json(report, RESULTS / f"{name}.json")
    write_html(report, RESULTS / f"{name}.html")
    write_junit(report, RESULTS / f"{name}.xml")
    write_sarif(report, RESULTS / f"{name}.sarif")
    write_markdown(report, RESULTS / f"{name}.md")
    manifest = create_manifest(
        report,
        policy_profile="benchmark-simulation@1",
        limitations=(
            "Deterministic simulated agents; no claim about live model quality",
            "Local execution environment and repository scenario pack only",
        ),
    )
    (RESULTS / f"{name}.manifest.json").write_text(
        manifest.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    cases = _cases()
    reports = {}
    for name, agent in (("vulnerable", vulnerable_agent), ("hardened", hardened_agent)):
        report = asyncio.run(
            EvaluationEngine().evaluate(
                PlainPythonAdapter(agent), cases, RunConfig(seed=2026, repetitions=2)
            )
        )
        reports[name] = report
        _write_bundle(name, report)
    summary = {
        "schema_version": "1",
        "scenario_files": len(discover_scenarios((PACK,))),
        "expanded_cases": len(cases),
        "repetitions": 2,
        "seed": 2026,
        "agents": {
            name: {
                "runs": len(report.runs),
                "passed": sum(run.status == "passed" for run in report.runs),
                "failed": sum(run.status != "passed" for run in report.runs),
                "deterministic": report.deterministic,
            }
            for name, report in reports.items()
        },
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
