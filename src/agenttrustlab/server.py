"""Optional local-first FastAPI evidence explorer."""

from __future__ import annotations

import os
import secrets
from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse

from agenttrustlab import __version__
from agenttrustlab.attacks import BUILTIN_ATTACKS
from agenttrustlab.contracts import EvaluationReport
from agenttrustlab.profiles import COMMUNITY_BALANCED, COMMUNITY_HIGH_IMPACT
from agenttrustlab.standards import CONTROL_REFERENCES
from agenttrustlab.storage import ReportStore


def create_app(database: str | Path | None = None, api_token: str | None = None) -> FastAPI:
    app = FastAPI(
        title="AgentTrustLab",
        description="Framework-neutral evidence and security verification for AI agents.",
        version=__version__,
    )
    database_path: str | Path = (
        database if database is not None else os.getenv("AGENTTRUST_DB", "agenttrustlab.db")
    )
    store = ReportStore(database_path)
    write_token = api_token if api_token is not None else os.getenv("AGENTTRUST_API_TOKEN")

    @app.middleware("http")
    async def security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
        content_length = int(request.headers.get("content-length", "0"))
        if content_length > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="request body exceeds 10 MiB")
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; connect-src 'self'"
        )
        return response

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/api/catalog")
    def catalog() -> dict[str, object]:
        return {
            "attacks": [attack.model_dump(mode="json") for attack in BUILTIN_ATTACKS],
            "controls": {
                control: [reference.model_dump(mode="json") for reference in references]
                for control, references in CONTROL_REFERENCES.items()
            },
            "profiles": [
                COMMUNITY_BALANCED.model_dump(mode="json"),
                COMMUNITY_HIGH_IMPACT.model_dump(mode="json"),
            ],
        }

    @app.post("/api/reports", status_code=201)
    def ingest_report(
        report: EvaluationReport, authorization: str | None = Header(default=None)
    ) -> dict[str, str]:
        if write_token:
            supplied = authorization.removeprefix("Bearer ") if authorization else ""
            if not secrets.compare_digest(supplied, write_token):
                raise HTTPException(status_code=401, detail="invalid API token")
        return {"id": store.put(report)}

    @app.get("/api/reports")
    def list_reports(limit: int = 50) -> tuple[dict[str, object], ...]:
        if not 1 <= limit <= 500:
            raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
        return store.list(limit)

    @app.get("/api/reports/{report_id}")
    def get_report(report_id: str) -> EvaluationReport:
        report = store.get(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="report not found")
        return report

    @app.get("/", response_class=HTMLResponse)
    def dashboard() -> str:
        return files("agenttrustlab.web").joinpath("index.html").read_text(encoding="utf-8")

    return app


app = create_app()
