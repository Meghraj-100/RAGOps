'use client'

import { useEffect, useState } from 'react'
import { api, HealthStatus } from '@/lib/api'
import { CheckCircle, XCircle } from 'lucide-react'

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.health()
      .then(setHealth)
      .catch(() => setHealth(null))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-semibold mb-6">Settings</h1>

      {/* System Health */}
      <div className="bg-surface-2 border border-surface-4 rounded p-6 mb-6">
        <h2 className="text-sm font-medium mb-4 text-zinc-300">System Health</h2>
        {loading ? (
          <p className="text-muted text-sm">Checking...</p>
        ) : health ? (
          <div className="space-y-3">
            <StatusRow label="API" status={health.status === 'healthy'} value={health.status} />
            <StatusRow label="Database" status={health.database === 'healthy'} value={health.database} />
            <StatusRow label="LLM" status={health.llm === 'configured'} value={health.llm} />
            <StatusRow label="Embedding Model" status={true} value={health.embedding_model} />
          </div>
        ) : (
          <p className="text-danger text-sm">Backend unreachable</p>
        )}
      </div>

      {/* Model Configuration */}
      <div className="bg-surface-2 border border-surface-4 rounded p-6 mb-6">
        <h2 className="text-sm font-medium mb-4 text-zinc-300">Fixed Model Configuration</h2>
        <p className="text-xs text-muted mb-4">
          Models are configured via environment variables. No runtime selection.
        </p>
        <div className="space-y-3 text-xs">
          <ConfigRow label="LLM" value="llama-3.3-70b-versatile (Groq)" />
          <ConfigRow label="Embedding" value="all-MiniLM-L6-v2 (local)" />
          <ConfigRow label="Reranker" value="cross-encoder/ms-marco-MiniLM-L-6-v2 (local)" />
        </div>
      </div>

      {/* API Endpoints */}
      <div className="bg-surface-2 border border-surface-4 rounded p-6">
        <h2 className="text-sm font-medium mb-4 text-zinc-300">API Endpoints</h2>
        <div className="space-y-2 text-xs font-mono">
          {[
            'GET  /api/v1/health',
            'GET  /api/v1/dashboard',
            'GET  /api/v1/documents',
            'POST /api/v1/documents/ingest',
            'POST /api/v1/query',
            'GET  /api/v1/queries',
            'GET  /api/v1/evaluations',
            'POST /api/v1/evaluations/run',
            'GET  /metrics',
          ].map(ep => (
            <p key={ep} className="text-zinc-400">{ep}</p>
          ))}
        </div>
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block mt-4 text-accent text-xs hover:underline"
        >
          Open FastAPI Docs →
        </a>
      </div>
    </div>
  )
}

function StatusRow({ label, status, value }: { label: string; status: boolean; value: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-surface-3 last:border-0">
      <span className="text-sm text-zinc-300">{label}</span>
      <div className="flex items-center gap-2">
        {status ? <CheckCircle size={14} className="text-success" /> : <XCircle size={14} className="text-danger" />}
        <span className="text-xs font-mono text-muted">{value}</span>
      </div>
    </div>
  )
}

function ConfigRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-surface-3 last:border-0">
      <span className="text-zinc-300">{label}</span>
      <span className="font-mono text-muted">{value}</span>
    </div>
  )
}
