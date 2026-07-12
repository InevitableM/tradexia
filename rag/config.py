"""Configuration management for the Tradexia RAG service."""
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# Always resolve .env relative to this file's directory
_ENV_FILE = Path(__file__).parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Postgres (pgvector-enabled)
    database_url: str

    # Google AI (embeddings)
    google_api_key: str
    embedding_model: str = "text-embedding-004"

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
    return Settings()
