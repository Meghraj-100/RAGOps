'use client'

import { useEffect, useState, useRef } from 'react'
import { api, Document } from '@/lib/api'
import { Upload, Trash2, FileText, Loader2 } from 'lucide-react'

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const loadDocs = () => {
    api.listDocuments()
      .then(data => setDocuments(data.documents))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadDocs() }, [])

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      await api.uploadDocument(file)
      loadDocs()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this document?')) return
    await api.deleteDocument(id)
    loadDocs()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Documents</h1>
        <label className="flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-hover text-white text-sm rounded cursor-pointer transition-colors">
          {uploading ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
          {uploading ? 'Uploading...' : 'Upload Document'}
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.txt,.docx"
            className="hidden"
            onChange={handleUpload}
            disabled={uploading}
          />
        </label>
      </div>

      {error && <div className="bg-danger/10 border border-danger/20 text-danger text-sm p-3 rounded mb-4">{error}</div>}

      {loading ? (
        <div className="text-muted text-sm">Loading documents...</div>
      ) : documents.length === 0 ? (
        <div className="text-center py-16 text-muted">
          <FileText size={40} className="mx-auto mb-3 opacity-40" />
          <p>No documents yet. Upload a PDF, TXT, or DOCX to get started.</p>
        </div>
      ) : (
        <div className="bg-surface-2 border border-surface-4 rounded overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-4 text-xs text-muted">
                <th className="text-left px-4 py-3 font-medium">Filename</th>
                <th className="text-left px-4 py-3 font-medium">Type</th>
                <th className="text-left px-4 py-3 font-medium">Size</th>
                <th className="text-left px-4 py-3 font-medium">Status</th>
                <th className="text-left px-4 py-3 font-medium">Chunks</th>
                <th className="text-left px-4 py-3 font-medium">Created</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {documents.map(doc => (
                <tr key={doc.id} className="border-b border-surface-3 last:border-0 hover:bg-surface-3/50">
                  <td className="px-4 py-3 font-mono text-zinc-200">{doc.filename}</td>
                  <td className="px-4 py-3 text-muted uppercase text-xs">{doc.file_type}</td>
                  <td className="px-4 py-3 text-muted font-mono">{(doc.file_size / 1024).toFixed(1)} KB</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      doc.status === 'completed' ? 'bg-success/10 text-success' :
                      doc.status === 'processing' ? 'bg-warning/10 text-warning' :
                      doc.status === 'failed' ? 'bg-danger/10 text-danger' :
                      'bg-surface-4 text-muted'
                    }`}>
                      {doc.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono">{doc.chunk_count}</td>
                  <td className="px-4 py-3 text-muted text-xs">{new Date(doc.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="text-muted hover:text-danger transition-colors"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
