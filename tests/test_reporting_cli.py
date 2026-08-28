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
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "x.html").exists()
    assert (tmp_path / "manifest.json").exists()
