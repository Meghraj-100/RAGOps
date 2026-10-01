"""Retrieval strategies — vector, hybrid, reranking, multi-query."""

from __future__ import annotations
import time
from abc import ABC, abstractmethod
from uuid import UUID

import numpy as np
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.models import Chunk, Document
from app.rag.embeddings import embed_text, embed_text_timed
import structlog

logger = structlog.get_logger()
settings = get_settings()


class RetrievedChunk:
    """A chunk returned by a retriever with its relevance score."""

    def __init__(self, chunk_id: str, document_id: str, document_filename: str,
                 content: str, chunk_index: int, score: float):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.document_filename = document_filename
        self.content = content
        self.chunk_index = chunk_index
        self.score = score

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "document_filename": self.document_filename,
            "content": self.content,
            "chunk_index": self.chunk_index,
            "score": round(self.score, 4),
        }


class BaseRetriever(ABC):
    """Abstract base for all retrieval strategies."""

    @abstractmethod
    async def retrieve(
        self, query: str, db: AsyncSession, top_k: int = 5
    ) -> tuple[list[RetrievedChunk], float, float]:
        """
        Returns (chunks, embedding_latency_ms, retrieval_latency_ms).
        """
        ...


class VectorRetriever(BaseRetriever):
    """Pure cosine-similarity vector search via pgvector."""

    async def retrieve(self, query: str, db: AsyncSession, top_k: int = 5):
        query_embedding, emb_latency = embed_text_timed(query)

        start = time.perf_counter()
        # pgvector cosine distance: <=> operator. Lower = more similar.
        result = await db.execute(
            text("""
                SELECT c.id, c.document_id, c.content, c.chunk_index,
                       d.filename AS document_filename,
                       1 - (c.embedding <=> :embedding::vector) AS score
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE d.status = 'completed'
                ORDER BY c.embedding <=> :embedding::vector
                LIMIT :top_k
            """),
            {"embedding": str(query_embedding), "top_k": top_k},
        )
        rows = result.fetchall()
        ret_latency = (time.perf_counter() - start) * 1000

        chunks = [
            RetrievedChunk(
                chunk_id=str(r.id),
                document_id=str(r.document_id),
                document_filename=r.document_filename,
                content=r.content,
                chunk_index=r.chunk_index,
                score=float(r.score) if r.score else 0.0,
            )
            for r in rows
        ]
        return chunks, emb_latency, ret_latency


class HybridRetriever(BaseRetriever):
    """Combines dense vector search with keyword (ts_vector) search via RRF."""

    async def retrieve(self, query: str, db: AsyncSession, top_k: int = 5):
        query_embedding, emb_latency = embed_text_timed(query)

        start = time.perf_counter()

        # Dense vector results
        vector_result = await db.execute(
            text("""
                SELECT c.id, c.document_id, c.content, c.chunk_index,
                       d.filename AS document_filename,
                       1 - (c.embedding <=> :embedding::vector) AS score
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE d.status = 'completed'
                ORDER BY c.embedding <=> :embedding::vector
                LIMIT :limit
            """),
            {"embedding": str(query_embedding), "limit": top_k * 2},
        )
        vector_rows = vector_result.fetchall()

        # Keyword search using PostgreSQL full-text search
        keyword_result = await db.execute(
            text("""
                SELECT c.id, c.document_id, c.content, c.chunk_index,
                       d.filename AS document_filename,
                       ts_rank_cd(to_tsvector('english', c.content),
                                  plainto_tsquery('english', :query)) AS score
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE d.status = 'completed'
                  AND to_tsvector('english', c.content) @@ plainto_tsquery('english', :query)
                ORDER BY score DESC
                LIMIT :limit
            """),
            {"query": query, "limit": top_k * 2},
        )
        keyword_rows = keyword_result.fetchall()

        # Reciprocal Rank Fusion
        rrf_k = 60  # standard RRF constant
        scores: dict[str, dict] = {}

        for rank, r in enumerate(vector_rows):
            cid = str(r.id)
            if cid not in scores:
                scores[cid] = {
                    "chunk_id": cid,
                    "document_id": str(r.document_id),
                    "document_filename": r.document_filename,
                    "content": r.content,
                    "chunk_index": r.chunk_index,
                    "rrf_score": 0.0,
                }
            scores[cid]["rrf_score"] += 1.0 / (rrf_k + rank + 1)

        for rank, r in enumerate(keyword_rows):
            cid = str(r.id)
            if cid not in scores:
                scores[cid] = {
                    "chunk_id": cid,
                    "document_id": str(r.document_id),
                    "document_filename": r.document_filename,
                    "content": r.content,
                    "chunk_index": r.chunk_index,
                    "rrf_score": 0.0,
                }
            scores[cid]["rrf_score"] += 1.0 / (rrf_k + rank + 1)

        sorted_chunks = sorted(scores.values(), key=lambda x: x["rrf_score"], reverse=True)[:top_k]
        ret_latency = (time.perf_counter() - start) * 1000

        chunks = [
            RetrievedChunk(
                chunk_id=c["chunk_id"],
                document_id=c["document_id"],
                document_filename=c["document_filename"],
                content=c["content"],
                chunk_index=c["chunk_index"],
                score=c["rrf_score"],
            )
            for c in sorted_chunks
        ]
        return chunks, emb_latency, ret_latency


class RerankingRetriever(BaseRetriever):
    """Vector retrieval → cross-encoder reranking (local, zero API cost)."""

    _reranker = None

    @classmethod
    def _get_reranker(cls):
        if cls._reranker is None:
            from sentence_transformers import CrossEncoder
            logger.info("loading_reranker", model=settings.reranker_model)
            cls._reranker = CrossEncoder(settings.reranker_model)
            logger.info("reranker_loaded")
        return cls._reranker

    async def retrieve(self, query: str, db: AsyncSession, top_k: int = 5):
        # First stage: retrieve more candidates via vector search
        vector = VectorRetriever()
        candidates, emb_latency, vec_latency = await vector.retrieve(query, db, top_k=top_k * 3)

        start = time.perf_counter()
        if candidates:
            reranker = self._get_reranker()
            pairs = [(query, c.content) for c in candidates]
            scores = reranker.predict(pairs)

            for i, c in enumerate(candidates):
                c.score = float(scores[i])

            candidates.sort(key=lambda x: x.score, reverse=True)

        rerank_latency = (time.perf_counter() - start) * 1000
        total_ret_latency = vec_latency + rerank_latency

        return candidates[:top_k], emb_latency, total_ret_latency


class MultiQueryRetriever(BaseRetriever):
    """Generate multiple query reformulations, retrieve for each, deduplicate."""

    async def retrieve(self, query: str, db: AsyncSession, top_k: int = 5):
        from app.rag.llm import generate
        from app.rag.prompts import MULTI_QUERY_SYSTEM, MULTI_QUERY_USER

        emb_latency_total = 0.0
        start = time.perf_counter()

        # Generate alternative queries
        n_queries = 3
        sys_prompt = MULTI_QUERY_SYSTEM.format(n=n_queries)
        user_prompt = MULTI_QUERY_USER.format(question=query, n=n_queries)
        alt_text, _ = await generate(sys_prompt, user_prompt, temperature=0.7, max_tokens=256)
        alt_queries = [q.strip() for q in alt_text.strip().split("\n") if q.strip()]
        alt_queries = alt_queries[:n_queries]

        # Include original query
        all_queries = [query] + alt_queries

        # Retrieve for each query and combine
        all_chunks: dict[str, RetrievedChunk] = {}
        vector = VectorRetriever()
        for q in all_queries:
            chunks, e_lat, _ = await vector.retrieve(q, db, top_k=top_k)
            emb_latency_total += e_lat
            for c in chunks:
                if c.chunk_id not in all_chunks or c.score > all_chunks[c.chunk_id].score:
                    all_chunks[c.chunk_id] = c

        # Sort by best score and take top_k
        sorted_chunks = sorted(all_chunks.values(), key=lambda x: x.score, reverse=True)[:top_k]
        total_ret_latency = (time.perf_counter() - start) * 1000

        return sorted_chunks, emb_latency_total, total_ret_latency


def get_retriever(strategy: str) -> BaseRetriever:
    """Factory function to get the appropriate retriever."""
    retrievers = {
        "vector-similarity": VectorRetriever,
        "hybrid-search": HybridRetriever,
        "reranking": RerankingRetriever,
        "multi-query": MultiQueryRetriever,
    }
    retriever_cls = retrievers.get(strategy)
    if not retriever_cls:
        raise ValueError(f"Unknown retrieval strategy: {strategy}. Available: {list(retrievers.keys())}")
    return retriever_cls()
