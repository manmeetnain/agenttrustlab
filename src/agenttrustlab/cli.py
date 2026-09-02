"""AgentTrustLab command-line interface."""

from __future__ import annotations

import asyncio
import importlib.util
import json
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from agenttrustlab.adapters import AgentAdapter, PlainPythonAdapter
from agenttrustlab.attacks import attack_cases
from agenttrustlab.baselines import compare_reports, measurements_from_report
from agenttrustlab.contracts import EvaluationCase, RunConfig
from agenttrustlab.engine import EvaluationEngine
from agenttrustlab.evidence import (
    EvidenceManifest,
    create_manifest,
    generate_ed25519_keypair,
    verify_manifest,
)
from agenttrustlab.profiles import COMMUNITY_BALANCED, COMMUNITY_HIGH_IMPACT
from agenttrustlab.reporting import write_html, write_json, write_junit, write_markdown, write_sarif
from agenttrustlab.scenarios import (
    EXAMPLE_SCENARIO_YAML,
    discover_scenarios,
    expand_scenario,
    load_scenario,
    scenario_json_schema,
    to_evaluation_case,
)
from agenttrustlab.storage import ReportStore
from agenttrustlab.targets import (
    EXAMPLE_AGENT_PY,
    EXAMPLE_TARGET_YAML,
    create_adapter,
    load_target,
)
from agenttrustlab.verdicts import GateStatus, evaluate_release

app = typer.Typer(help="Independent verification for AI agents.", no_args_is_help=True)
console = Console()


def _scenario_pack_source() -> Traversable:
    packaged = files("agenttrustlab").joinpath("scenario_pack")
    if packaged.is_dir():
        return packaged
    return Path(__file__).parents[2] / "scenario-pack" / "core"


def _load_suite(path: Path) -> tuple[Any, list[EvaluationCase]]:
    spec = importlib.util.spec_from_file_location("agenttrust_suite", path)
    if spec is None or spec.loader is None:
        raise typer.BadParameter(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.agent, list(module.cases)


@app.command("init")
def initialize_project(
    directory: Path = typer.Argument(Path("."), file_okay=False),
) -> None:
    """Create a reviewable starter scenario and editor schema."""
    scenario_directory = directory / "scenarios"
    scenario_path = scenario_directory / "refund-confirmation.yml"
    schema_path = directory / "agenttrust.schema.json"
    target_path = directory / "agenttrust-target.yml"
    agent_path = directory / "agent.py"
    outputs = (scenario_path, schema_path, target_path, agent_path)
    collisions = [path for path in outputs if path.exists()]
    if collisions:
        rendered = ", ".join(str(path) for path in collisions)
        raise typer.BadParameter(f"refusing to overwrite existing files: {rendered}")
    scenario_directory.mkdir(parents=True, exist_ok=True)
    scenario_path.write_text(EXAMPLE_SCENARIO_YAML, encoding="utf-8")
    schema_path.write_text(json.dumps(scenario_json_schema(), indent=2) + "\n", encoding="utf-8")
    target_path.write_text(EXAMPLE_TARGET_YAML, encoding="utf-8")
    agent_path.write_text(EXAMPLE_AGENT_PY, encoding="utf-8")
    for path in outputs:
        console.print(f"Created {path}")
    console.print(
        f"Next: agenttrust run {scenario_directory} --target {target_path}",
        style="bold blue",
    )


@app.command("validate")
def validate_scenarios(
    paths: list[Path] = typer.Argument(..., help="Scenario files or directories."),
) -> None:
    """Validate YAML scenarios without executing an agent."""
    scenarios = discover_scenarios(paths)
    if not scenarios:
        raise typer.BadParameter("no .yml or .yaml scenario files found")
    table = Table(title="AgentTrustLab scenario validation")
    table.add_column("File")
    table.add_column("Scenario")
    table.add_column("Variants")
    table.add_column("Status")
    failures = 0
    for path in scenarios:
        try:
            parsed = load_scenario(path)
            expanded = expand_scenario(parsed.scenario)
            table.add_row(str(path), parsed.scenario.id, str(len(expanded) - 1), "[green]valid[/]")
        except Exception as exc:  # Validation errors are presented per file.
            failures += 1
            table.add_row(str(path), "—", "—", f"[red]{type(exc).__name__}: {exc}[/]")
    console.print(table)
    raise typer.Exit(code=1 if failures else 0)


@app.command("schema")
def write_scenario_schema(
    output: Path = typer.Option(Path("agenttrust.schema.json"), "--output", "-o"),
) -> None:
    """Write the versioned scenario JSON Schema."""
    output.write_text(json.dumps(scenario_json_schema(), indent=2) + "\n", encoding="utf-8")
    console.print(f"Created {output}")


@app.command("pack")
def install_scenario_pack(
    directory: Path = typer.Argument(Path("agenttrust-scenarios"), file_okay=False),
) -> None:
    """Copy the bundled 20-case core scenario pack into a project."""
    source = _scenario_pack_source()
    entries = sorted(
        (entry for entry in source.iterdir() if entry.name.endswith((".yml", ".yaml"))),
        key=lambda entry: entry.name,
    )
    if not entries:
        raise typer.BadParameter("bundled scenario pack is unavailable")
    collisions = [directory / entry.name for entry in entries if (directory / entry.name).exists()]
    if collisions:
        raise typer.BadParameter(f"refusing to overwrite existing files: {collisions[0]}")
    directory.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        (directory / entry.name).write_text(entry.read_text(encoding="utf-8"), encoding="utf-8")
    console.print(f"Installed {len(entries)} scenarios in {directory}")


@app.command()
def run(
    suite: Path = typer.Argument(..., exists=True, help="Python suite or YAML scenario path."),
    target: Path | None = typer.Option(
        None, "--target", exists=True, dir_okay=False, help="Execution target for YAML scenarios."
    ),
    json_report: Path = typer.Option(Path("agenttrust-report.json"), "--json"),
    html_report: Path = typer.Option(Path("agenttrust-report.html"), "--html"),
    junit_report: Path = typer.Option(Path("agenttrust-report.xml"), "--junit"),
    sarif_report: Path = typer.Option(Path("agenttrust-report.sarif"), "--sarif"),
    markdown_report: Path = typer.Option(Path("agenttrust-report.md"), "--markdown"),
    seed: int = typer.Option(0),
    repetitions: int = typer.Option(1, min=1, max=100),
    attacks: bool = typer.Option(False, "--attacks", help="Add built-in adversarial cases."),
    profile: str = typer.Option("balanced", help="Release policy: balanced or high-impact."),
    manifest: Path = typer.Option(Path("agenttrust-manifest.json")),
    baseline: Path | None = typer.Option(None, exists=True, dir_okay=False),
    store: Path | None = typer.Option(None, help="Persist the report to a dashboard SQLite DB."),
    signing_key: Path | None = typer.Option(None, exists=True, dir_okay=False),
) -> None:
    """Run a Python suite or YAML scenarios against a declared target."""
    adapter: AgentAdapter
    if target is None:
        if suite.is_dir() or suite.suffix != ".py":
            raise typer.BadParameter("YAML scenarios require --target agenttrust-target.yml")
        agent, cases = _load_suite(suite)
        adapter = PlainPythonAdapter(agent)
    else:
        parsed_target = load_target(target)
        adapter = create_adapter(parsed_target, target)
        scenario_paths = discover_scenarios((suite,))
        if not scenario_paths:
            raise typer.BadParameter("no .yml or .yaml scenario files found")
        cases = [
            to_evaluation_case(expanded)
            for path in scenario_paths
            for expanded in expand_scenario(load_scenario(path).scenario)
        ]
    if attacks:
        cases = [variant for case in cases for variant in (case, *attack_cases(case))]
    profiles = {"balanced": COMMUNITY_BALANCED, "high-impact": COMMUNITY_HIGH_IMPACT}
    if profile not in profiles:
        raise typer.BadParameter("profile must be balanced or high-impact")
    selected_profile = profiles[profile]
    report = asyncio.run(
        EvaluationEngine().evaluate(adapter, cases, RunConfig(seed=seed, repetitions=repetitions))
    )
    write_json(report, json_report)
    write_html(report, html_report)
    write_junit(report, junit_report)
    write_sarif(report, sarif_report)
    write_markdown(report, markdown_report)
    if store:
        ReportStore(store).put(report)
    evidence = create_manifest(
        report,
        policy_profile=f"{selected_profile.name}@{selected_profile.version}",
        limitations=("Local environment and declared cases only",),
        private_key_pem=signing_key.read_bytes() if signing_key else None,
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
def keygen(
    private_key: Path = typer.Option(Path("agenttrust-private.pem")),
    public_key: Path = typer.Option(Path("agenttrust-public.pem")),
) -> None:
    """Generate an Ed25519 evidence-signing keypair."""
    if private_key.exists() or public_key.exists():
        raise typer.BadParameter("refusing to overwrite an existing key")
    private_bytes, public_bytes = generate_ed25519_keypair()
    private_key.write_bytes(private_bytes)
    private_key.chmod(0o600)
    public_key.write_bytes(public_bytes)
    console.print(f"Created {private_key} and {public_key}")


@app.command("verify")
def verify_evidence(
    report: Path = typer.Argument(..., exists=True, dir_okay=False),
    manifest: Path = typer.Argument(..., exists=True, dir_okay=False),
) -> None:
    """Verify an evidence manifest and its report digest/signature."""
    from agenttrustlab.contracts import EvaluationReport

    parsed_report = EvaluationReport.model_validate_json(report.read_text(encoding="utf-8"))
    parsed_manifest = EvidenceManifest.model_validate_json(manifest.read_text(encoding="utf-8"))
    valid = verify_manifest(parsed_manifest, parsed_report)
    console.print("Evidence verified" if valid else "Evidence verification failed")
    raise typer.Exit(code=0 if valid else 1)


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
