from fastapi.testclient import TestClient

from agenttrustlab.server import create_app


def test_server_health_catalog_and_dashboard(tmp_path) -> None:
    client = TestClient(create_app(tmp_path / "server.db"))
    assert client.get("/health").json()["status"] == "ok"
    catalog = client.get("/api/catalog").json()
    assert len(catalog["attacks"]) == 11
    assert catalog["profiles"][0]["name"] == "community-balanced"
    response = client.get("/")
    assert response.status_code == 200
    assert "Release trust gate" in response.text


def test_report_api(tmp_path) -> None:
    import asyncio

    from agenttrustlab import EvaluationCase, EvaluationEngine, PlainPythonAdapter

    client = TestClient(create_app(tmp_path / "api.db"))
    report = asyncio.run(
        EvaluationEngine().evaluate(
            PlainPythonAdapter(lambda case, tools: "ok"),
            [EvaluationCase(id="api", prompt="x")],
        )
    )
    response = client.post("/api/reports", json=report.model_dump(mode="json"))
    assert response.status_code == 201
    report_id = response.json()["id"]
    assert client.get(f"/api/reports/{report_id}").json()["adapter"] == "plain-python"
    assert len(client.get("/api/reports").json()) == 1
    assert client.get("/api/reports/missing").status_code == 404
    assert client.get("/api/reports?limit=0").status_code == 422
