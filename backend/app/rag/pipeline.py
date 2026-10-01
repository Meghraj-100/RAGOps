"""RAG pipeline — the core orchestrator for query → answer."""

import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.models import QueryLog
from app.rag.retriever import get_retriever, RetrievedChunk
from app.rag.llm import generate
from app.rag.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.schemas.schemas import QueryResponse, SourceOut
from app.observability.tracing import get_tracer
import structlog

logger = structlog.get_logger()
settings = get_settings()
tracer = get_tracer()


async def run_rag_pipeline(
    question: str,
    strategy: str,
    top_k: int,
    db: AsyncSession,
) -> QueryResponse:
    """Execute the full RAG pipeline: embed → retrieve → generate → persist."""
    pipeline_start = time.perf_counter()
    query_log_id = str(uuid.uuid4())
    trace_id = None

    with tracer.start_as_current_span("POST /query") as span:
        span.set_attribute("query_log_id", query_log_id)
        span.set_attribute("retrieval_strategy", strategy)
        span.set_attribute("top_k", top_k)

        # Get trace ID
        ctx = span.get_span_context()
        if ctx and ctx.trace_id:
            trace_id = format(ctx.trace_id, '032x')

        try:
            # ── Query Processing ───────────────────────
            with tracer.start_as_current_span("query_processing"):
                pass

            # ── Retrieval ──────────────────────────────
            retriever = get_retriever(strategy)
            chunks, emb_latency, ret_latency = await retriever.retrieve(question, db, top_k)
            span.set_attribute("chunks_retrieved", len(chunks))

            # ── Context assembly ───────────────────────
            with tracer.start_as_current_span("prompt_construction") as prompt_span:
                context = _build_context(chunks)
                user_prompt = USER_PROMPT_TEMPLATE.format(context=context, question=question)

            # ── Generation ─────────────────────────────
            gen_start = time.perf_counter()
            with tracer.start_as_current_span("llm_generation") as gen_span:
                gen_span.set_attribute("model", settings.llm_model)
                answer, token_usage = await generate(SYSTEM_PROMPT, user_prompt)
                gen_span.set_attribute("tokens", token_usage.get("total_tokens", 0))
            gen_latency = (time.perf_counter() - gen_start) * 1000

            total_latency = (time.perf_counter() - pipeline_start) * 1000

            # ── Persist query log ──────────────────────
            with tracer.start_as_current_span("persist_query_log"):
                query_log = QueryLog(
                    id=uuid.UUID(query_log_id),
                    question=question,
                    answer=answer,
                    retrieval_strategy=strategy,
                    retrieved_chunk_ids=[c.chunk_id for c in chunks],
                    num_chunks_retrieved=len(chunks),
                    latency_ms=total_latency,
                    embedding_latency_ms=emb_latency,
                    retrieval_latency_ms=ret_latency,
                    generation_latency_ms=gen_latency,
                    token_usage=token_usage,
                    trace_id=trace_id,
                )
                db.add(query_log)
                await db.flush()

            # ── Build response ─────────────────────────
            sources = [
                SourceOut(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    document_filename=c.document_filename,
                    content=c.content,
                    chunk_index=c.chunk_index,
                    score=c.score,
                )
                for c in chunks
            ]

            return QueryResponse(
                query_log_id=query_log_id,
                question=question,
                answer=answer,
                sources=sources,
                strategy=strategy,
                num_chunks_retrieved=len(chunks),
                latency_ms=round(total_latency, 2),
                embedding_latency_ms=round(emb_latency, 2),
                retrieval_latency_ms=round(ret_latency, 2),
                generation_latency_ms=round(gen_latency, 2),
                trace_id=trace_id,
            )

        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            logger.error("rag_pipeline_failed", error=str(e), question=question[:100])

            # Persist error log
            total_latency = (time.perf_counter() - pipeline_start) * 1000
            query_log = QueryLog(
                id=uuid.UUID(query_log_id),
                question=question,
                retrieval_strategy=strategy,
                latency_ms=total_latency,
                error=str(e),
                trace_id=trace_id,
            )
            db.add(query_log)
            await db.flush()
            raise


def _build_context(chunks: list[RetrievedChunk]) -> str:
    """Assemble retrieved chunks into an LLM context string."""
    parts = []
    for i, chunk in enumerate(chunks):
        parts.append(
            f"[Source {i+1}: {chunk.document_filename}, Chunk {chunk.chunk_index}]\n"
            f"{chunk.content}\n"
        )
    return "\n".join(parts)
