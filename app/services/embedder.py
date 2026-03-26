"""
Embedding Service
-----------------
Converts text into embedding vectors using a local sentence-transformers model.
The model runs entirely on your machine — no API key or internet needed
after the first run (the model is downloaded once and cached).

Model used: all-MiniLM-L6-v2
  - 384 dimensions
  - ~80 MB download (happens automatically on first use)
  - Fast and accurate for semantic search tasks

Lazy loading: the model is only loaded the first time embed_texts() is called,
not at import time. This keeps tests fast and avoids unnecessary downloads.
"""

from sentence_transformers import SentenceTransformer
from app.config import settings

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Load the model on first use and reuse it for all subsequent calls."""
    global _model
    if _model is None:
        print(f"Loading embedding model '{settings.embedding_model}'... ", end="", flush=True)
        _model = SentenceTransformer(settings.embedding_model)
        print("ready.")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts. Returns a list of vectors (one per text).
    Runs locally — no API calls made.
    """
    if not texts:
        return []

    embeddings = _get_model().encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """
    Embed a single query string.
    Used during retrieval to find similar chunks.
    """
    return embed_texts([query])[0]
