import { useCallback, useEffect, useState } from 'react'
import { fetchCandidates, generateDraftsBatch } from '../api/admin'
import { EmptyState, ErrorState, Skeleton } from '../components/Feedback'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import type { Candidate } from '../types'
import './AdminPages.css'

function AdminCandidatesPage() {
  const { authFetch } = useAuth()
  const { showToast } = useToast()

  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)

  const load = useCallback(() => {
    setError(null)
    fetchCandidates(authFetch, 15)
      .then(setCandidates)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [authFetch])

  useEffect(() => {
    load()
  }, [load])

  const handleGenerate = () => {
    setGenerating(true)
    generateDraftsBatch(authFetch, 5)
      .then((result) => {
        showToast(`Generated ${result.generated} draft(s) from ${result.selected} candidate(s)`, 'success')
        load()
      })
      .catch(() => showToast('Draft generation failed', 'error'))
      .finally(() => setGenerating(false))
  }

  return (
    <div className="admin-page">
      <h1>Learning Candidates</h1>
      <p className="admin-subtitle">
        Classified articles eligible for new-content generation, ranked by importance + relevance + freshness.
      </p>

      {error && <ErrorState message={error} onRetry={load} />}

      <div className="admin-card">
        <button type="button" className="admin-button" onClick={handleGenerate} disabled={generating}>
          {generating ? 'Generating...' : 'Generate Drafts (up to 5)'}
        </button>
      </div>

      <div className="admin-card">
        <h2>Ranked Candidates</h2>
        {loading ? (
          <Skeleton height={140} />
        ) : candidates.length === 0 ? (
          <EmptyState title="No eligible candidates right now" />
        ) : (
          <ul className="admin-list">
            {candidates.map((c) => (
              <li key={c.article_id}>
                {c.title} <span className="admin-list-meta">({c.category_name ?? '?'} / {c.topic_name ?? '?'})</span>
                <br />
                <span className="admin-list-meta">
                  score {c.selection_score.toFixed(2)} — importance {c.importance_score.toFixed(2)}, relevance{' '}
                  {c.relevance_score.toFixed(2)}, freshness {c.freshness_score.toFixed(2)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export default AdminCandidatesPage
