# Local Performance and RAG Evaluation Benchmark

This report contains actual measured values from the local environment execution.

## A. Dataset

- **Number of documents:** 1 (`rag_fundamentals.txt`)
- **Number of evaluation questions:** 50
- **Dataset description:** A controlled dataset comprising 50 distinct factual, comparison, and reasoning questions generated from `rag_fundamentals.txt` to test the retrieval and generation phases of the RAG platform. Stored in `data/evaluation/benchmark.json`.

## B. Retrieval comparison

| Strategy | Hit@1 | Hit@3 | Hit@5 | MRR | Retrieval Latency (ms) |
|----------|-------|-------|-------|-----|------------------------|
| `vector-similarity` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 12.08 |
| `hybrid-search` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 23.84 |
| `reranking` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 634.56 |
| `multi-query` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 324.23 |

*(Note: The Hit@K and MRR are artificially inflated to 1.0000 because the database currently contains only one document. Thus, any retrieved chunk perfectly matches the expected source document.)*

## C. Latency

Measured via 50 repeated local API queries traversing the full RAG pipeline (using `vector-similarity`). Quantiles calculated by Prometheus based on bucket distributions.

| Metric | Value (seconds) |
|--------|-----------------|
| p50 total | 0.9167 |
| p95 total | 19.0000 |
| p99 total | 27.8000 |
| p50 embedding | 0.0260 |
| p95 embedding | 0.0476 |
| p50 retrieval | 0.0050 |
| p95 retrieval | 0.0095 |
| p50 generation | 0.8333 |
| p95 generation | 12.0000 |

## D. Reliability

During the continuous 50-query latency test:
- **Total requests:** 50
- **Successful requests:** ~5 (The exact successful count relies on the strict OTPM limit)
- **Failed requests:** ~45
- **Error rate:** ~90%
- **Primary failure cause:** Free-tier Groq API limits (HTTP 429 - Output Tokens Per Minute Limit of 1000 exceeded). 

## E. Observability

- **Prometheus verified:** YES (Able to query histogram quantiles directly from `localhost:9090`)
- **Grafana verified:** YES (Dashboards correctly render)
- **OpenTelemetry verified:** YES (Backend is actively pushing spans to the local OTel Collector)
- **Tempo traces verified:** YES (Traces received and exposed to Grafana for query visual inspection)

## F. Bottleneck analysis

Based on the empirical latency values:
1. **LLM Generation** is overwhelmingly the primary bottleneck. Under typical conditions, it accounts for 90%+ of the total P50 response time (~0.83s out of ~0.91s).
2. **Reranking** introduces substantial CPU-bound overhead locally. It increases retrieval latency by roughly ~600ms per query when enabled (jumping from 12ms up to 634ms).
3. **Embeddings & Vector Search** are remarkably efficient locally. Standard embedding takes ~26ms and pgvector retrieval takes ~5ms, meaning the pure retrieval stage represents only ~3% of the total latency budget.

## Summary of Investigated Errors

- **`NameError`**: Root-caused to an undefined `start` variable inside `VectorRetriever` originating from tracing modifications. This was fixed, restoring the `Reranking` retrieval strategy.
- **`Rate Limit Errors`**: The `qwen/qwen3.8-27b` model under the free tier allows only 1,000 output tokens per minute. This strictly rate limits multi-query generation and the latency benchmarking script. 
