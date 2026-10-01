'use client'

import { useEffect, useState } from 'react'
import { api, DashboardStats } from '@/lib/api'
import { Activity, FileText, MessageSquare, FlaskConical, Clock, AlertTriangle } from 'lucide-react'

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.dashboard()
      .then(setStats)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-muted">Loading dashboard...</div>
  if (error) return <div className="text-danger">Error: {error}</div>
  if (!stats) return null

  return (
    <div>
      <h1 className="text-xl font-semibold mb-6">Dashboard</h1>

      {/* Stat Cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard icon={FileText} label="Documents" value={stats.total_documents} />
        <StatCard icon={MessageSquare} label="Chunks" value={stats.total_chunks.toLocaleString()} />
        <StatCard icon={Activity} label="Queries" value={stats.total_queries} />
        <StatCard icon={FlaskConical} label="Eval Runs" value={stats.total_eval_runs} />
      </div>

      {/* Latency & Error */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <MetricCard label="Avg Latency" value={`${stats.avg_latency_ms.toFixed(0)} ms`} icon={Clock} />
        <MetricCard label="P95 Latency" value={`${stats.p95_latency_ms.toFixed(0)} ms`} icon={Clock} />
        <MetricCard
          label="Error Rate"
          value={`${(stats.error_rate * 100).toFixed(1)}%`}
          icon={AlertTriangle}
          danger={stats.error_rate > 0.05}
        />
      </div>

      {/* Latest Eval */}
      {stats.latest_eval && (
        <div className="bg-surface-2 border border-surface-4 rounded p-4 mb-8">
          <h2 className="text-sm font-medium mb-3 text-zinc-300">Latest Evaluation</h2>
          <div className="grid grid-cols-5 gap-4 text-sm">
            <div>
              <span className="text-muted text-xs">Strategy</span>
              <p className="font-mono text-accent">{stats.latest_eval.strategy}</p>
            </div>
            <div>
              <span className="text-muted text-xs">Hit@1</span>
              <p className="font-mono">{(stats.latest_eval.hit_at_1 * 100).toFixed(1)}%</p>
            </div>
            <div>
              <span className="text-muted text-xs">Hit@5</span>
              <p className="font-mono">{(stats.latest_eval.hit_at_5 * 100).toFixed(1)}%</p>
            </div>
            <div>
              <span className="text-muted text-xs">MRR</span>
              <p className="font-mono">{stats.latest_eval.mrr.toFixed(3)}</p>
            </div>
            <div>
              <span className="text-muted text-xs">Regression</span>
              <p className={`font-mono ${stats.latest_eval.regression_detected ? 'text-danger' : 'text-success'}`}>
                {stats.latest_eval.regression_detected ? 'DETECTED' : 'None'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Recent Queries */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-surface-2 border border-surface-4 rounded p-4">
          <h2 className="text-sm font-medium mb-3 text-zinc-300">Recent Queries</h2>
          {stats.recent_queries.length === 0 ? (
            <p className="text-muted text-sm">No queries yet</p>
          ) : (
            <div className="space-y-2">
              {stats.recent_queries.map(q => (
                <div key={q.id} className="flex items-center justify-between text-xs py-1.5 border-b border-surface-3 last:border-0">
                  <span className="truncate mr-4 text-zinc-300 max-w-[260px]">{q.question}</span>
                  <span className="text-muted font-mono shrink-0">{q.latency_ms.toFixed(0)}ms</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-surface-2 border border-surface-4 rounded p-4">
          <h2 className="text-sm font-medium mb-3 text-zinc-300">Recent Evaluations</h2>
          {stats.recent_evals.length === 0 ? (
            <p className="text-muted text-sm">No evaluations yet</p>
          ) : (
            <div className="space-y-2">
              {stats.recent_evals.map(e => (
                <div key={e.id} className="flex items-center justify-between text-xs py-1.5 border-b border-surface-3 last:border-0">
                  <span className="font-mono text-accent">{e.strategy}</span>
                  <span className="text-muted font-mono">MRR {e.mrr.toFixed(3)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon: Icon, label, value }: { icon: any; label: string; value: string | number }) {
  return (
    <div className="bg-surface-2 border border-surface-4 rounded p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon size={14} className="text-muted" />
        <span className="text-xs text-muted">{label}</span>
      </div>
      <p className="text-2xl font-semibold font-mono">{value}</p>
    </div>
  )
}

function MetricCard({ icon: Icon, label, value, danger }: { icon: any; label: string; value: string; danger?: boolean }) {
  return (
    <div className="bg-surface-2 border border-surface-4 rounded p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon size={14} className="text-muted" />
        <span className="text-xs text-muted">{label}</span>
      </div>
      <p className={`text-lg font-semibold font-mono ${danger ? 'text-danger' : ''}`}>{value}</p>
    </div>
  )
}
