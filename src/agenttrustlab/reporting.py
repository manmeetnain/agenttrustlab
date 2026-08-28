"""Portable JSON and dependency-free HTML reports."""

from __future__ import annotations

from html import escape
from pathlib import Path

from agenttrustlab.contracts import EvaluationReport


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
