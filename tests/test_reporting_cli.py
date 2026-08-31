import asyncio
import json

from typer.testing import CliRunner

from agenttrustlab import EvaluationCase, EvaluationEngine, PlainPythonAdapter
from agenttrustlab.cli import app
from agenttrustlab.reporting import write_html, write_json


def test_reports(tmp_path) -> None:
    report = asyncio.run(
        EvaluationEngine().evaluate(
            PlainPythonAdapter(lambda case, tools: "ok"), [EvaluationCase(id="ok", prompt="x")]
        )
    )
    json_path = write_json(report, tmp_path / "report.json")
    html_path = write_html(report, tmp_path / "report.html")
    assert json.loads(json_path.read_text())["adapter"] == "plain-python"
    assert "AgentTrustLab" in html_path.read_text()


def test_cli_end_to_end(tmp_path) -> None:
    suite = tmp_path / "suite.py"
    suite.write_text(
        "from agenttrustlab import EvaluationCase\n"
        "def agent(case, tools): return 'ok'\n"
        "cases=[EvaluationCase(id='ok', prompt='x')]\n"
    )
    result = CliRunner().invoke(
        app,
        [
            "run",
            str(suite),
            "--json",
            str(tmp_path / "x.json"),
            "--html",
            str(tmp_path / "x.html"),
            "--manifest",
            str(tmp_path / "manifest.json"),
            "--store",
            str(tmp_path / "reports.db"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "x.html").exists()
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "reports.db").exists()


def test_cli_keygen_refuses_overwrite(tmp_path) -> None:
    private = tmp_path / "private.pem"
    public = tmp_path / "public.pem"
    args = ["keygen", "--private-key", str(private), "--public-key", str(public)]
    first = CliRunner().invoke(app, args)
    assert first.exit_code == 0, first.output
    assert private.exists() and public.exists()
    second = CliRunner().invoke(app, args)
    assert second.exit_code != 0


def test_cli_init_validate_and_schema(tmp_path) -> None:
    runner = CliRunner()
    initialized = runner.invoke(app, ["init", str(tmp_path)])
    assert initialized.exit_code == 0, initialized.output
    scenario = tmp_path / "scenarios" / "refund-confirmation.yml"
    schema = tmp_path / "agenttrust.schema.json"
    target = tmp_path / "agenttrust-target.yml"
    agent = tmp_path / "agent.py"
    assert scenario.exists() and schema.exists() and target.exists() and agent.exists()
    assert json.loads(schema.read_text())["properties"]["version"]["const"] == "1"

    validated = runner.invoke(app, ["validate", str(tmp_path / "scenarios")])
    assert validated.exit_code == 0, validated.output
    assert "payments.refund-confirmati" in validated.output
    assert "valid" in validated.output

    collision = runner.invoke(app, ["init", str(tmp_path)])
    assert collision.exit_code != 0

    explicit_schema = tmp_path / "standalone.schema.json"
    generated = runner.invoke(app, ["schema", "--output", str(explicit_schema)])
    assert generated.exit_code == 0, generated.output
    assert explicit_schema.exists()

    report = tmp_path / "scenario-report.json"
    html = tmp_path / "scenario-report.html"
    manifest = tmp_path / "scenario-manifest.json"
    executed = runner.invoke(
        app,
        [
            "run",
            str(tmp_path / "scenarios"),
            "--target",
            str(target),
            "--json",
            str(report),
            "--html",
            str(html),
            "--manifest",
            str(manifest),
        ],
    )
    assert executed.exit_code == 0, executed.output
    payload = json.loads(report.read_text())
    assert len(payload["runs"]) == 2
    assert all(run["status"] == "passed" for run in payload["runs"])
    assert all(run["metadata"]["trace_assertion"]["passed"] for run in payload["runs"])


def test_cli_validate_reports_invalid_file(tmp_path) -> None:
    invalid = tmp_path / "invalid.yml"
    invalid.write_text('version: "2"\nscenario: {}\n', encoding="utf-8")
    result = CliRunner().invoke(app, ["validate", str(invalid)])
    assert result.exit_code == 1
    assert "ValidationError" in result.output
