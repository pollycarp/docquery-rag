"""
Phase 2 Tests — Retrieval (no database required)
"""

from app.services.retriever import RetrievedChunk


def test_retrieved_chunk_score_range():
    """Score should be between 0 and 1."""
    chunk = RetrievedChunk(
        chunk_id=1, document_id=1, filename="test.txt",
        content="Some content", page_number=1, chunk_index=0, score=0.87
    )
    assert 0.0 <= chunk.score <= 1.0


def test_retrieved_chunk_has_all_fields():
    """RetrievedChunk should expose all metadata fields."""
    chunk = RetrievedChunk(
        chunk_id=42, document_id=3, filename="policy.pdf",
        content="Leave entitlement is 20 days.", page_number=5,
        chunk_index=7, score=0.95
    )
    assert chunk.chunk_id == 42
    assert chunk.filename == "policy.pdf"
    assert chunk.page_number == 5
    assert chunk.content == "Leave entitlement is 20 days."
