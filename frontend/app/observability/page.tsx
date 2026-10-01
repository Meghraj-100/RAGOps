'use client'

import { Activity, ExternalLink } from 'lucide-react'

export default function ObservabilityPage() {
  return (
    <div>
      <h1 className="text-xl font-semibold mb-6">Observability</h1>

      <div className="grid grid-cols-2 gap-6 mb-8">
        {/* Grafana */}
        <div className="bg-surface-2 border border-surface-4 rounded p-6">
          <div className="flex items-center gap-2 mb-3">
            <Activity size={18} className="text-accent" />
            <h2 className="text-sm font-medium">Grafana Dashboard</h2>
          </div>
          <p className="text-xs text-muted mb-4">
            View real-time metrics: request rate, latency percentiles (P50/P95/P99),
            error rate, retrieval/embedding/generation latency breakdown.
          </p>
          <a
            href="http://localhost:3001"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-accent hover:bg-accent-hover text-white text-sm rounded transition-colors"
          >
            Open Grafana <ExternalLink size={12} />
          </a>
          <p className="text-[10px] text-muted mt-2 font-mono">admin / admin</p>
        </div>

        {/* Prometheus */}
        <div className="bg-surface-2 border border-surface-4 rounded p-6">
          <div className="flex items-center gap-2 mb-3">
            <Activity size={18} className="text-warning" />
            <h2 className="text-sm font-medium">Prometheus</h2>
          </div>
          <p className="text-xs text-muted mb-4">
            Query raw metrics directly. All RAG pipeline metrics are exposed via the /metrics endpoint.
          </p>
          <a
            href="http://localhost:9090"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-surface-4 hover:bg-surface-3 text-zinc-200 text-sm rounded transition-colors"
          >
            Open Prometheus <ExternalLink size={12} />
          </a>
        </div>
      </div>

      {/* Metrics Reference */}
      <div className="bg-surface-2 border border-surface-4 rounded p-6">
        <h2 className="text-sm font-medium mb-4 text-zinc-300">Available Metrics</h2>
        <div className="grid grid-cols-2 gap-3">
          {[
            { name: 'rag_queries_total', type: 'Counter', desc: 'Total RAG queries by strategy' },
            { name: 'rag_query_errors_total', type: 'Counter', desc: 'Failed queries by strategy and error type' },
            { name: 'rag_query_latency_seconds', type: 'Histogram', desc: 'End-to-end query latency' },
            { name: 'rag_retrieval_latency_seconds', type: 'Histogram', desc: 'Retrieval stage latency' },
            { name: 'rag_embedding_latency_seconds', type: 'Histogram', desc: 'Embedding generation latency' },
            { name: 'rag_generation_latency_seconds', type: 'Histogram', desc: 'LLM generation latency' },
            { name: 'documents_ingested_total', type: 'Counter', desc: 'Successfully ingested documents' },
            { name: 'evaluation_runs_total', type: 'Counter', desc: 'Completed evaluation runs' },
          ].map(m => (
            <div key={m.name} className="bg-surface-3 rounded p-3">
              <code className="text-xs font-mono text-accent">{m.name}</code>
              <span className="ml-2 text-[10px] bg-surface-4 px-1.5 py-0.5 rounded text-muted">{m.type}</span>
              <p className="text-xs text-muted mt-1">{m.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Trace Info */}
      <div className="bg-surface-2 border border-surface-4 rounded p-6 mt-6">
        <h2 className="text-sm font-medium mb-3 text-zinc-300">Distributed Tracing</h2>
        <p className="text-xs text-muted mb-2">
          Every RAG query generates an OpenTelemetry trace exported to Tempo via OTLP gRPC.
        </p>
        <p className="text-xs text-muted mb-3">
          Trace structure: <code className="text-accent">rag_pipeline → retrieval → generation → persist_query_log</code>
        </p>
        <p className="text-xs text-muted">
          Each span records: query_log_id, retrieval_strategy, top_k, chunk_count, model, latency.
          Find traces by query_log_id in Grafana → Tempo.
        </p>
      </div>
    </div>
  )
}
