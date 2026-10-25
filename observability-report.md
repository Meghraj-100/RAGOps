# Observability Implementation Report

## 1. Files Created
- `observability/otel-collector/otel-collector-config.yml` (Minimal production-appropriate OTel Collector config for routing traces to local Tempo and optional external endpoints).

## 2. Files Modified
- `.env.example`: Cleaned up and clearly separated configurations into sections (`APPLICATION`, `DATABASE`, `MODEL`, `CORS / FRONTEND`, `OBSERVABILITY`), using `qwen/qwen3.8-27b` by default.
- `docker-compose.yml`: Added `otel-collector` service with configurable endpoint dependencies, mapped to ports 4317/4318.
- `backend/app/core/config.py`: Added configuration variables `otel_enabled`, `otel_exporter_otlp_headers`, `prometheus_enabled`, and `cors_origins`.
- `backend/app/main.py`: Updated CORS origins to be dynamically configurable for production (Vercel, Render) and conditionally mounted `/metrics` based on `PROMETHEUS_ENABLED`.
- `backend/app/api/routes.py`: Added observation of `RAG_RETRIEVED_DOCUMENTS` metric to `/query` route.
- `backend/app/evaluation/engine.py`: Added start and end timer logic to calculate and observe the `EVALUATION_DURATION` metric.
- `backend/app/observability/tracing.py`: Updated tracing setup to securely handle production OTLP endpoints via headers and fallback securely (`insecure=False` when using `https`).
- `backend/app/observability/metrics.py`: Added missing Prometheus metrics: `RAG_RERANKING_LATENCY`, `RAG_RETRIEVED_DOCUMENTS`, `EVALUATION_DURATION`.
- `backend/app/rag/pipeline.py`: Replaced monolithic tracing spans with precise spans matching requirements: `query_processing`, `prompt_construction`, and `llm_generation`.
- `backend/app/rag/embeddings.py`: Wrapped local embedding execution inside `query_embedding` tracing span.
- `backend/app/rag/retriever.py`: Appended `vector_retrieval` and `reranking` tracing spans to their respective operations.
- `observability/grafana/dashboards/rag-overview.json`: Appended panels for `Reranking Latency` and `Retrieved Documents`.
- `README.md`: Replaced the Observability documentation with deep-dives on the trace lifecycle, metrics structure, and separated Local/Production checklists.

## 3. Existing Observability Components Reused
- OpenTelemetry SDK integration inside the FastAPI backend.
- Prometheus configuration and endpoints.
- Tempo Docker setup for trace reception.
- Grafana dashboard provisioner and `rag-overview.json`.

## 4. New Observability Components Added
- `otel-collector` service in Docker compose to accept OTLP traces.
- Conditional telemetry mounting to disable endpoints dynamically in testing or production if not needed.
- `RAG_RERANKING_LATENCY` & `RAG_RETRIEVED_DOCUMENTS` & `EVALUATION_DURATION` Prometheus metric collections.
- `OTEL_EXPORTER_OTLP_HEADERS` environment configuration support for securely forwarding to Grafana Cloud.

## 5. Local Command to Start Everything
```bash
docker compose up -d --build
```

## 6. Grafana URL
`http://localhost:3001` (Credentials: admin/admin)

## 7. Prometheus URL
`http://localhost:9090`

## 8. Backend Metrics URL
`http://localhost:8000/metrics`

## 9. How to Verify a RAG Trace
1. Submit a RAG query to `POST /api/v1/query`.
2. Grab the `trace_id` returned in the JSON response payload.
3. Open Grafana (`http://localhost:3001`), navigate to the **Explore** tab.
4. Select **Tempo** as the data source.
5. Search by `trace_id` to visually trace through `query_embedding`, `vector_retrieval`, and `llm_generation`.

## 10. Production Deployment Steps
1. Deploy the FastAPI backend on **Render/Railway** with the `Dockerfile`.
2. Configure **Vercel** to deploy the Next.js frontend, pointing `NEXT_PUBLIC_API_URL` to the Render backend URL.
3. Attach the backend to a **Neon/Supabase** database and set `DATABASE_URL`.
4. In Render/Railway environment variables, configure observability settings to point directly to a hosted tracing solution (e.g. Grafana Cloud).
5. Ensure `PROMETHEUS_ENABLED=true` so the provider (or Datadog/Cloud) can scrape `/metrics`.

## 11. Required Environment Variables for Production
```env
# Application
DATABASE_URL=postgresql://user:pass@host/db
GROQ_API_KEY=gsk_xxx

# Observability
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway.grafana.net/otlp
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic xxx
PROMETHEUS_ENABLED=true
CORS_ORIGINS=https://my-frontend-app.vercel.app
```

## 12. Limitations & Manual Steps
- Grafana Cloud sets strict limits on log sizes and metrics card counts. You will need to explicitly create an API key with `metrics:write` and `traces:write` permissions.
- You must manually update `CORS_ORIGINS` on Render to allow Vercel's generated domain name so that client-side `fetch` requests can hit the backend properly.
