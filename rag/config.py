"""Configuration management for the Tradexia RAG service."""
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache
from loguru import logger

# Always resolve .env relative to this file's directory
_ENV_FILE = Path(__file__).parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Postgres (pgvector-enabled)
    database_url: str

    # Google AI (embeddings)
    google_api_key: str
    embedding_model: str = "gemini-embedding-001"
    # Must be 768, 1536, or 3072 — the officially supported Matryoshka tiers
    # for gemini-embedding-001. Must also match the VECTOR(N) column size
    # in the document_chunks table.
    embedding_dimension: int = 1536

    # Chunking
    chunk_size: int = 800       # tokens per chunk
    chunk_overlap: int = 100    # token overlap between consecutive chunks

    # Retrieval
    default_top_k: int = 5

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = str(_ENV_FILE)
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    try:
        settings = Settings()
    except Exception:
        logger.exception(f"[config] failed to load settings from {_ENV_FILE}")
        raise
    logger.info(
        f"[config] loaded: embedding_model={settings.embedding_model} "
        f"embedding_dimension={settings.embedding_dimension} "
        f"chunk_size={settings.chunk_size} chunk_overlap={settings.chunk_overlap} "
        f"database={settings.database_url.split('@')[-1]}"
    )
    return settings
