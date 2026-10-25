from pathlib import Path
from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache

# Resolve project root where .env resides
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"

# Explicitly load .env into os.environ so getenv and Pydantic both work reliably
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()


class Settings(BaseSettings):
    """Central configuration. Every value can be overridden via env var."""

    # Database
    database_url: str = "postgresql+asyncpg://raguser:ragpass@localhost:5432/ragdb"
    database_url_sync: str = "postgresql://raguser:ragpass@localhost:5432/ragdb"

    @field_validator("database_url", mode="before")
    @classmethod
    def clean_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip().strip("'\"")
            if v.startswith("postgres://"):
                v = "postgresql+asyncpg://" + v[len("postgres://"):]
            elif v.startswith("postgresql://") and not v.startswith("postgresql+"):
                v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    @field_validator("database_url_sync", mode="before")
    @classmethod
    def clean_database_url_sync(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip().strip("'\"")
            if v.startswith("postgres://"):
                v = "postgresql://" + v[len("postgres://"):]
            elif v.startswith("postgresql+asyncpg://"):
                v = "postgresql://" + v[len("postgresql+asyncpg://"):]
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

    # Environment & API security
    environment: str = "development"
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

    model_config = {
        "env_file": [str(ENV_FILE), ".env"],
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: int, info) -> int:
        if v < 0:
            raise ValueError("chunk_overlap must be non-negative")
        chunk_size = info.data.get("chunk_size", 512)
        if chunk_size is not None and v >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")
        return v

    @field_validator("chunk_size")
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("chunk_size must be positive")
        return v

    def validate_production_security(self) -> None:
        """Validate critical security configurations for production environments."""
        if self.environment.lower() == "production":
            insecure_keys = {"", "your-api-key-here", "dev-api-key"}
            if not self.api_key or self.api_key in insecure_keys or len(self.api_key) < 16:
                raise ValueError(
                    "Production security violation: A strong API_KEY (at least 16 characters) must be configured."
                )
            if "ragpass" in self.database_url or "ragpass" in self.database_url_sync:
                raise ValueError(
                    "Production security violation: Default database password 'ragpass' is prohibited in production."
                )
            insecure_groq = {"", "your-groq-api-key-here"}
            if not self.groq_api_key or self.groq_api_key in insecure_groq:
                raise ValueError(
                    "Production security violation: GROQ_API_KEY must be configured in production."
                )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
