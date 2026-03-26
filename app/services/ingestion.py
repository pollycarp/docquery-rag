"""
Ingestion Pipeline
------------------
Orchestrates the full ingestion flow for a single document:

  File on disk
      ↓  loader.py     — extract text + page metadata
  List of Pages
      ↓  chunker.py    — split into overlapping chunks
  List of Chunks
      ↓  embedder.py   — generate embedding vectors via OpenAI
  Chunks + Vectors
      ↓  database      — save Document + Chunk rows to PostgreSQL
  Done ✓
"""

import os
from sqlalchemy.orm import Session
from app.services.loader import load_document
from app.services.chunker import chunk_pages
from app.services.embedder import embed_texts
from app.models.document import Document, Chunk as ChunkModel
from app.config import settings


def ingest_file(file_path: str, db: Session) -> dict:
    """
    Full ingestion pipeline for a single file.

    Args:
        file_path: Absolute or relative path to the file
        db:        SQLAlchemy database session

    Returns:
        A summary dict with document id, filename, and chunk count
    """
    filename = os.path.basename(file_path)
    file_type = os.path.splitext(filename)[1].lstrip(".").lower()

    print(f"\n[1/4] Loading '{filename}'...")
    pages = load_document(file_path)
    print(f"      → {len(pages)} page(s) extracted")

    print(f"[2/4] Chunking text...")
    chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
    print(f"      → {len(chunks)} chunk(s) created")

    print(f"[3/4] Generating embeddings using '{settings.embedding_model}'...")
    texts = [chunk.content for chunk in chunks]
    embeddings = embed_texts(texts)
    print(f"      → {len(embeddings)} embedding(s) generated")

    print(f"[4/4] Saving to database...")

    # Create the parent Document record
    doc = Document(
        filename=filename,
        file_type=file_type,
        total_chunks=len(chunks),
    )
    db.add(doc)
    db.flush()  # flush to get the auto-generated doc.id before inserting chunks

    # Create one Chunk record per chunk — store the embedding model name for versioning
    chunk_models = [
        ChunkModel(
            document_id=doc.id,
            content=chunk.content,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            section_title=None,
            embedding=embedding,
            embedding_model=settings.embedding_model,
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]
    db.bulk_save_objects(chunk_models)
    db.commit()

    print(f"      → Saved document id={doc.id} with {len(chunks)} chunks\n")

    return {
        "document_id": doc.id,
        "filename": filename,
        "file_type": file_type,
        "total_chunks": len(chunks),
        "pages_processed": len(pages),
    }
