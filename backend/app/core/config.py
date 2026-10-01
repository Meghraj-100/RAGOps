"""Application configuration loaded from environment variables."""

from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Central configuration. Every value can be overridden via env var."""

    # Database
    database_url: str = "postgresql+asyncpg://raguser:ragpass@localhost:5432/ragdb"
    database_url_sync: str = "postgresql://raguser:ragpass@localhost:5432/ragdb"

    @field_validator("database_url", "database_url_sync", mode="before")
    def clean_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().strip("'\"")
        return v

    # LLM — Groq free tier
    groq_api_key: str = ""
    llm_model: str = "qwen/qwen3.8-27b"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024

    # Embeddings — local sentence-transformers
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    # Reranker — local cross-encoder
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_enabled: bool = True

    # RAG
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 5

    # API security & CORS
    api_key: str = ""
    cors_origins: str = "http://localhost:3000,http://frontend:3000,http://localhost:3002"

    # Observability
    otel_enabled: bool = True
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_exporter_otlp_headers: str = ""
    otel_service_name: str = "rag-platform"
    prometheus_enabled: bool = True

    # Evaluation
    eval_regression_threshold: float = 0.02

    # Upload
    max_upload_size_mb: int = 50
    upload_dir: str = "uploads"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
