import { useCallback, useEffect, useState } from 'react'
import { approveDraft, fetchAllTopics, fetchDrafts, rejectDraft } from '../api/admin'
import { EmptyState, ErrorState, Skeleton } from '../components/Feedback'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import type { AIDraft, Topic } from '../types'
import './AdminPages.css'

function DraftRow({ draft, topics, onDecided }: { draft: AIDraft; topics: Topic[]; onDecided: () => void }) {
  const { authFetch } = useAuth()
  const { showToast } = useToast()
  const [topicId, setTopicId] = useState('')
  const [busy, setBusy] = useState(false)

  const handleApprove = () => {
    if (!topicId) {
      showToast('Pick a topic first', 'error')
      return
    }
    setBusy(true)
    approveDraft(authFetch, draft.id, Number(topicId))
      .then((q) => {
        showToast(`Approved -> created Question #${q.id}`, 'success')
        onDecided()
      })
      .catch(() => showToast('Approve failed', 'error'))
      .finally(() => setBusy(false))
  }

  const handleReject = () => {
    setBusy(true)
    rejectDraft(authFetch, draft.id)
      .then(() => {
        showToast('Draft rejected', 'success')
        onDecided()
      })
      .catch(() => showToast('Reject failed', 'error'))
      .finally(() => setBusy(false))
  }

  return (
    <li>
      <strong>{draft.question_text}</strong>{' '}
      <span className="admin-list-meta">
        ({draft.status} — from "{draft.source_article_title}")
      </span>
      <p className="admin-list-meta">{draft.answer}</p>
      {draft.status === 'generated' && (
        <div className="admin-form-row">
          <select value={topicId} onChange={(e) => setTopicId(e.target.value)}>
            <option value="">Choose topic...</option>
            {topics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <button type="button" className="admin-button" onClick={handleApprove} disabled={busy}>
            Approve
          </button>
          <button type="button" className="admin-button admin-button-secondary" onClick={handleReject} disabled={busy}>
            Reject
          </button>
        </div>
      )}
    </li>
  )
}

function AdminDraftsPage() {
  const { authFetch } = useAuth()
  const { showToast } = useToast()

  const [drafts, setDrafts] = useState<AIDraft[]>([])
  const [topics, setTopics] = useState<Topic[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('generated')

  const [articleId, setArticleId] = useState('1')
  const [genLoading, setGenLoading] = useState(false)

  const load = useCallback(() => {
    setError(null)
    Promise.all([fetchDrafts(authFetch, statusFilter || undefined), fetchAllTopics()])
      .then(([draftData, topicData]) => {
        setDrafts(draftData)
        setTopics(topicData)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [authFetch, statusFilter])

  useEffect(() => {
    load()
  }, [load])

  const handleGenerateFromArticle = () => {
    setGenLoading(true)
    authFetch(`/api/ai/drafts/article/${articleId}`, { method: 'POST' })
      .then(async (r) => {
        const body = await r.json().catch(() => ({}))
        if (!r.ok) throw new Error(body.detail || `Request failed (${r.status})`)
        return body
      })
      .then(() => {
        showToast('Draft generated', 'success')
        load()
      })
      .catch((err: Error) => showToast(err.message, 'error'))
      .finally(() => setGenLoading(false))
  }

  return (
    <div className="admin-page">
      <h1>AI Drafts</h1>
      <p className="admin-subtitle">Review, approve, or reject AI-generated draft questions.</p>

      {error && <ErrorState message={error} onRetry={load} />}

      <div className="admin-card">
        <h2>Generate From Article</h2>
        <div className="admin-form-row">
          <input type="text" value={articleId} onChange={(e) => setArticleId(e.target.value)} placeholder="Source article id" />
          <button type="button" className="admin-button" onClick={handleGenerateFromArticle} disabled={genLoading}>
            {genLoading ? 'Generating...' : 'Generate Draft'}
          </button>
        </div>
      </div>

      <div className="admin-card">
        <div className="admin-form-row">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="generated">Pending review</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="">All</option>
          </select>
        </div>
        {loading ? (
          <Skeleton height={140} />
        ) : drafts.length === 0 ? (
          <EmptyState title="No drafts in this status" />
        ) : (
          <ul className="admin-list">
            {drafts.map((d) => (
              <DraftRow key={d.id} draft={d} topics={topics} onDecided={load} />
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export default AdminDraftsPage
