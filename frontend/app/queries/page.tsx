'use client'

import { useEffect, useState } from 'react'
import { api, QueryLog, QueryLogDetail } from '@/lib/api'
import { ScrollText, X, Clock, Layers } from 'lucide-react'

export default function QueriesPage() {
  const [queries, setQueries] = useState<QueryLog[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<QueryLogDetail | null>(null)

  useEffect(() => {
    api.listQueries(100)
      .then(setQueries)
      .finally(() => setLoading(false))
  }, [])

  const handleSelect = async (id: string) => {
    const detail = await api.getQuery(id)
    setSelected(detail)
  }

  return (
    <div className="flex gap-6">
      {/* Query List */}
      <div className="flex-1">
        <h1 className="text-xl font-semibold mb-6">Query Log</h1>

        {loading ? (
          <div className="text-muted text-sm">Loading...</div>
        ) : queries.length === 0 ? (
          <div className="text-center py-16 text-muted">
            <ScrollText size={40} className="mx-auto mb-3 opacity-40" />
            <p>No queries yet. Ask questions in the Chat page.</p>
          </div>
        ) : (
          <div className="bg-surface-2 border border-surface-4 rounded overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-4 text-xs text-muted">
                  <th className="text-left px-4 py-3 font-medium">Question</th>
                  <th className="text-left px-4 py-3 font-medium">Strategy</th>
                  <th className="text-right px-4 py-3 font-medium">Chunks</th>
                  <th className="text-right px-4 py-3 font-medium">Latency</th>
                  <th className="text-center px-4 py-3 font-medium">Status</th>
                  <th className="text-left px-4 py-3 font-medium">Time</th>
                </tr>
              </thead>
              <tbody>
                {queries.map(q => (
                  <tr
                    key={q.id}
                    onClick={() => handleSelect(q.id)}
                    className="border-b border-surface-3 last:border-0 hover:bg-surface-3/50 cursor-pointer"
                  >
                    <td className="px-4 py-3 text-zinc-200 max-w-xs truncate">{q.question}</td>
                    <td className="px-4 py-3 font-mono text-accent text-xs">{q.retrieval_strategy}</td>
                    <td className="px-4 py-3 text-right font-mono">{q.num_chunks_retrieved}</td>
                    <td className="px-4 py-3 text-right font-mono text-muted">{q.latency_ms.toFixed(0)}ms</td>
                    <td className="px-4 py-3 text-center">
                      {q.error ? (
                        <span className="text-danger text-xs">error</span>
                      ) : (
                        <span className="text-success text-xs">ok</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted">
                      {new Date(q.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detail Panel */}
      {selected && (
        <div className="w-96 bg-surface-2 border border-surface-4 rounded p-4 h-fit sticky top-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium">Query Detail</h2>
            <button onClick={() => setSelected(null)} className="text-muted hover:text-zinc-200">
              <X size={14} />
            </button>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-muted">Question</span>
              <p className="text-zinc-200 mt-1">{selected.question}</p>
            </div>

            {selected.answer && (
              <div>
                <span className="text-muted">Answer</span>
                <p className="text-zinc-300 mt-1 text-xs leading-relaxed max-h-32 overflow-y-auto">
                  {selected.answer}
                </p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-2">
              <div className="bg-surface-3 rounded p-2">
                <span className="text-muted">Strategy</span>
                <p className="font-mono text-accent">{selected.retrieval_strategy}</p>
              </div>
              <div className="bg-surface-3 rounded p-2">
                <span className="text-muted">Total Latency</span>
                <p className="font-mono">{selected.latency_ms.toFixed(0)}ms</p>
              </div>
            </div>

            <div className="bg-surface-3 rounded p-2">
              <span className="text-muted">Latency Breakdown</span>
              <div className="mt-1 space-y-1 font-mono">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Embedding</span>
                  <span>{selected.embedding_latency_ms.toFixed(0)}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Retrieval</span>
                  <span>{selected.retrieval_latency_ms.toFixed(0)}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Generation</span>
                  <span>{selected.generation_latency_ms.toFixed(0)}ms</span>
                </div>
              </div>
            </div>

            {selected.token_usage && (
              <div className="bg-surface-3 rounded p-2">
                <span className="text-muted">Token Usage</span>
                <div className="mt-1 font-mono">
                  <span className="text-zinc-400">Prompt: </span>{selected.token_usage.prompt_tokens}
                  <span className="text-zinc-400 ml-2">Completion: </span>{selected.token_usage.completion_tokens}
                </div>
              </div>
            )}

            {selected.trace_id && (
              <div className="bg-surface-3 rounded p-2">
                <span className="text-muted">Trace ID</span>
                <p className="font-mono text-[10px] break-all text-zinc-400 mt-1">{selected.trace_id}</p>
              </div>
            )}

            {selected.error && (
              <div className="bg-danger/10 border border-danger/20 rounded p-2">
                <span className="text-danger">Error</span>
                <p className="text-danger text-xs mt-1">{selected.error}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
