"""
Stats API Route
---------------
GET /api/stats — Live usage statistics from the query_logs table
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.query_log import QueryLog
from app.models.document import Document, Chunk
from app.api.dependencies import verify_api_key

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", dependencies=[Depends(verify_api_key)])
def get_stats(db: Session = Depends(get_db)):
    """
    Returns live usage statistics:
    - Total queries answered
    - Average latency (retrieval, generation, total)
    - Slowest and fastest queries
    - Total documents and chunks in the system
    - Embedding models in use (versioning info)
    """
    total_queries = db.query(func.count(QueryLog.id)).scalar() or 0

    # Document and chunk counts
    total_documents = db.query(func.count(Document.id)).scalar() or 0
    total_chunks    = db.query(func.count(Chunk.id)).scalar() or 0

    # Embedding model versions currently stored
    embedding_versions = [
        row[0] for row in db.query(Chunk.embedding_model).distinct().all()
    ]

    if total_queries == 0:
        return {
            "total_queries":      0,
            "total_documents":    total_documents,
            "total_chunks":       total_chunks,
            "embedding_versions": embedding_versions,
            "latency_ms":         None,
        }

    # Aggregate latency stats
    stats = db.query(
        func.avg(QueryLog.retrieval_ms).label("avg_retrieval"),
        func.avg(QueryLog.generation_ms).label("avg_generation"),
        func.avg(QueryLog.total_ms).label("avg_total"),
        func.min(QueryLog.total_ms).label("min_total"),
        func.max(QueryLog.total_ms).label("max_total"),
    ).one()

    return {
        "total_queries":      total_queries,
        "total_documents":    total_documents,
        "total_chunks":       total_chunks,
        "embedding_versions": embedding_versions,
        "latency_ms": {
            "avg_retrieval":  round(stats.avg_retrieval, 1),
            "avg_generation": round(stats.avg_generation, 1),
            "avg_total":      round(stats.avg_total, 1),
            "min_total":      round(stats.min_total, 1),
            "max_total":      round(stats.max_total, 1),
        },
    }
