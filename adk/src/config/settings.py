"""Configuration management for Tradexia ADK agents."""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google AI
    google_api_key: str
    agent_model: str = "gemini-2.0-flash-exp"
    agent_temperature: float = 0.7
    agent_max_tokens: int = 2048
    
    # Backend API
    backend_api_url: str = "http://localhost:8000"
    backend_api_key: str = ""
    
    # Redis Cache
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
