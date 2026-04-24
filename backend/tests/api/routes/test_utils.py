from fastapi.testclient import TestClient

from app.core.config import settings


def test_health_check(client: TestClient) -> None:
    """Health check should return DB status and deployment metadata."""
    response = client.get(f"{settings.API_V1_STR}/utils/health-check/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "ok"
    assert payload["git_sha"] == settings.GIT_SHA
    assert payload["environment"] == settings.ENVIRONMENT
