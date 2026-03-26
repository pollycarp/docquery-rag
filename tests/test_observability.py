"""
Phase 5 Tests — Observability (logging, stats endpoint, response headers)
"""

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app, raise_server_exceptions=False)
HEADERS = {"X-API-Key": settings.api_key}


def test_response_has_request_id_header():
    """Every response should include an X-Request-ID header."""
    response = client.get("/health")
    assert "x-request-id" in response.headers


def test_response_has_response_time_header():
    """Every response should include an X-Response-Time header."""
    response = client.get("/health")
    assert "x-response-time" in response.headers


def test_stats_endpoint_requires_auth():
    """GET /api/stats should require an API key."""
    response = client.get("/api/stats")
    assert response.status_code == 401


def test_stats_endpoint_returns_expected_shape():
    """GET /api/stats should return document, chunk, and query counts."""
    response = client.get("/api/stats", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "total_queries"      in data
    assert "total_documents"    in data
    assert "total_chunks"       in data
    assert "embedding_versions" in data


def test_stats_embedding_versions_is_list():
    """embedding_versions should be a list of model name strings."""
    response = client.get("/api/stats", headers=HEADERS)
    data = response.json()
    assert isinstance(data["embedding_versions"], list)
