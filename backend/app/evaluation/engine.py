"""Evaluation service — run retrieval benchmarks and persist results."""

import json
import time
import uuid
from pathlib import Path
from statistics import mean

import numpy as np
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.models import EvaluationRun, Chunk
from app.rag.retriever import get_retriever
from app.schemas.schemas import EvalRunOut
import structlog

logger = structlog.get_logger()
settings = get_settings()

EVAL_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "evaluation"


def load_eval_dataset(dataset_name: str = "default") -> list[dict]:
    """Load evaluation cases from JSON file."""
    filepath = EVAL_DATA_DIR / f"{dataset_name}.json"
    if not filepath.exists():
        raise FileNotFoundError(f"Evaluation dataset not found: {filepath}")
    with open(filepath) as f:
        data = json.load(f)
    return data.get("cases", data) if isinstance(data, dict) else data


def calculate_hit_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    """Check if any relevant ID appears in the top-k retrieved."""
    top_k = retrieved_ids[:k]
    return 1.0 if any(rid in top_k for rid in relevant_ids) else 0.0


def calculate_mrr(retrieved_ids: list[str], relevant_ids: list[str]) -> float:
    """Calculate Mean Reciprocal Rank for a single query."""
    for i, rid in enumerate(retrieved_ids):
        if rid in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0


def percentile(values: list[float], p: int) -> float:
    """Calculate the p-th percentile of a list."""
    if not values:
        return 0.0
    return float(np.percentile(values, p))


async def run_evaluation(
    strategy: str,
    dataset_name: str,
    top_k: int,
    db: AsyncSession,
) -> EvaluationRun:
    """Execute evaluation against a dataset and persist results."""
    cases = load_eval_dataset(dataset_name)
    retriever = get_retriever(strategy)

    eval_start = time.perf_counter()

    case_results = []
    hit_at_1_scores = []
    hit_at_3_scores = []
    hit_at_5_scores = []
    mrr_scores = []
    latencies = []

    for case in cases:
        case_id = case.get("case_id", str(uuid.uuid4()))
        question = case["question"]
        expected_source = case.get("expected_source", "")
        relevant_chunk_ids = case.get("relevant_chunk_ids", [])

        try:
            start = time.perf_counter()
            chunks, emb_lat, ret_lat = await retriever.retrieve(question, db, top_k)
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

            retrieved_ids = [c.chunk_id for c in chunks]

            # If no specific chunk IDs provided, match by source filename
            if not relevant_chunk_ids and expected_source:
                relevant_chunk_ids = [
                    c.chunk_id for c in chunks
                    if c.document_filename and expected_source.lower() in c.document_filename.lower()
                ]

            h1 = calculate_hit_at_k(retrieved_ids, relevant_chunk_ids, 1) if relevant_chunk_ids else 0
            h3 = calculate_hit_at_k(retrieved_ids, relevant_chunk_ids, 3) if relevant_chunk_ids else 0
            h5 = calculate_hit_at_k(retrieved_ids, relevant_chunk_ids, 5) if relevant_chunk_ids else 0
            mrr = calculate_mrr(retrieved_ids, relevant_chunk_ids) if relevant_chunk_ids else 0

            hit_at_1_scores.append(h1)
            hit_at_3_scores.append(h3)
            hit_at_5_scores.append(h5)
            mrr_scores.append(mrr)

            case_results.append({
                "case_id": case_id,
                "question": question,
                "hit_at_1": h1,
                "hit_at_3": h3,
                "hit_at_5": h5,
                "mrr": mrr,
                "latency_ms": round(latency, 2),
                "retrieved_count": len(chunks),
                "error": None,
            })

        except Exception as e:
            logger.error("eval_case_failed", case_id=case_id, error=str(e))
            case_results.append({
                "case_id": case_id,
                "question": question,
                "hit_at_1": 0, "hit_at_3": 0, "hit_at_5": 0, "mrr": 0,
                "latency_ms": 0, "retrieved_count": 0,
                "error": str(e),
            })

    # Check for regression against latest run of same strategy
    regression = False
    prev_run_result = await db.execute(
        select(EvaluationRun)
        .where(EvaluationRun.strategy == strategy)
        .order_by(EvaluationRun.created_at.desc())
        .limit(1)
    )
    prev_run = prev_run_result.scalar_one_or_none()

    avg_hit5 = mean(hit_at_5_scores) if hit_at_5_scores else 0
    avg_mrr = mean(mrr_scores) if mrr_scores else 0

    if prev_run:
        threshold = settings.eval_regression_threshold
        if prev_run.hit_at_5 - avg_hit5 > threshold or prev_run.mrr - avg_mrr > threshold:
            regression = True
            logger.warning(
                "regression_detected",
                strategy=strategy,
                prev_hit5=prev_run.hit_at_5,
                new_hit5=avg_hit5,
                prev_mrr=prev_run.mrr,
                new_mrr=avg_mrr,
            )

    # Persist
    eval_run = EvaluationRun(
        strategy=strategy,
        dataset_name=dataset_name,
        llm_model=settings.llm_model,
        embedding_model=settings.embedding_model,
        reranker_model=settings.reranker_model if strategy == "reranking" else None,
        top_k=top_k,
        total_cases=len(cases),
        hit_at_1=round(mean(hit_at_1_scores), 4) if hit_at_1_scores else 0,
        hit_at_3=round(mean(hit_at_3_scores), 4) if hit_at_3_scores else 0,
        hit_at_5=round(avg_hit5, 4),
        mrr=round(avg_mrr, 4),
        avg_latency_ms=round(mean(latencies), 2) if latencies else 0,
        p50_latency_ms=round(percentile(latencies, 50), 2) if latencies else 0,
        p95_latency_ms=round(percentile(latencies, 95), 2) if latencies else 0,
        case_results=case_results,
        regression_detected=regression,
    )
    db.add(eval_run)
    await db.flush()

    logger.info(
        "evaluation_complete",
        strategy=strategy, cases=len(cases),
        hit_at_1=eval_run.hit_at_1, hit_at_5=eval_run.hit_at_5,
        mrr=eval_run.mrr, regression=regression,
    )

    from app.observability.metrics import EVALUATION_DURATION
    duration_sec = time.perf_counter() - eval_start
    EVALUATION_DURATION.labels(strategy=strategy).observe(duration_sec)

    return eval_run
