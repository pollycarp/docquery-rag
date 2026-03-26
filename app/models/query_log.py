"""
QueryLog Model
--------------
Stores a record for every question answered by the system.

Why track this?
  - See which questions users ask most
  - Monitor latency trends over time
  - Identify slow queries (long generation_ms = Ollama struggling)
  - Calculate daily/weekly usage
"""

from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id:               Mapped[int]   = mapped_column(Integer, primary_key=True, index=True)
    question:         Mapped[str]   = mapped_column(Text, nullable=False)
    answer_length:    Mapped[int]   = mapped_column(Integer, default=0)   # chars in answer
    chunks_retrieved: Mapped[int]   = mapped_column(Integer, default=0)   # top_k used
    retrieval_ms:     Mapped[float] = mapped_column(Float, default=0.0)   # vector search time
    generation_ms:    Mapped[float] = mapped_column(Float, default=0.0)   # LLM time
    total_ms:         Mapped[float] = mapped_column(Float, default=0.0)   # end-to-end time
    llm_model:        Mapped[str]   = mapped_column(String(100), nullable=False)
    embedding_model:  Mapped[str]   = mapped_column(String(100), nullable=False)
    top_k:            Mapped[int]   = mapped_column(Integer, default=5)
    created_at:       Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
