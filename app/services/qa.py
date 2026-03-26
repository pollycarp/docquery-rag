"""
Q&A Pipeline
------------
Orchestrates the full RAG flow and logs each query to the database.

  User Question
      ↓  retriever.py   — embed question, find top-k similar chunks
  Retrieved Chunks
      ↓  llm.py         — build prompt, call Ollama, get cited answer
  Answer + Sources
      ↓  query_log      — save latency + metadata to DB
      ↓  caller         — return structured result
"""

import time
from sqlalchemy.orm import Session
from app.services.retriever import retrieve
from app.services.llm import generate_answer
from app.models.query_log import QueryLog
from app.config import settings
from app.logging_config import logger


def answer_question(question: str, db: Session, top_k: int | None = None) -> dict:
    """
    Full RAG pipeline: retrieve relevant chunks then generate a cited answer.
    Logs timing and metadata to the query_logs table.
    """
    if top_k is None:
        top_k = settings.retrieval_top_k

    # Step 1: Retrieve
    t0 = time.perf_counter()
    chunks = retrieve(question, db, top_k=top_k)
    retrieval_ms = round((time.perf_counter() - t0) * 1000, 1)

    # Step 2: Generate
    t1 = time.perf_counter()
    answer = generate_answer(question, chunks)
    generation_ms = round((time.perf_counter() - t1) * 1000, 1)

    total_ms = round(retrieval_ms + generation_ms, 1)

    # Step 3: Log to database
    log = QueryLog(
        question=question,
        answer_length=len(answer),
        chunks_retrieved=len(chunks),
        retrieval_ms=retrieval_ms,
        generation_ms=generation_ms,
        total_ms=total_ms,
        llm_model=settings.ollama_model,
        embedding_model=settings.embedding_model,
        top_k=top_k,
    )
    db.add(log)
    db.commit()

    logger.info(
        "query_answered",
        extra={
            "retrieval_ms":  retrieval_ms,
            "generation_ms": generation_ms,
            "total_ms":      total_ms,
            "chunks":        len(chunks),
            "top_k":         top_k,
        },
    )

    # Step 4: Format sources
    sources = [
        {
            "chunk_id":    chunk.chunk_id,
            "filename":    chunk.filename,
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index,
            "score":       chunk.score,
            "content":     chunk.content,
        }
        for chunk in chunks
    ]

    return {
        "question":     question,
        "answer":       answer,
        "sources":      sources,
        "latency_ms":   {"retrieval": retrieval_ms, "generation": generation_ms, "total": total_ms},
    }
