"""SQLAlchemy ORM models for the RAG platform."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def _get_embedding_dim():
    from app.core.config import get_settings
    return get_settings().embedding_dimensions


class Document(Base):
    """Uploaded document metadata."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, default=0)
    status = Column(String(50), default="pending")  # pending | processing | completed | failed
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    """A chunk of text extracted from a document, with its embedding."""

    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(384))  # all-MiniLM-L6-v2 = 384 dimensions
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    document = relationship("Document", back_populates="chunks")


class QueryLog(Base):
    """Log of every RAG query for observability."""

    __tablename__ = "query_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    retrieval_strategy = Column(String(100), nullable=False)
    retrieved_chunk_ids = Column(JSON, default=list)
    num_chunks_retrieved = Column(Integer, default=0)
    latency_ms = Column(Float, default=0)
    embedding_latency_ms = Column(Float, default=0)
    retrieval_latency_ms = Column(Float, default=0)
    generation_latency_ms = Column(Float, default=0)
    token_usage = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    trace_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class EvaluationRun(Base):
    """Persisted results of an evaluation run."""

    __tablename__ = "evaluation_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy = Column(String(100), nullable=False)
    dataset_name = Column(String(256), default="default")
    llm_model = Column(String(256), nullable=True)
    embedding_model = Column(String(256), nullable=True)
    reranker_model = Column(String(256), nullable=True)
    top_k = Column(Integer, default=5)
    total_cases = Column(Integer, default=0)
    hit_at_1 = Column(Float, default=0)
    hit_at_3 = Column(Float, default=0)
    hit_at_5 = Column(Float, default=0)
    mrr = Column(Float, default=0)
    avg_latency_ms = Column(Float, default=0)
    p50_latency_ms = Column(Float, default=0)
    p95_latency_ms = Column(Float, default=0)
    case_results = Column(JSON, default=list)  # per-case breakdown
    regression_detected = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
