"""Tests for the FastAPI API endpoints (mocked external deps)."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with mocked database."""
    with patch("app.db.database.engine") as mock_engine, \
         patch("app.main.engine") as mock_main_engine:
        mock_engine.begin = MagicMock()
        mock_main_engine.begin = MagicMock()
        mock_main_engine.dispose = AsyncMock()

        from app.main import app
        with TestClient(app) as c:
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
