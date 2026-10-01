"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ── Health ──────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    database: str
    llm: str
    embedding_model: str


# ── Documents ───────────────────────────────────────────────────
class DocumentOut(BaseModel):
    id: UUID
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentOut]
    total: int


# ── Chunks ──────────────────────────────────────────────────────
class ChunkOut(BaseModel):
    id: UUID
    document_id: UUID
    content: str
    chunk_index: int
    score: Optional[float] = None
    document_filename: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Query ───────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    strategy: str = Field(default="vector-similarity")
    top_k: int = Field(default=5, ge=1, le=20)


class SourceOut(BaseModel):
    chunk_id: str
    document_id: str
    document_filename: str
    content: str
    chunk_index: int
    score: float


class QueryResponse(BaseModel):
    query_log_id: str
    question: str
    answer: str
    sources: list[SourceOut]
    strategy: str
    num_chunks_retrieved: int
    latency_ms: float
    embedding_latency_ms: float
    retrieval_latency_ms: float
    generation_latency_ms: float
    trace_id: Optional[str] = None


# ── Query Log ───────────────────────────────────────────────────
class QueryLogOut(BaseModel):
    id: UUID
    question: str
    answer: Optional[str] = None
    retrieval_strategy: str
    num_chunks_retrieved: int
    latency_ms: float
    error: Optional[str] = None
    trace_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryLogDetailOut(QueryLogOut):
    retrieved_chunk_ids: list
    embedding_latency_ms: float
    retrieval_latency_ms: float
    generation_latency_ms: float
    token_usage: Optional[dict] = None


# ── Evaluation ──────────────────────────────────────────────────
class EvalCaseInput(BaseModel):
    case_id: str
    question: str
    expected_source: Optional[str] = None
    relevant_chunk_ids: list[str] = []


class EvalRunRequest(BaseModel):
    strategy: str = "vector-similarity"
    dataset_name: str = "default"
    top_k: int = 5


class EvalRunOut(BaseModel):
    id: UUID
    strategy: str
    dataset_name: str
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    reranker_model: Optional[str] = None
    top_k: int
    total_cases: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    regression_detected: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EvalRunDetailOut(EvalRunOut):
    case_results: list


class EvalCompareResponse(BaseModel):
    run_a: EvalRunOut
    run_b: EvalRunOut
    deltas: dict


# ── Dashboard ───────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_documents: int
    total_chunks: int
    total_queries: int
    total_eval_runs: int
    avg_latency_ms: float
    p95_latency_ms: float
    error_rate: float
    latest_eval: Optional[EvalRunOut] = None
    recent_queries: list[QueryLogOut]
    recent_evals: list[EvalRunOut]


# ── Error ───────────────────────────────────────────────────────
class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
