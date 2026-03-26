"""
CLI Ingestion Script
--------------------
Use this to ingest one or more documents from the command line
without needing to use the API.

Usage:
    python scripts/ingest_documents.py sample_docs/sample_policy.txt
    python scripts/ingest_documents.py path/to/file1.pdf path/to/file2.docx
"""

import sys
import os

# Make sure Python can find our app/ package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, SessionLocal
from app.services.ingestion import ingest_file


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest_documents.py <file1> [file2] ...")
        sys.exit(1)

    file_paths = sys.argv[1:]

    print("Initializing database...")
    init_db()

    db = SessionLocal()
    try:
        for path in file_paths:
            if not os.path.exists(path):
                print(f"  [SKIP] File not found: {path}")
                continue

            result = ingest_file(path, db)
            print(f"  [OK] {result['filename']} — {result['total_chunks']} chunks stored")

    finally:
        db.close()

    print("\nAll done!")


if __name__ == "__main__":
    main()
