from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_readiness_with_real_postgres_and_redis_services() -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "postgres": "ok", "redis": "ok"}
