# RAG Evaluation & Observability Platform

A general-purpose RAG platform that lets you upload documents, ask questions with grounded answers, run retrieval evaluations across strategies, explore query logs, and monitor everything through Grafana — all in one deployable repo.

## Overview

Most RAG demos stop at chat. This platform closes the loop: change the retrieval strategy → measure the same dataset → see what regressed, why, and where to look in the production trace.

**Core capabilities:**
- **Grounded chat** — answers cite retrieved sources with per-message latency
- **Persisted eval runs** — every evaluation lands in Postgres with Hit@K, MRR, latency percentiles
- **Run comparison** — compare two eval runs with per-metric deltas
- **Query log explorer** — inspect every RAG request with full latency breakdown
- **Production observability** — OpenTelemetry traces, Prometheus metrics, Grafana dashboards

## Architecture

```mermaid
graph TB
    User([User]) --> Frontend[Next.js Frontend]
    Frontend -->|HTTP/REST| Backend[FastAPI Backend]
    Backend --> RAG[RAG Pipeline]
    Backend --> Eval[Evaluation Engine]
    RAG --> PG[(PostgreSQL + pgvector)]
    RAG --> LLM[Groq LLM API]
    RAG --> Embed[Local Embeddings]
    Eval --> PG
    Backend -->|OTLP| Tempo[Tempo]
    Backend -->|/metrics| Prometheus[Prometheus]
    Prometheus --> Grafana[Grafana]
    Tempo --> Grafana
```

## Fixed Model Configuration

These are the fixed models selected for this version of the project:

| Task | Model | Provider | Cost | Justification |
|------|-------|----------|------|---------------|
| **LLM** | `llama-3.3-70b-versatile` | Groq | Free | Fast inference (500+ tok/s), 128K context, strong RAG/QA performance, OpenAI-compatible API |
| **Embeddings** | `all-MiniLM-L6-v2` | sentence-transformers (local) | Free | Runs locally, 384-dim, fast CPU inference, good semantic search quality, zero API cost |
| **Reranker** | `cross-encoder/ms-marco-MiniLM-L-6-v2` | sentence-transformers (local) | Free | Local cross-encoder, strong reranking quality on MS MARCO, zero API cost |
| **Query Rewriting** | `llama-3.3-70b-versatile` | Groq | Free | Same LLM — no benefit from a separate model for query reformulation |

## Features

- ✅ Document upload (PDF, TXT, DOCX)
- ✅ Text extraction, chunking, local embedding
- ✅ PostgreSQL + pgvector storage
- ✅ 4 retrieval strategies (vector, hybrid/RRF, reranking, multi-query)
- ✅ RAG generation with citations
- ✅ Evaluation engine (Hit@K, MRR, latency percentiles)
- ✅ Run comparison with deltas
- ✅ Regression detection (configurable threshold)
- ✅ Query log explorer with latency breakdown
- ✅ OpenTelemetry tracing (→ Tempo)
- ✅ Prometheus metrics (histograms for P50/P95/P99)
- ✅ Grafana dashboard (auto-provisioned)
- ✅ Docker Compose deployment
- ✅ CI/CD (GitHub Actions)
- ✅ CLI evaluation runner for CI gating

## RAG Pipeline

```
User Query
    ↓
Query Embedding (local all-MiniLM-L6-v2)
    ↓
Retrieval (selected strategy)
    ↓
Optional Reranking (local cross-encoder)
    ↓
Context Assembly
    ↓
LLM Generation (Groq llama-3.3-70b)
    ↓
Answer + Citations
    ↓
Persist Query Log + OTel Trace
```

## Retrieval Strategies

| Strategy | How it works |
|----------|-------------|
| `vector-similarity` | Query embedding → pgvector cosine distance → top-K |
| `hybrid-search` | Dense vector + PostgreSQL full-text search → Reciprocal Rank Fusion |
| `reranking` | Vector retrieval (3×K candidates) → cross-encoder reranking → top-K |
| `multi-query` | LLM generates 3 query reformulations → retrieve for each → deduplicate → top-K |

## Evaluation

Run evaluations against a dataset to measure retrieval quality:

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/evaluations/run \
  -H "Content-Type: application/json" \
  -d '{"strategy": "vector-similarity", "dataset_name": "default", "top_k": 5}'

# Via CLI (for CI)
cd backend && python -m app.evaluation.cli --strategy vector-similarity

# With regression threshold
python -m app.evaluation.cli --strategy hybrid-search --threshold 0.02
```

Metrics calculated: Hit@1, Hit@3, Hit@5, MRR, Avg/P50/P95 latency.

Regression detection: if Hit@5 or MRR drops below threshold vs. previous run, exit code 1.

## Observability

### OpenTelemetry Traces
Every RAG query generates a trace with spans for: `rag_pipeline → retrieval → generation → persist_query_log`.

### Prometheus Metrics
| Metric | Type | Description |
|--------|------|-------------|
| `rag_queries_total` | Counter | Total queries by strategy |
| `rag_query_errors_total` | Counter | Failed queries |
| `rag_query_latency_seconds` | Histogram | End-to-end latency |
| `rag_retrieval_latency_seconds` | Histogram | Retrieval stage |
| `rag_embedding_latency_seconds` | Histogram | Embedding generation |
| `rag_generation_latency_seconds` | Histogram | LLM generation |
| `documents_ingested_total` | Counter | Ingested documents |
| `evaluation_runs_total` | Counter | Eval runs |

### Grafana Dashboard
Auto-provisioned with panels for: requests/sec, error rate, P50/P95/P99 latency, retrieval/embedding/generation breakdown.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/dashboard` | Dashboard stats |
| GET | `/api/v1/documents` | List documents |
| POST | `/api/v1/documents/ingest` | Upload & ingest document |
| DELETE | `/api/v1/documents/{id}` | Delete document |
| POST | `/api/v1/query` | RAG query |
| GET | `/api/v1/queries` | List query logs |
| GET | `/api/v1/queries/{id}` | Query detail |
| GET | `/api/v1/evaluations` | List eval runs |
| GET | `/api/v1/evaluations/{id}` | Eval run detail |
| POST | `/api/v1/evaluations/run` | Run evaluation |
| GET | `/api/v1/evaluations/compare/{a}/{b}` | Compare two runs |
| GET | `/metrics` | Prometheus metrics |

Interactive docs: http://localhost:8000/docs

## Database Schema

```mermaid
erDiagram
    documents ||--o{ chunks : "has"
    documents {
        uuid id PK
        string filename
        string file_type
        int file_size
        string status
        int chunk_count
        datetime created_at
    }
    chunks {
        uuid id PK
        uuid document_id FK
        text content
        int chunk_index
        vector embedding
        json metadata
    }
    query_logs {
        uuid id PK
        text question
        text answer
        string retrieval_strategy
        json retrieved_chunk_ids
        float latency_ms
        float embedding_latency_ms
        float retrieval_latency_ms
        float generation_latency_ms
        json token_usage
        string trace_id
        datetime created_at
    }
    evaluation_runs {
        uuid id PK
        string strategy
        string dataset_name
        int total_cases
        float hit_at_1
        float hit_at_3
        float hit_at_5
        float mrr
        float avg_latency_ms
        float p50_latency_ms
        float p95_latency_ms
        json case_results
        boolean regression_detected
        datetime created_at
    }
```

## Local Development

### Prerequisites
- Docker & Docker Compose
- Groq API key (free at https://console.groq.com)

### Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — set GROQ_API_KEY

# 2. Start everything
docker compose up --build

# 3. Access
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/docs
# Grafana:   http://localhost:3001  (admin/admin)
# Prometheus: http://localhost:9090
```

### Without Docker

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Docker

```bash
docker compose up --build        # Start all services
docker compose up -d             # Detached mode
docker compose down              # Stop
docker compose down -v           # Stop + remove volumes
docker compose logs backend -f   # Follow backend logs
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key (free tier) | Required |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://raguser:ragpass@postgres:5432/ragdb` |
| `LLM_MODEL` | LLM model name | `llama-3.3-70b-versatile` |
| `EMBEDDING_MODEL` | Embedding model | `all-MiniLM-L6-v2` |
| `RERANKER_MODEL` | Reranker model | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| `CHUNK_SIZE` | Characters per chunk | `512` |
| `CHUNK_OVERLAP` | Overlap between chunks | `50` |
| `TOP_K` | Default retrieval count | `5` |
| `EVAL_REGRESSION_THRESHOLD` | Max acceptable metric drop | `0.02` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Tempo endpoint | `http://tempo:4317` |

## Testing

```bash
cd backend
pytest tests/ -v                # Run all tests
pytest tests/ -v --tb=long      # With full tracebacks
pytest tests/ --cov=app         # With coverage
```

Tests cover: chunking, text extraction, evaluation metrics (Hit@K, MRR, percentile), retriever factory, prompt templates, API endpoints.

No paid API calls required for tests.

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`):
1. Backend: install deps → run pytest
2. Frontend: install deps → typecheck → build
3. Docker: build both images

No paid API dependencies in CI.

## Production Deployment

| Component | Recommended | Alternative |
|-----------|-------------|-------------|
| Frontend | Vercel | Netlify, Cloudflare Pages |
| Backend | Render, Railway, Fly.io | Any Docker host |
| Database | Neon, Supabase | Any managed PostgreSQL with pgvector |
| Observability | Grafana Cloud | Self-hosted |

### Deployment checklist
- [ ] Set all environment variables
- [ ] Configure CORS for production domain
- [ ] Enable HTTPS
- [ ] Set a strong API_KEY
- [ ] Use managed PostgreSQL with pgvector
- [ ] Configure Grafana Cloud or self-hosted for traces/metrics

## Performance Benchmarking

**Methodology:** Run `POST /api/v1/evaluations/run` for each strategy against the bundled 10-case evaluation dataset.

**Current status:** Run benchmark to populate. Upload the sample document (`data/sample_docs/rag_fundamentals.txt`), then run evaluations.

```bash
# Run all strategies
for strategy in vector-similarity hybrid-search reranking multi-query; do
  curl -X POST http://localhost:8000/api/v1/evaluations/run \
    -H "Content-Type: application/json" \
    -d "{\"strategy\": \"$strategy\", \"dataset_name\": \"default\", \"top_k\": 5}"
done
```

Results are persisted in PostgreSQL and visible in the Evaluations page.

## Limitations

- Embedding model (all-MiniLM-L6-v2) has a 256-token context window — longer chunks are truncated
- Groq free tier has rate limits (30 RPM, 100K tokens/day for 70B model)
- No authentication/authorization beyond API key
- Single-user — no multi-tenancy
- No streaming responses
- Reranking adds latency (runs locally on CPU)

## Future Improvements

- Upgrade to a stronger embedding model (e.g., BGE-M3, Qwen3-Embedding)
- Add streaming RAG responses
- Implement Alembic migrations for schema evolution
- Add answer faithfulness evaluation (LLM-as-judge)
- User authentication and RBAC
- Async document ingestion with background workers
- Chunking strategy experimentation (semantic chunking)
- PDF page-level source citations
