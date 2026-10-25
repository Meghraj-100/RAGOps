"""Tests for the FastAPI API endpoints (mocked external deps)."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with mocked database and tracing."""
    import app.main
    mock_engine = MagicMock()
    mock_conn = AsyncMock()
    mock_engine.begin.return_value.__aenter__.return_value = mock_conn
    mock_engine.dispose = AsyncMock()

    with patch("app.db.database.get_engine", return_value=mock_engine), \
         patch("app.main.get_engine", return_value=mock_engine), \
         patch("app.main.setup_tracing"):
        with TestClient(app.main.app) as c:
            yield c


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "RAG" in data["message"]


def test_openapi_docs(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
    assert "/api/v1/health" in data["paths"]


def test_security_headers_present(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_health_check_public(client):
    """Health check endpoint must be publicly accessible without API key."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_api_key_enforcement(client):
    """When API_KEY is set in configuration, protected endpoints reject unauthorized requests."""
    from app.core.config import get_settings
    settings = get_settings()
    original_key = settings.api_key

    try:
        settings.api_key = "secure-production-test-key-12345"

        # Request without key must fail with 401
        res_no_key = client.get("/api/v1/queries")
        assert res_no_key.status_code == 401

        # Request with invalid key must fail with 401
        res_wrong_key = client.get("/api/v1/queries", headers={"X-API-Key": "wrong-key"})
        assert res_wrong_key.status_code == 401

        async def mock_get_db():
            mock_session = AsyncMock()
            mock_res = MagicMock()
            mock_res.scalars.return_value.all.return_value = []
            mock_session.execute = AsyncMock(return_value=mock_res)
            yield mock_session

        from app.db.database import get_db
        import app.main
        app.main.app.dependency_overrides[get_db] = mock_get_db
        try:
            res_valid_header = client.get("/api/v1/queries", headers={"X-API-Key": "secure-production-test-key-12345"})
            assert res_valid_header.status_code == 200

            res_valid_bearer = client.get("/api/v1/queries", headers={"Authorization": "Bearer secure-production-test-key-12345"})
            assert res_valid_bearer.status_code == 200
        finally:
            app.main.app.dependency_overrides.pop(get_db, None)
    finally:
        settings.api_key = original_key

