from fastapi.testclient import TestClient

from bodhaflow.main import create_app


def test_unknown_route_returns_404() -> None:
    client = TestClient(create_app())

    response = client.get("/does-not-exist")

    assert response.status_code == 404


def test_health_rejects_post() -> None:
    client = TestClient(create_app())

    response = client.post("/health")

    assert response.status_code == 405
