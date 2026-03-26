from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configuration is read from environment variables (your .env file).
    Pydantic-settings automatically loads them for us.
    """

    # OpenAI (used for the LLM in Phase 2 — not needed for embeddings now)
    openai_api_key: str = ""

    # Local embedding model (sentence-transformers, runs on your machine)
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    # PostgreSQL
    postgres_user: str = "raguser"
    postgres_password: str = "ragpassword"
    postgres_db: str = "ragdb"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Chunking settings
    chunk_size: int = 512        # max characters per chunk
    chunk_overlap: int = 64      # characters shared between adjacent chunks

    # Ollama (local LLM)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Retrieval settings
    retrieval_top_k: int = 5     # number of chunks to retrieve per query

    # API security
    api_key: str = "dev-secret-key"   # override this in .env for production

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


# Single shared instance used across the entire app
settings = Settings()
