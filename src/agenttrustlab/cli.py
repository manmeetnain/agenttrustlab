"""AgentTrustLab command-line interface."""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from agenttrustlab.adapters import PlainPythonAdapter
from agenttrustlab.attacks import attack_cases
from agenttrustlab.baselines import compare_reports, measurements_from_report
from agenttrustlab.contracts import EvaluationCase, RunConfig
from agenttrustlab.engine import EvaluationEngine
from agenttrustlab.evidence import create_manifest
from agenttrustlab.profiles import COMMUNITY_BALANCED, COMMUNITY_HIGH_IMPACT
from agenttrustlab.reporting import write_html, write_json
from agenttrustlab.storage import ReportStore
from agenttrustlab.verdicts import GateStatus, evaluate_release

app = typer.Typer(help="Independent verification for AI agents.", no_args_is_help=True)
console = Console()


def _load_suite(path: Path) -> tuple[Any, list[EvaluationCase]]:
    spec = importlib.util.spec_from_file_location("agenttrust_suite", path)
    if spec is None or spec.loader is None:
        raise typer.BadParameter(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.agent, list(module.cases)


@app.command()
def run(
    suite: Path = typer.Argument(..., exists=True, dir_okay=False),
    json_report: Path = typer.Option(Path("agenttrust-report.json"), "--json"),
    html_report: Path = typer.Option(Path("agenttrust-report.html"), "--html"),
    seed: int = typer.Option(0),
    repetitions: int = typer.Option(1, min=1, max=100),
    attacks: bool = typer.Option(False, "--attacks", help="Add built-in adversarial cases."),
    profile: str = typer.Option("balanced", help="Release policy: balanced or high-impact."),
    manifest: Path = typer.Option(Path("agenttrust-manifest.json")),
    baseline: Path | None = typer.Option(None, exists=True, dir_okay=False),
    store: Path | None = typer.Option(None, help="Persist the report to a dashboard SQLite DB."),
) -> None:
    """Run a Python evaluation suite."""
    agent, cases = _load_suite(suite)
    if attacks:
        cases = [variant for case in cases for variant in (case, *attack_cases(case))]
    profiles = {"balanced": COMMUNITY_BALANCED, "high-impact": COMMUNITY_HIGH_IMPACT}
    if profile not in profiles:
        raise typer.BadParameter("profile must be balanced or high-impact")
    selected_profile = profiles[profile]
    report = asyncio.run(
        EvaluationEngine().evaluate(
            PlainPythonAdapter(agent), cases, RunConfig(seed=seed, repetitions=repetitions)
        )
    )
    write_json(report, json_report)
    write_html(report, html_report)
    if store:
        ReportStore(store).put(report)
    evidence = create_manifest(
        report,
        policy_profile=f"{selected_profile.name}@{selected_profile.version}",
        limitations=("Local environment and declared cases only",),
    )
    manifest.write_text(evidence.model_dump_json(indent=2), encoding="utf-8")
    verdict = evaluate_release(measurements_from_report(report), selected_profile)
    table = Table(title="AgentTrustLab verification")
    for heading in ("Case", "Status", "Score", "Latency"):
        table.add_column(heading)
    for record in report.runs:
        table.add_row(
            record.case_id,
            record.status,
            f"{record.score.total:.0%}" if record.score else "—",
            f"{record.latency_ms:.1f} ms",
        )
    console.print(table)
    if baseline:
        from agenttrustlab.contracts import EvaluationReport

        baseline_report = EvaluationReport.model_validate_json(baseline.read_text(encoding="utf-8"))
        comparison = compare_reports(report, baseline_report)
        if comparison.regressions:
            console.print(f"[yellow]Regressions:[/] {', '.join(comparison.regressions)}")
    console.print(f"Release verdict: [bold]{verdict.status.value.upper()}[/]")
    console.print(f"Evidence manifest: {manifest}")
    raise typer.Exit(code=0 if verdict.status == GateStatus.PASSED else 1)


@app.command()
def version() -> None:
    """Show the installed version."""
    from agenttrustlab import __version__

    console.print(__version__)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind address."),
    port: int = typer.Option(8787, min=1, max=65535),
) -> None:
    """Launch the local evidence explorer."""
    try:
        import uvicorn
    except ImportError as exc:
        raise typer.BadParameter("Install AgentTrustLab with the 'server' extra") from exc
    uvicorn.run("agenttrustlab.server:app", host=host, port=port)
