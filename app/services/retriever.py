"""
Retrieval Service
-----------------
Given a user's question, finds the most relevant chunks from the database
using vector (semantic) similarity search.

How it works:
  1. Embed the question into a 384-dim vector (same model used during ingestion)
  2. Compare that vector against all stored chunk vectors using cosine distance
  3. Return the top-k most similar chunks with their metadata

Cosine distance measures the "angle" between two vectors.
  - Distance 0.0 = identical meaning
  - Distance 1.0 = completely unrelated
We convert distance → score (1 - distance) so higher = more relevant.
"""

from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.models.document import Chunk, Document
from app.services.embedder import embed_query
from app.config import settings


@dataclass
class RetrievedChunk:
    """A chunk returned from the vector search, with its relevance score."""
    chunk_id: int
    document_id: int
    filename: str
    content: str
    page_number: int | None
    chunk_index: int
    score: float          # 0.0 to 1.0, higher = more relevant


def retrieve(query: str, db: Session, top_k: int | None = None) -> list[RetrievedChunk]:
    """
    Find the top-k most relevant chunks for a given query.

    Args:
        query:  The user's natural language question
        db:     Database session
        top_k:  How many chunks to return (defaults to config value)

    Returns:
        List of RetrievedChunk, sorted by relevance (most relevant first)
    """
    if top_k is None:
        top_k = settings.retrieval_top_k

    # Step 1: embed the question
    query_vector = embed_query(query)

    # Step 2: cosine distance search using pgvector's <=> operator
    results = (
        db.query(Chunk, Chunk.embedding.cosine_distance(query_vector).label("distance"))
        .join(Document, Chunk.document_id == Document.id)
        .order_by("distance")
        .limit(top_k)
        .all()
    )

    # Step 3: pack into RetrievedChunk dataclasses
    return [
        RetrievedChunk(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            filename=chunk.document.filename,
            content=chunk.content,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            score=round(1 - float(distance), 4),
        )
        for chunk, distance in results
    ]
