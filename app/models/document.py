from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.database import Base
from app.config import settings


class Document(Base):
    """
    Represents an ingested file (e.g., policy.pdf).
    One document has many chunks.
    """
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf, docx, txt
    total_chunks: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship: one document → many chunks
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk", back_populates="document", cascade="all, delete-orphan"
    )


class Chunk(Base):
    """
    Represents a piece of text extracted from a document.
    Each chunk has:
      - the raw text content
      - metadata (page number, position in document)
      - an embedding vector for semantic search
    """
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-based position
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # The embedding vector — dimensions set by config (384 for all-MiniLM-L6-v2)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.embedding_dimensions), nullable=True
    )

    # Which embedding model produced this vector.
    # Stored so we know which chunks need re-embedding after a model upgrade.
    embedding_model: Mapped[str] = mapped_column(
        String(100), nullable=False, default=settings.embedding_model
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship back to parent document
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
