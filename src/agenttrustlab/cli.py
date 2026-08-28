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
from agenttrustlab.contracts import EvaluationCase, RunConfig
from agenttrustlab.engine import EvaluationEngine
from agenttrustlab.reporting import write_html, write_json

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
) -> None:
    """Run a Python evaluation suite."""
    agent, cases = _load_suite(suite)
    report = asyncio.run(
        EvaluationEngine().evaluate(
            PlainPythonAdapter(agent), cases, RunConfig(seed=seed, repetitions=repetitions)
        )
    )
    write_json(report, json_report)
    write_html(report, html_report)
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
    raise typer.Exit(code=0 if report.passed else 1)


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
