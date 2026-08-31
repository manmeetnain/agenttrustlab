"""Portable human and CI-native evaluation reports."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from xml.etree import ElementTree

from agenttrustlab.contracts import EvaluationReport, RunStatus


def write_json(report: EvaluationReport, path: str | Path) -> Path:
    target = Path(path)
    target.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return target


def write_html(report: EvaluationReport, path: str | Path) -> Path:
    target = Path(path)
    rows = "".join(
        f"<tr><td>{escape(run.case_id)}</td><td><span class='{run.status}'>{run.status}</span></td>"
        f"<td>{f'{run.score.total:.0%}' if run.score else '—'}</td>"
        f"<td>{run.latency_ms:.1f} ms</td>"
        f"<td>{escape('; '.join(run.violations) or run.error or '')}</td></tr>"
        for run in report.runs
    )
    html = f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>AgentTrustLab report</title><style>
:root{{--ink:#16233a;--muted:#61708a;--line:#dce3ed;--brand:#3157d5;--good:#08785b;--bad:#b42318}}
body{{font:15px system-ui;margin:0;background:#f7f9fc;color:var(--ink)}}main{{max-width:1080px;margin:48px auto;padding:0 24px}}
.card{{background:white;border:1px solid var(--line);border-radius:16px;padding:28px;box-shadow:0 8px 28px #16233a0d}}
h1{{font-size:28px;margin:0}}p{{color:var(--muted)}}table{{border-collapse:collapse;width:100%;margin-top:24px}}th,td{{padding:12px;text-align:left;border-bottom:1px solid var(--line)}}
th{{font-size:12px;text-transform:uppercase;color:var(--muted)}}.passed{{color:var(--good)}}.failed,.error,.blocked{{color:var(--bad)}}
</style></head><body><main><div class='card'><h1>AgentTrustLab</h1><p>Independent verification report · {escape(report.adapter)} · {report.created_at.isoformat()}</p>
<table><thead><tr><th>Case</th><th>Status</th><th>Score</th><th>Latency</th><th>Finding</th></tr></thead><tbody>{rows}</tbody></table></div></main></body></html>"""
    target.write_text(html, encoding="utf-8")
    return target


def _finding(run: object) -> str:
    violations = getattr(run, "violations", ())
    return "; ".join(violations) or getattr(run, "error", None) or "verification failed"


def write_junit(report: EvaluationReport, path: str | Path) -> Path:
    """Write JUnit XML consumable by CI test-report systems."""
    failures = sum(run.status != RunStatus.PASSED for run in report.runs)
    suite = ElementTree.Element(
        "testsuite",
        name="AgentTrustLab",
        tests=str(len(report.runs)),
        failures=str(failures),
        time=f"{sum(run.latency_ms for run in report.runs) / 1000:.6f}",
    )
    for run in report.runs:
        case = ElementTree.SubElement(
            suite,
            "testcase",
            classname=f"agenttrust.{report.adapter}",
            name=run.case_id,
            time=f"{run.latency_ms / 1000:.6f}",
        )
        if run.status != RunStatus.PASSED:
            failure = ElementTree.SubElement(case, "failure", type=run.status.value)
            failure.text = _finding(run)
    target = Path(path)
    ElementTree.ElementTree(suite).write(target, encoding="utf-8", xml_declaration=True)
    return target


def write_sarif(report: EvaluationReport, path: str | Path) -> Path:
    """Write SARIF 2.1.0 findings for GitHub code scanning and compatible tools."""
    results = []
    for run in report.runs:
        if run.status == RunStatus.PASSED:
            continue
        results.append(
            {
                "ruleId": f"agenttrust/{run.status.value}",
                "level": "error"
                if run.status in {RunStatus.ERROR, RunStatus.BLOCKED}
                else "warning",
                "message": {"text": f"{run.case_id}: {_finding(run)}"},
                "properties": {
                    "caseId": run.case_id,
                    "score": run.score.total if run.score else None,
                    "adapter": report.adapter,
                },
            }
        )
    payload = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "AgentTrustLab",
                        "informationUri": "https://github.com/manmeetnain/agenttrustlab",
                        "version": "0.1.0",
                    }
                },
                "results": results,
            }
        ],
    }
    target = Path(path)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


def write_markdown(report: EvaluationReport, path: str | Path) -> Path:
    """Write a review-friendly audit summary with reproducible raw findings."""
    passed = sum(run.status == RunStatus.PASSED for run in report.runs)
    lines = [
        "# AgentTrustLab verification report",
        "",
        f"- Adapter: `{report.adapter}`",
        f"- Result: **{'PASS' if report.passed else 'FAIL'}**",
        f"- Cases: {len(report.runs)} ({passed} passed, {len(report.runs) - passed} failed)",
        f"- Deterministic: {'yes' if report.deterministic else 'no'}",
        "",
        "| Case | Status | Score | Latency | Finding |",
        "|---|---:|---:|---:|---|",
    ]
    for run in report.runs:
        finding = _finding(run) if run.status != RunStatus.PASSED else "—"
        finding = finding.replace("|", "\\|").replace("\n", " ")
        score = f"{run.score.total:.0%}" if run.score else "—"
        lines.append(
            f"| `{run.case_id}` | {run.status.value} | {score} | "
            f"{run.latency_ms:.1f} ms | {finding} |"
        )
    target = Path(path)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target
