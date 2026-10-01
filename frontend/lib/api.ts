/**
 * API client for the RAG platform backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  if (!res.ok) {
    const errorBody = await res.text()
    throw new Error(`API Error ${res.status}: ${errorBody}`)
  }
  return res.json()
}

// ── Types ────────────────────────────────────────────────────────

export interface DashboardStats {
  total_documents: number
  total_chunks: number
  total_queries: number
  total_eval_runs: number
  avg_latency_ms: number
  p95_latency_ms: number
  error_rate: number
  latest_eval: EvalRun | null
  recent_queries: QueryLog[]
  recent_evals: EvalRun[]
}

export interface Document {
  id: string
  filename: string
  file_type: string
  file_size: number
  status: string
  chunk_count: number
  error_message: string | null
  created_at: string
}

export interface QueryLog {
  id: string
  question: string
  answer: string | null
  retrieval_strategy: string
  num_chunks_retrieved: number
  latency_ms: number
  error: string | null
  trace_id: string | null
  created_at: string
}

export interface QueryLogDetail extends QueryLog {
  retrieved_chunk_ids: string[]
  embedding_latency_ms: number
  retrieval_latency_ms: number
  generation_latency_ms: number
  token_usage: Record<string, number> | null
}

export interface Source {
  chunk_id: string
  document_id: string
  document_filename: string
  content: string
  chunk_index: number
  score: number
}

export interface QueryResponse {
  query_log_id: string
  question: string
  answer: string
  sources: Source[]
  strategy: string
  num_chunks_retrieved: number
  latency_ms: number
  embedding_latency_ms: number
  retrieval_latency_ms: number
  generation_latency_ms: number
  trace_id: string | null
}

export interface EvalRun {
  id: string
  strategy: string
  dataset_name: string
  llm_model: string | null
  embedding_model: string | null
  reranker_model: string | null
  top_k: number
  total_cases: number
  hit_at_1: number
  hit_at_3: number
  hit_at_5: number
  mrr: number
  avg_latency_ms: number
  p50_latency_ms: number
  p95_latency_ms: number
  regression_detected: boolean
  created_at: string
}

export interface EvalRunDetail extends EvalRun {
  case_results: CaseResult[]
}

export interface CaseResult {
  case_id: string
  question: string
  hit_at_1: number
  hit_at_3: number
  hit_at_5: number
  mrr: number
  latency_ms: number
  retrieved_count: number
  error: string | null
}

export interface EvalCompare {
  run_a: EvalRun
  run_b: EvalRun
  deltas: Record<string, number>
}

export interface HealthStatus {
  status: string
  database: string
  llm: string
  embedding_model: string
}

// ── API Methods ──────────────────────────────────────────────────

export const api = {
  health: () => apiFetch<HealthStatus>('/api/v1/health'),

  dashboard: () => apiFetch<DashboardStats>('/api/v1/dashboard'),

  listDocuments: () => apiFetch<{ documents: Document[]; total: number }>('/api/v1/documents'),

  getDocument: (id: string) => apiFetch<Document>(`/api/v1/documents/${id}`),

  uploadDocument: async (file: File): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${API_BASE}/api/v1/documents/ingest`, {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) throw new Error(`Upload failed: ${await res.text()}`)
    return res.json()
  },

  deleteDocument: async (id: string): Promise<void> => {
    await fetch(`${API_BASE}/api/v1/documents/${id}`, { method: 'DELETE' })
  },

  query: (question: string, strategy: string, topK: number) =>
    apiFetch<QueryResponse>('/api/v1/query', {
      method: 'POST',
      body: JSON.stringify({ question, strategy, top_k: topK }),
    }),

  listQueries: (limit = 50, offset = 0) =>
    apiFetch<QueryLog[]>(`/api/v1/queries?limit=${limit}&offset=${offset}`),

  getQuery: (id: string) => apiFetch<QueryLogDetail>(`/api/v1/queries/${id}`),

  listEvaluations: () => apiFetch<EvalRun[]>('/api/v1/evaluations'),

  getEvaluation: (id: string) => apiFetch<EvalRunDetail>(`/api/v1/evaluations/${id}`),

  runEvaluation: (strategy: string, datasetName: string, topK: number) =>
    apiFetch<EvalRun>('/api/v1/evaluations/run', {
      method: 'POST',
      body: JSON.stringify({ strategy, dataset_name: datasetName, top_k: topK }),
    }),

  compareEvaluations: (runAId: string, runBId: string) =>
    apiFetch<EvalCompare>(`/api/v1/evaluations/compare/${runAId}/${runBId}`),
}
