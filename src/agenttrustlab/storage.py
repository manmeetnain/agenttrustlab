"""Small local SQLite store for immutable evaluation reports."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from agenttrustlab.contracts import EvaluationReport


class ReportStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    adapter TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    payload TEXT NOT NULL
                )"""
            )

    def put(self, report: EvaluationReport) -> str:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO reports VALUES (?, ?, ?, ?, ?)",
                (
                    str(report.id),
                    report.created_at.isoformat(),
                    report.adapter,
                    int(report.passed),
                    report.model_dump_json(),
                ),
            )
        return str(report.id)

    def get(self, report_id: str) -> EvaluationReport | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM reports WHERE id = ?", (report_id,)
            ).fetchone()
        return EvaluationReport.model_validate_json(row["payload"]) if row else None

    def list(self, limit: int = 50) -> tuple[dict[str, object], ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, created_at, adapter, passed FROM reports "
                "ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return tuple(dict(row) for row in rows)
