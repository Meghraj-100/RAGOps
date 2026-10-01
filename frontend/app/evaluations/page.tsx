'use client'

import { useEffect, useState } from 'react'
import { api, EvalRun } from '@/lib/api'
import { FlaskConical, Loader2, AlertTriangle, CheckCircle } from 'lucide-react'
import Link from 'next/link'

const STRATEGIES = ['vector-similarity', 'hybrid-search', 'reranking', 'multi-query']

export default function EvaluationsPage() {
  const [runs, setRuns] = useState<EvalRun[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [strategy, setStrategy] = useState('vector-similarity')
  const [error, setError] = useState<string | null>(null)
  const [compareA, setCompareA] = useState<string>('')
  const [compareB, setCompareB] = useState<string>('')
  const [comparison, setComparison] = useState<any>(null)

  const loadRuns = () => {
    api.listEvaluations()
      .then(setRuns)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadRuns() }, [])

  const handleRun = async () => {
    setRunning(true)
    setError(null)
    try {
      await api.runEvaluation(strategy, 'default', 5)
      loadRuns()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setRunning(false)
    }
  }

  const handleCompare = async () => {
    if (!compareA || !compareB) return
    try {
      const result = await api.compareEvaluations(compareA, compareB)
      setComparison(result)
    } catch (err: any) {
      setError(err.message)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Evaluations</h1>
        <div className="flex gap-2">
          <select
            value={strategy}
            onChange={e => setStrategy(e.target.value)}
            className="bg-surface-2 border border-surface-4 rounded px-3 py-2 text-sm text-zinc-200"
          >
            {STRATEGIES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <button
            onClick={handleRun}
            disabled={running}
            className="flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-sm rounded transition-colors"
          >
            {running ? <Loader2 size={14} className="animate-spin" /> : <FlaskConical size={14} />}
            {running ? 'Running...' : 'Run Evaluation'}
          </button>
        </div>
      </div>

      {error && <div className="bg-danger/10 border border-danger/20 text-danger text-sm p-3 rounded mb-4">{error}</div>}

      {/* Compare Tool */}
      {runs.length >= 2 && (
        <div className="bg-surface-2 border border-surface-4 rounded p-4 mb-6">
          <h2 className="text-sm font-medium mb-3 text-zinc-300">Compare Runs</h2>
          <div className="flex gap-3 items-end">
            <div>
              <label className="text-xs text-muted block mb-1">Run A</label>
              <select
                value={compareA}
                onChange={e => setCompareA(e.target.value)}
                className="bg-surface-3 border border-surface-4 rounded px-3 py-2 text-xs text-zinc-200"
              >
                <option value="">Select...</option>
                {runs.map(r => (
                  <option key={r.id} value={r.id}>
                    {r.strategy} — {new Date(r.created_at).toLocaleString()}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-muted block mb-1">Run B</label>
              <select
                value={compareB}
                onChange={e => setCompareB(e.target.value)}
                className="bg-surface-3 border border-surface-4 rounded px-3 py-2 text-xs text-zinc-200"
              >
                <option value="">Select...</option>
                {runs.map(r => (
                  <option key={r.id} value={r.id}>
                    {r.strategy} — {new Date(r.created_at).toLocaleString()}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={handleCompare}
              disabled={!compareA || !compareB}
              className="px-4 py-2 bg-surface-4 hover:bg-surface-3 disabled:opacity-50 text-sm rounded transition-colors"
            >
              Compare
            </button>
          </div>

          {comparison && (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-surface-4 text-muted">
                    <th className="text-left py-2 px-3">Metric</th>
                    <th className="text-right py-2 px-3">Run A</th>
                    <th className="text-right py-2 px-3">Run B</th>
                    <th className="text-right py-2 px-3">Delta</th>
                  </tr>
                </thead>
                <tbody className="font-mono">
                  {[
                    { key: 'hit_at_1', label: 'Hit@1', pct: true },
                    { key: 'hit_at_3', label: 'Hit@3', pct: true },
                    { key: 'hit_at_5', label: 'Hit@5', pct: true },
                    { key: 'mrr', label: 'MRR', pct: false },
                    { key: 'avg_latency_ms', label: 'Avg Latency', pct: false, unit: 'ms' },
                    { key: 'p95_latency_ms', label: 'P95 Latency', pct: false, unit: 'ms' },
                  ].map(m => {
                    const a = comparison.run_a[m.key]
                    const b = comparison.run_b[m.key]
                    const d = comparison.deltas[m.key]
                    return (
                      <tr key={m.key} className="border-b border-surface-3">
                        <td className="py-2 px-3 text-zinc-300">{m.label}</td>
                        <td className="py-2 px-3 text-right">{m.pct ? `${(a * 100).toFixed(1)}%` : m.unit ? `${a.toFixed(0)}${m.unit}` : a.toFixed(3)}</td>
                        <td className="py-2 px-3 text-right">{m.pct ? `${(b * 100).toFixed(1)}%` : m.unit ? `${b.toFixed(0)}${m.unit}` : b.toFixed(3)}</td>
                        <td className={`py-2 px-3 text-right ${d > 0 && !m.unit ? 'text-success' : d < 0 && !m.unit ? 'text-danger' : ''}`}>
                          {d > 0 ? '+' : ''}{m.pct ? `${(d * 100).toFixed(1)}pp` : m.unit ? `${d.toFixed(0)}${m.unit}` : d.toFixed(3)}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Runs Table */}
      {loading ? (
        <div className="text-muted text-sm">Loading...</div>
      ) : runs.length === 0 ? (
        <div className="text-center py-16 text-muted">
          <FlaskConical size={40} className="mx-auto mb-3 opacity-40" />
          <p>No evaluation runs yet. Upload documents and run an evaluation.</p>
        </div>
      ) : (
        <div className="bg-surface-2 border border-surface-4 rounded overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-4 text-xs text-muted">
                <th className="text-left px-4 py-3 font-medium">Strategy</th>
                <th className="text-right px-4 py-3 font-medium">Cases</th>
                <th className="text-right px-4 py-3 font-medium">Hit@1</th>
                <th className="text-right px-4 py-3 font-medium">Hit@5</th>
                <th className="text-right px-4 py-3 font-medium">MRR</th>
                <th className="text-right px-4 py-3 font-medium">P95</th>
                <th className="text-center px-4 py-3 font-medium">Regression</th>
                <th className="text-left px-4 py-3 font-medium">Date</th>
              </tr>
            </thead>
            <tbody>
              {runs.map(run => (
                <tr key={run.id} className="border-b border-surface-3 last:border-0 hover:bg-surface-3/50 cursor-pointer">
                  <td className="px-4 py-3">
                    <Link href={`/evaluations/${run.id}`} className="font-mono text-accent hover:underline">
                      {run.strategy}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-right font-mono">{run.total_cases}</td>
                  <td className="px-4 py-3 text-right font-mono">{(run.hit_at_1 * 100).toFixed(1)}%</td>
                  <td className="px-4 py-3 text-right font-mono">{(run.hit_at_5 * 100).toFixed(1)}%</td>
                  <td className="px-4 py-3 text-right font-mono">{run.mrr.toFixed(3)}</td>
                  <td className="px-4 py-3 text-right font-mono text-muted">{run.p95_latency_ms.toFixed(0)}ms</td>
                  <td className="px-4 py-3 text-center">
                    {run.regression_detected ? (
                      <AlertTriangle size={14} className="text-danger inline" />
                    ) : (
                      <CheckCircle size={14} className="text-success inline" />
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">{new Date(run.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
