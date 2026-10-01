'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { api, EvalRunDetail } from '@/lib/api'
import { ArrowLeft, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import Link from 'next/link'

export default function EvaluationDetailPage() {
  const params = useParams()
  const [run, setRun] = useState<EvalRunDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (params.id) {
      api.getEvaluation(params.id as string)
        .then(setRun)
        .finally(() => setLoading(false))
    }
  }, [params.id])

  if (loading) return <div className="text-muted">Loading...</div>
  if (!run) return <div className="text-danger">Evaluation not found</div>

  return (
    <div>
      <Link href="/evaluations" className="flex items-center gap-1 text-muted hover:text-zinc-200 text-sm mb-4">
        <ArrowLeft size={14} /> Back to evaluations
      </Link>

      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-xl font-semibold">Evaluation Run</h1>
        <span className="font-mono text-accent text-sm">{run.strategy}</span>
        {run.regression_detected && (
          <span className="flex items-center gap-1 text-danger text-xs bg-danger/10 px-2 py-1 rounded">
            <AlertTriangle size={12} /> Regression Detected
          </span>
        )}
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-6 gap-3 mb-6">
        {[
          { label: 'Hit@1', value: `${(run.hit_at_1 * 100).toFixed(1)}%` },
          { label: 'Hit@3', value: `${(run.hit_at_3 * 100).toFixed(1)}%` },
          { label: 'Hit@5', value: `${(run.hit_at_5 * 100).toFixed(1)}%` },
          { label: 'MRR', value: run.mrr.toFixed(3) },
          { label: 'P50', value: `${run.p50_latency_ms.toFixed(0)}ms` },
          { label: 'P95', value: `${run.p95_latency_ms.toFixed(0)}ms` },
        ].map(m => (
          <div key={m.label} className="bg-surface-2 border border-surface-4 rounded p-3">
            <p className="text-xs text-muted mb-1">{m.label}</p>
            <p className="text-lg font-mono font-semibold">{m.value}</p>
          </div>
        ))}
      </div>

      {/* Configuration */}
      <div className="bg-surface-2 border border-surface-4 rounded p-4 mb-6">
        <h2 className="text-sm font-medium mb-2 text-zinc-300">Configuration</h2>
        <div className="grid grid-cols-4 gap-4 text-xs">
          <div><span className="text-muted">LLM:</span> <span className="font-mono">{run.llm_model || '-'}</span></div>
          <div><span className="text-muted">Embeddings:</span> <span className="font-mono">{run.embedding_model || '-'}</span></div>
          <div><span className="text-muted">Reranker:</span> <span className="font-mono">{run.reranker_model || '-'}</span></div>
          <div><span className="text-muted">Top-K:</span> <span className="font-mono">{run.top_k}</span></div>
        </div>
      </div>

      {/* Per-Case Results */}
      <div className="bg-surface-2 border border-surface-4 rounded overflow-hidden">
        <h2 className="text-sm font-medium p-4 border-b border-surface-4 text-zinc-300">
          Case Results ({run.case_results.length})
        </h2>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-surface-4 text-muted">
              <th className="text-left px-4 py-2 font-medium">Case ID</th>
              <th className="text-left px-4 py-2 font-medium">Question</th>
              <th className="text-center px-4 py-2 font-medium">Hit@1</th>
              <th className="text-center px-4 py-2 font-medium">Hit@5</th>
              <th className="text-right px-4 py-2 font-medium">MRR</th>
              <th className="text-right px-4 py-2 font-medium">Latency</th>
            </tr>
          </thead>
          <tbody>
            {run.case_results.map((c: any) => (
              <tr key={c.case_id} className="border-b border-surface-3 last:border-0">
                <td className="px-4 py-2 font-mono text-muted">{c.case_id}</td>
                <td className="px-4 py-2 text-zinc-300 max-w-xs truncate">{c.question}</td>
                <td className="px-4 py-2 text-center">
                  {c.hit_at_1 ? <CheckCircle size={12} className="text-success inline" /> : <XCircle size={12} className="text-muted inline" />}
                </td>
                <td className="px-4 py-2 text-center">
                  {c.hit_at_5 ? <CheckCircle size={12} className="text-success inline" /> : <XCircle size={12} className="text-muted inline" />}
                </td>
                <td className="px-4 py-2 text-right font-mono">{c.mrr.toFixed(3)}</td>
                <td className="px-4 py-2 text-right font-mono text-muted">{c.latency_ms.toFixed(0)}ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
