"""
Query API Route
---------------
POST /api/query  — Ask a question, get a cited answer
Rate limit: 20 requests per minute per IP
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.qa import answer_question
from app.config import settings
from app.api.dependencies import verify_api_key

router = APIRouter(prefix="/api", tags=["query"])


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="The question to ask")
    top_k: int = Field(
        default=5, ge=1, le=20,
        description="Number of document chunks to retrieve (1–20)"
    )


@router.post("/query", dependencies=[Depends(verify_api_key)])
def query_documents(request: Request, payload: QueryRequest, db: Session = Depends(get_db)):
    """
    Ask a natural language question and receive a cited answer.
    Rate limited to 20 requests per minute per IP address.
    """
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = answer_question(payload.question, db, top_k=payload.top_k)
        return result
    except Exception as e:
        error_msg = str(e)
        if "connection" in error_msg.lower() or "refused" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail="Could not connect to Ollama. Make sure Ollama is running.",
            )
        raise HTTPException(status_code=500, detail=error_msg)
