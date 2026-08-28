from fastapi.testclient import TestClient

from agenttrustlab.server import create_app


def test_server_health_catalog_and_dashboard() -> None:
    client = TestClient(create_app())
    assert client.get("/health").json()["status"] == "ok"
    catalog = client.get("/api/catalog").json()
    assert len(catalog["attacks"]) == 3
    assert catalog["profiles"][0]["name"] == "community-balanced"
    response = client.get("/")
    assert response.status_code == 200
    assert "Release trust gate" in response.text
