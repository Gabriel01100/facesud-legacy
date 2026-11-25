from fastapi.testclient import TestClient

from app.api import health
from app.main import app

client = TestClient(app)


def test_readiness_returns_503_when_redis_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(health, "check_database", lambda: True)
    monkeypatch.setattr(health, "check_redis", lambda: False)
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["detail"]["postgres"] == "ok"
    assert response.json()["detail"]["redis"] == "unavailable"


def test_readiness_returns_503_when_postgres_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(health, "check_database", lambda: False)
    monkeypatch.setattr(health, "check_redis", lambda: True)
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["detail"]["postgres"] == "unavailable"
    assert response.json()["detail"]["redis"] == "ok"


def test_readiness_returns_200_when_dependencies_are_available(monkeypatch) -> None:
    monkeypatch.setattr(health, "check_database", lambda: True)
    monkeypatch.setattr(health, "check_redis", lambda: True)
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "postgres": "ok", "redis": "ok"}
