from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


# The engine is the connection to our PostgreSQL database
engine = create_engine(settings.database_url, echo=False)

# A session is like a "unit of work" — we open one per request, then close it
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class that all database models inherit from."""
    pass


def init_db() -> None:
    """
    Creates the pgvector extension and all tables on first run.
    Safe to call multiple times — it won't overwrite existing data.
    """
    with engine.connect() as conn:
        # Enable the pgvector extension so we can store vector columns
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # Import all models so Base knows about them before create_all
    from app.models import document, query_log  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Add embedding_model column to existing chunks table if it doesn't exist yet.
    # This handles upgrades without needing a full migration tool.
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE chunks
            ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100)
            DEFAULT 'all-MiniLM-L6-v2'
        """))
        conn.commit()


def get_db():
    """
    Dependency used by FastAPI endpoints.
    Opens a DB session, yields it to the endpoint, then closes it automatically.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
