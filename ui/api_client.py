"""
API Client
----------
All communication between the UI and the FastAPI backend lives here.
The UI never calls the database directly — it always goes through the API.
"""

import os
import requests

# When running locally:  http://127.0.0.1:8000  (default)
# When running in Docker: http://api:8000        (set via API_BASE_URL env var)
BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
API_KEY  = os.getenv("API_KEY", "dev-secret-key")

HEADERS = {"X-API-Key": API_KEY}


def ask_question(question: str, top_k: int = 5) -> dict:
    """Send a question to the backend and return the answer + sources."""
    response = requests.post(
        f"{BASE_URL}/api/query",
        headers=HEADERS,
        json={"question": question, "top_k": top_k},
        timeout=120,   # Ollama can be slow on first call
    )
    response.raise_for_status()
    return response.json()


def list_documents() -> list[dict]:
    """Return all ingested documents."""
    response = requests.get(f"{BASE_URL}/api/documents", headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.json()["documents"]


def upload_document(file_bytes: bytes, filename: str) -> dict:
    """Upload and ingest a document file."""
    response = requests.post(
        f"{BASE_URL}/api/ingest",
        headers=HEADERS,
        files={"file": (filename, file_bytes)},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def delete_document(document_id: int) -> dict:
    """Delete a document and all its chunks."""
    response = requests.delete(
        f"{BASE_URL}/api/documents/{document_id}",
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def get_stats() -> dict:
    """Fetch live system statistics."""
    response = requests.get(f"{BASE_URL}/api/stats", headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.json()
