"""API v1 route definitions."""

import time
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import get_db
from app.models.models import Document, Chunk, QueryLog, EvaluationRun
from app.schemas.schemas import (
    HealthResponse, DocumentOut, DocumentListResponse,
    QueryRequest, QueryResponse, QueryLogOut, QueryLogDetailOut,
    EvalRunRequest, EvalRunOut, EvalRunDetailOut, EvalCompareResponse,
    DashboardStats, ErrorResponse, ErrorDetail,
)
from app.services.ingestion import ingest_document, ALLOWED_EXTENSIONS
from app.rag.pipeline import run_rag_pipeline
from app.evaluation.engine import run_evaluation
from app.observability.metrics import (
    RAG_QUERIES_TOTAL, RAG_QUERY_ERRORS_TOTAL, RAG_QUERY_LATENCY,
    RAG_RETRIEVAL_LATENCY, RAG_EMBEDDING_LATENCY, RAG_GENERATION_LATENCY,
    EVALUATION_RUNS_TOTAL, ACTIVE_QUERIES,
)
import structlog

logger = structlog.get_logger()
settings = get_settings()
router = APIRouter(prefix="/api/v1")


# ── Health ──────────────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check — verifies database connectivity and LLM config."""
    db_status = "healthy"
    try:
        await db.execute(select(func.count()).select_from(Document))
    except Exception:
        db_status = "unhealthy"

    llm_status = "configured" if settings.groq_api_key else "not_configured"

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        llm=llm_status,
        embedding_model=settings.embedding_model,
    )


# ── Dashboard ───────────────────────────────────────────────────
@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Dashboard stats — all values from real database queries."""
    total_docs = (await db.execute(select(func.count()).select_from(Document))).scalar() or 0
    total_chunks = (await db.execute(select(func.count()).select_from(Chunk))).scalar() or 0
    total_queries = (await db.execute(select(func.count()).select_from(QueryLog))).scalar() or 0
    total_evals = (await db.execute(select(func.count()).select_from(EvaluationRun))).scalar() or 0

    # Latency stats
    avg_lat = (await db.execute(select(func.avg(QueryLog.latency_ms)))).scalar() or 0
    error_count = (await db.execute(
        select(func.count()).select_from(QueryLog).where(QueryLog.error.isnot(None))
    )).scalar() or 0
    error_rate = error_count / total_queries if total_queries > 0 else 0

    # P95 latency — get from actual data
    p95_result = await db.execute(
        select(QueryLog.latency_ms)
        .where(QueryLog.error.is_(None))
        .order_by(QueryLog.latency_ms.desc())
    )
    all_latencies = [r[0] for r in p95_result.fetchall()]
    p95 = 0.0
    if all_latencies:
        import numpy as np
        p95 = float(np.percentile(all_latencies, 95))

    # Latest eval
    latest_eval_result = await db.execute(
        select(EvaluationRun).order_by(desc(EvaluationRun.created_at)).limit(1)
    )
    latest_eval = latest_eval_result.scalar_one_or_none()

    # Recent queries
    recent_q_result = await db.execute(
        select(QueryLog).order_by(desc(QueryLog.created_at)).limit(5)
    )
    recent_queries = recent_q_result.scalars().all()

    # Recent evals
    recent_e_result = await db.execute(
        select(EvaluationRun).order_by(desc(EvaluationRun.created_at)).limit(5)
    )
    recent_evals = recent_e_result.scalars().all()

    return DashboardStats(
        total_documents=total_docs,
        total_chunks=total_chunks,
        total_queries=total_queries,
        total_eval_runs=total_evals,
        avg_latency_ms=round(avg_lat, 2),
        p95_latency_ms=round(p95, 2),
        error_rate=round(error_rate, 4),
        latest_eval=EvalRunOut.model_validate(latest_eval) if latest_eval else None,
        recent_queries=[QueryLogOut.model_validate(q) for q in recent_queries],
        recent_evals=[EvalRunOut.model_validate(e) for e in recent_evals],
    )


# ── Documents ───────────────────────────────────────────────────
@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(desc(Document.created_at)))
    docs = result.scalars().all()
    return DocumentListResponse(
        documents=[DocumentOut.model_validate(d) for d in docs],
        total=len(docs),
    )


@router.get("/documents/{doc_id}", response_model=DocumentOut)
async def get_document(doc_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut.model_validate(doc)


@router.post("/documents/ingest", response_model=DocumentOut, status_code=201)
async def ingest(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Upload and ingest a document (PDF, TXT, DOCX)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}",
        )

    content = await file.read()
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail=f"File too large. Max: {settings.max_upload_size_mb}MB")

    try:
        doc = await ingest_document(file.filename, content, file.content_type or "", db)
        return DocumentOut.model_validate(doc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("ingest_endpoint_error", error=str(e))
        raise HTTPException(status_code=500, detail="Document ingestion failed")


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(doc_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)


# ── Query ───────────────────────────────────────────────────────
@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest, db: AsyncSession = Depends(get_db)):
    """Execute a RAG query."""
    ACTIVE_QUERIES.inc()
    start = time.perf_counter()
    try:
        RAG_QUERIES_TOTAL.labels(strategy=req.strategy).inc()
        result = await run_rag_pipeline(req.question, req.strategy, req.top_k, db)

        # Record metrics
        latency_sec = (time.perf_counter() - start)
        RAG_QUERY_LATENCY.labels(strategy=req.strategy).observe(latency_sec)
        RAG_RETRIEVAL_LATENCY.labels(strategy=req.strategy).observe(result.retrieval_latency_ms / 1000)
        RAG_EMBEDDING_LATENCY.observe(result.embedding_latency_ms / 1000)
        RAG_GENERATION_LATENCY.observe(result.generation_latency_ms / 1000)

        return result
    except Exception as e:
        RAG_QUERY_ERRORS_TOTAL.labels(strategy=req.strategy, error_type=type(e).__name__).inc()
        logger.error("query_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        ACTIVE_QUERIES.dec()


# ── Query Logs ──────────────────────────────────────────────────
@router.get("/queries", response_model=list[QueryLogOut])
async def list_queries(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QueryLog).order_by(desc(QueryLog.created_at)).limit(limit).offset(offset)
    )
    return [QueryLogOut.model_validate(q) for q in result.scalars().all()]


@router.get("/queries/{query_id}", response_model=QueryLogDetailOut)
async def get_query(query_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QueryLog).where(QueryLog.id == query_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Query log not found")
    return QueryLogDetailOut.model_validate(q)


# ── Evaluations ─────────────────────────────────────────────────
@router.get("/evaluations", response_model=list[EvalRunOut])
async def list_evaluations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EvaluationRun).order_by(desc(EvaluationRun.created_at))
    )
    return [EvalRunOut.model_validate(e) for e in result.scalars().all()]


@router.get("/evaluations/{eval_id}", response_model=EvalRunDetailOut)
async def get_evaluation(eval_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EvaluationRun).where(EvaluationRun.id == eval_id))
    e = result.scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return EvalRunDetailOut.model_validate(e)


@router.post("/evaluations/run", response_model=EvalRunOut, status_code=201)
async def run_eval(req: EvalRunRequest, db: AsyncSession = Depends(get_db)):
    """Execute an evaluation run against a dataset."""
    try:
        EVALUATION_RUNS_TOTAL.labels(strategy=req.strategy).inc()
        eval_run = await run_evaluation(req.strategy, req.dataset_name, req.top_k, db)
        return EvalRunOut.model_validate(eval_run)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("eval_run_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluations/compare/{run_a_id}/{run_b_id}", response_model=EvalCompareResponse)
async def compare_evaluations(
    run_a_id: UUID, run_b_id: UUID, db: AsyncSession = Depends(get_db)
):
    """Compare two evaluation runs."""
    result_a = await db.execute(select(EvaluationRun).where(EvaluationRun.id == run_a_id))
    result_b = await db.execute(select(EvaluationRun).where(EvaluationRun.id == run_b_id))
    run_a = result_a.scalar_one_or_none()
    run_b = result_b.scalar_one_or_none()

    if not run_a or not run_b:
        raise HTTPException(status_code=404, detail="One or both evaluation runs not found")

    a = EvalRunOut.model_validate(run_a)
    b = EvalRunOut.model_validate(run_b)

    deltas = {
        "hit_at_1": round(b.hit_at_1 - a.hit_at_1, 4),
        "hit_at_3": round(b.hit_at_3 - a.hit_at_3, 4),
        "hit_at_5": round(b.hit_at_5 - a.hit_at_5, 4),
        "mrr": round(b.mrr - a.mrr, 4),
        "avg_latency_ms": round(b.avg_latency_ms - a.avg_latency_ms, 2),
        "p95_latency_ms": round(b.p95_latency_ms - a.p95_latency_ms, 2),
    }

    return EvalCompareResponse(run_a=a, run_b=b, deltas=deltas)
