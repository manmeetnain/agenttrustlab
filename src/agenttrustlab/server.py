"""Optional local-first FastAPI evidence explorer."""

from __future__ import annotations

from importlib.resources import files

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from agenttrustlab import __version__
from agenttrustlab.attacks import BUILTIN_ATTACKS
from agenttrustlab.profiles import COMMUNITY_BALANCED, COMMUNITY_HIGH_IMPACT
from agenttrustlab.standards import CONTROL_REFERENCES


def create_app() -> FastAPI:
    app = FastAPI(
        title="AgentTrustLab",
        description="Framework-neutral evidence and security verification for AI agents.",
        version=__version__,
    )

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

    @app.get("/", response_class=HTMLResponse)
    def dashboard() -> str:
        return files("agenttrustlab.web").joinpath("index.html").read_text(encoding="utf-8")

    return app


app = create_app()
