"""
Ingestion API Routes
--------------------
POST   /api/ingest              — Upload and ingest a document
GET    /api/documents           — List all ingested documents
GET    /api/documents/{id}      — Get a single document's details
DELETE /api/documents/{id}      — Delete a document and all its chunks
"""

import os
import shutil
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.ingestion import ingest_file
from app.models.document import Document
from app.api.dependencies import verify_api_key

router = APIRouter(prefix="/api", tags=["ingestion"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.post("/ingest", status_code=201, dependencies=[Depends(verify_api_key)])
async def ingest_document(
    file: UploadFile = File(..., description="PDF, DOCX, or TXT file to ingest"),
    db: Session = Depends(get_db),
):
    """
    Upload a document and ingest it into the vector store.

    Requires header: X-API-Key: <your-key>
    """
    _, ext = os.path.splitext(file.filename or "")
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = ingest_file(tmp_path, db)
        result["filename"] = file.filename
        return {"message": "Document ingested successfully", "data": result}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)


@router.get("/documents", dependencies=[Depends(verify_api_key)])
def list_documents(db: Session = Depends(get_db)):
    """List all ingested documents. Requires X-API-Key header."""
    documents = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return {
        "total": len(documents),
        "documents": [_format_document(doc) for doc in documents],
    }


@router.get("/documents/{document_id}", dependencies=[Depends(verify_api_key)])
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get details for a single document by its ID. Requires X-API-Key header."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document with id={document_id} not found.",
        )
    return _format_document(doc)


@router.delete("/documents/{document_id}", dependencies=[Depends(verify_api_key)])
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    Delete a document and ALL of its chunks from the database.
    This action is irreversible — the document must be re-ingested to restore it.

    Requires X-API-Key header.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document with id={document_id} not found.",
        )

    filename = doc.filename
    chunk_count = doc.total_chunks

    db.delete(doc)   # cascades to chunks automatically (see model definition)
    db.commit()

    return {
        "message": f"Document '{filename}' and its {chunk_count} chunks deleted successfully.",
        "document_id": document_id,
    }


def _format_document(doc: Document) -> dict:
    """Shared helper to format a Document model into a response dict."""
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "total_chunks": doc.total_chunks,
        "uploaded_at": doc.uploaded_at.isoformat(),
    }
