"""
Re-ingestion Script
-------------------
Use this when you change your embedding model (e.g., upgrade to a better one).

The problem:
  If you switch embedding models, old chunks have vectors from the old model
  and new chunks have vectors from the new model. Comparing them during search
  produces garbage results — it's like comparing temperatures in Celsius vs Fahrenheit.

The solution:
  Delete all chunks for affected documents and re-embed from source files.

Usage:
    python scripts/reingest_all.py --docs-folder sample_docs/
    python scripts/reingest_all.py --docs-folder sample_docs/ --model old-model-name

Arguments:
    --docs-folder   Folder containing the original document files
    --model         Only re-ingest chunks produced by this model (default: re-ingest all)
    --dry-run       Show what would be re-ingested without actually doing it
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, SessionLocal
from app.models.document import Document, Chunk
from app.services.ingestion import ingest_file
from app.config import settings


def main():
    parser = argparse.ArgumentParser(description="Re-ingest documents with the current embedding model")
    parser.add_argument("--docs-folder", required=True, help="Folder containing original document files")
    parser.add_argument("--model",       default=None,  help="Only re-ingest chunks from this model (default: all stale)")
    parser.add_argument("--dry-run",     action="store_true", help="Preview without making changes")
    args = parser.parse_args()

    if not os.path.isdir(args.docs_folder):
        print(f"Error: '{args.docs_folder}' is not a valid folder.")
        sys.exit(1)

    init_db()
    db = SessionLocal()

    try:
        # Find documents with stale embeddings (different from current model)
        stale_model = args.model or f"not:{settings.embedding_model}"

        if args.model:
            stale_docs = (
                db.query(Document)
                .join(Chunk)
                .filter(Chunk.embedding_model == args.model)
                .distinct()
                .all()
            )
        else:
            stale_docs = (
                db.query(Document)
                .join(Chunk)
                .filter(Chunk.embedding_model != settings.embedding_model)
                .distinct()
                .all()
            )

        if not stale_docs:
            print(f"All chunks already use '{settings.embedding_model}'. Nothing to do.")
            return

        print(f"Found {len(stale_docs)} document(s) with stale embeddings:")
        for doc in stale_docs:
            print(f"  - [{doc.id}] {doc.filename}")

        if args.dry_run:
            print("\nDry run — no changes made.")
            return

        print(f"\nRe-ingesting with model: '{settings.embedding_model}'")

        for doc in stale_docs:
            file_path = os.path.join(args.docs_folder, doc.filename)
            if not os.path.exists(file_path):
                print(f"  [SKIP] '{doc.filename}' not found in {args.docs_folder}")
                continue

            # Delete old chunks (document row stays, chunks are replaced)
            db.query(Chunk).filter(Chunk.document_id == doc.id).delete()
            db.flush()

            # Re-ingest produces new chunks with updated embedding_model
            ingest_file(file_path, db)
            print(f"  [OK] {doc.filename} re-ingested")

        print("\nRe-ingestion complete.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
