"""Prometheus metrics for the RAG platform."""

from prometheus_client import Counter, Histogram, Gauge

# ── Counters ────────────────────────────────────────────────────
RAG_QUERIES_TOTAL = Counter(
    "rag_queries_total",
    "Total number of RAG queries",
    ["strategy"],
)

RAG_QUERY_ERRORS_TOTAL = Counter(
    "rag_query_errors_total",
    "Total number of failed RAG queries",
    ["strategy", "error_type"],
)

DOCUMENTS_INGESTED = Counter(
    "documents_ingested_total",
    "Total number of documents successfully ingested",
)

EVALUATION_RUNS_TOTAL = Counter(
    "evaluation_runs_total",
    "Total number of evaluation runs",
    ["strategy"],
)

# ── Histograms ──────────────────────────────────────────────────
RAG_QUERY_LATENCY = Histogram(
    "rag_query_latency_seconds",
    "End-to-end RAG query latency",
    ["strategy"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

RAG_RETRIEVAL_LATENCY = Histogram(
    "rag_retrieval_latency_seconds",
    "Retrieval stage latency",
    ["strategy"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

RAG_EMBEDDING_LATENCY = Histogram(
    "rag_embedding_latency_seconds",
    "Embedding generation latency",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
)

RAG_GENERATION_LATENCY = Histogram(
    "rag_generation_latency_seconds",
    "LLM generation latency",
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

RAG_RERANKING_LATENCY = Histogram(
    "rag_reranking_latency_seconds",
    "Reranking stage latency",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

EVALUATION_DURATION = Histogram(
    "evaluation_duration_seconds",
    "Time taken to run a full evaluation",
    ["strategy"],
    buckets=[1.0, 5.0, 15.0, 30.0, 60.0, 120.0, 300.0],
)

RAG_RETRIEVED_DOCUMENTS = Histogram(
    "rag_retrieved_documents_count",
    "Number of documents retrieved per query",
    ["strategy"],
    buckets=[1, 3, 5, 10, 20, 50],
)

# ── Gauges ──────────────────────────────────────────────────────
ACTIVE_QUERIES = Gauge(
    "rag_active_queries",
    "Number of currently active RAG queries",
)
