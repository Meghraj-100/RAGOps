"""Local embedding service using sentence-transformers (zero API cost)."""

import time
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the embedding model."""
    global _model
    if _model is None:
        logger.info("loading_embedding_model", model=settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("embedding_model_loaded", model=settings.embedding_model)
    return _model


def embed_text(text: str) -> list[float]:
    """Generate embedding for a single text string."""
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
    return embeddings.tolist()


from app.observability.tracing import get_tracer

tracer = get_tracer()

def embed_text_timed(text: str) -> tuple[list[float], float]:
    """Generate embedding and return (embedding, latency_ms)."""
    start = time.perf_counter()
    with tracer.start_as_current_span("query_embedding") as span:
        span.set_attribute("embedding_model", settings.embedding_model)
        emb = embed_text(text)
    latency_ms = (time.perf_counter() - start) * 1000
    return emb, latency_ms
