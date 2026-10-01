'use client'

import { useState } from 'react'
import { api, QueryResponse } from '@/lib/api'
import { Send, Clock, Layers, Zap, FileText } from 'lucide-react'

const STRATEGIES = [
  { value: 'vector-similarity', label: 'Vector Similarity' },
  { value: 'hybrid-search', label: 'Hybrid Search' },
  { value: 'reranking', label: 'Reranking' },
  { value: 'multi-query', label: 'Multi-Query' },
]

export default function ChatPage() {
  const [question, setQuestion] = useState('')
  const [strategy, setStrategy] = useState('vector-similarity')
  const [topK, setTopK] = useState(5)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await api.query(question, strategy, topK)
      setResult(res)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-xl font-semibold mb-6">Chat</h1>

      {/* Query Form */}
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex gap-3 mb-3">
          <select
            value={strategy}
            onChange={e => setStrategy(e.target.value)}
            className="bg-surface-2 border border-surface-4 rounded px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-accent"
          >
            {STRATEGIES.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
          <select
            value={topK}
            onChange={e => setTopK(Number(e.target.value))}
            className="bg-surface-2 border border-surface-4 rounded px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-accent"
          >
            {[3, 5, 8, 10].map(k => (
              <option key={k} value={k}>Top {k}</option>
            ))}
          </select>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="Ask a question about your documents..."
            className="flex-1 bg-surface-2 border border-surface-4 rounded px-4 py-3 text-sm text-zinc-200 placeholder:text-muted focus:outline-none focus:border-accent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="px-4 py-3 bg-accent hover:bg-accent-hover disabled:opacity-50 text-white rounded transition-colors flex items-center gap-2 text-sm"
          >
            <Send size={14} />
            {loading ? 'Querying...' : 'Ask'}
          </button>
        </div>
      </form>

      {error && <div className="bg-danger/10 border border-danger/20 text-danger text-sm p-3 rounded mb-4">{error}</div>}

      {/* Result */}
      {result && (
        <div className="space-y-4">
          {/* Metrics Bar */}
          <div className="flex gap-4 text-xs">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-2 border border-surface-4 rounded">
              <Zap size={12} className="text-accent" />
              <span className="text-muted">Strategy:</span>
              <span className="font-mono text-zinc-200">{result.strategy}</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-2 border border-surface-4 rounded">
              <Layers size={12} className="text-accent" />
              <span className="text-muted">Retrieved:</span>
              <span className="font-mono text-zinc-200">{result.num_chunks_retrieved} chunks</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-2 border border-surface-4 rounded">
              <Clock size={12} className="text-accent" />
              <span className="text-muted">Latency:</span>
              <span className="font-mono text-zinc-200">{result.latency_ms.toFixed(0)} ms</span>
            </div>
          </div>

          {/* Latency Breakdown */}
          <div className="bg-surface-2 border border-surface-4 rounded p-3">
            <p className="text-xs text-muted mb-2">Latency Breakdown</p>
            <div className="flex gap-6 text-xs font-mono">
              <span>Embedding: <span className="text-zinc-200">{result.embedding_latency_ms.toFixed(0)}ms</span></span>
              <span>Retrieval: <span className="text-zinc-200">{result.retrieval_latency_ms.toFixed(0)}ms</span></span>
              <span>Generation: <span className="text-zinc-200">{result.generation_latency_ms.toFixed(0)}ms</span></span>
            </div>
          </div>

          {/* Answer */}
          <div className="bg-surface-2 border border-surface-4 rounded p-4">
            <h3 className="text-sm font-medium mb-3 text-zinc-300">Answer</h3>
            <div className="text-sm text-zinc-200 whitespace-pre-wrap leading-relaxed">
              {result.answer}
            </div>
          </div>

          {/* Sources */}
          {result.sources.length > 0 && (
            <div className="bg-surface-2 border border-surface-4 rounded p-4">
              <h3 className="text-sm font-medium mb-3 text-zinc-300">Sources ({result.sources.length})</h3>
              <div className="space-y-3">
                {result.sources.map((source, i) => (
                  <div key={i} className="border border-surface-3 rounded p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2 text-xs">
                        <FileText size={12} className="text-accent" />
                        <span className="font-mono text-zinc-300">{source.document_filename}</span>
                        <span className="text-muted">Chunk {source.chunk_index}</span>
                      </div>
                      <span className="text-xs font-mono text-muted">
                        Score: {source.score.toFixed(4)}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-400 line-clamp-3">{source.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Trace ID */}
          {result.trace_id && (
            <p className="text-xs text-muted font-mono">
              Trace: {result.trace_id} · Query Log: {result.query_log_id}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
