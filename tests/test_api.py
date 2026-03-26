"""
Phase 3 Tests — API authentication and document management endpoints.
Uses FastAPI's TestClient to make real HTTP requests against the app
without needing the server to be running.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.config import settings

client = TestClient(app, raise_server_exceptions=False)

VALID_KEY = settings.api_key
HEADERS = {"X-API-Key": VALID_KEY}


# ── Auth Tests ────────────────────────────────────────────────────────────────

def test_health_check_requires_no_auth():
    """/health should be publicly accessible."""
    response = client.get("/health")
    assert response.status_code == 200


def test_missing_api_key_returns_401():
    """Requests without X-API-Key should be rejected."""
    response = client.get("/api/documents")
    assert response.status_code == 401


def test_wrong_api_key_returns_401():
    """Requests with the wrong key should be rejected."""
    response = client.get("/api/documents", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401


def test_valid_api_key_is_accepted():
    """Requests with the correct key should pass auth."""
    response = client.get("/api/documents", headers=HEADERS)
    assert response.status_code == 200


# ── Document Listing Tests ────────────────────────────────────────────────────

def test_list_documents_returns_expected_shape():
    """GET /api/documents should return total and documents list."""
    response = client.get("/api/documents", headers=HEADERS)
    data = response.json()
    assert "total" in data
    assert "documents" in data
    assert isinstance(data["documents"], list)


def test_get_nonexistent_document_returns_404():
    """GET /api/documents/99999 should return 404 for unknown id."""
    response = client.get("/api/documents/99999", headers=HEADERS)
    assert response.status_code == 404


def test_delete_nonexistent_document_returns_404():
    """DELETE /api/documents/99999 should return 404 for unknown id."""
    response = client.delete("/api/documents/99999", headers=HEADERS)
    assert response.status_code == 404


# ── Query Validation Tests ────────────────────────────────────────────────────

def test_query_rejects_empty_question():
    """POST /api/query with a too-short question should return 422."""
    response = client.post(
        "/api/query",
        headers=HEADERS,
        json={"question": "Hi", "top_k": 5},  # less than min_length=3
    )
    assert response.status_code == 422


def test_query_rejects_invalid_top_k():
    """top_k must be between 1 and 20."""
    response = client.post(
        "/api/query",
        headers=HEADERS,
        json={"question": "What is the leave policy?", "top_k": 50},
    )
    assert response.status_code == 422


def test_ingest_rejects_unsupported_file_type():
    """Uploading a .csv file should return 400."""
    response = client.post(
        "/api/ingest",
        headers=HEADERS,
        files={"file": ("data.csv", b"col1,col2\n1,2", "text/csv")},
    )
    assert response.status_code == 400
