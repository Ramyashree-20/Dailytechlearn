import { useCallback, useEffect, useState } from 'react'
import { fetchPipelineStatus, fetchSourceArticles, replenishContent } from '../api/admin'
import { EmptyState, ErrorState, Skeleton } from '../components/Feedback'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import type { PipelineStatus, SourceArticle } from '../types'
import './AdminPages.css'

type ClassificationResult = {
  classification: {
    category: string
    topic: string
    difficulty: string
    relevance_score: number
    reasoning: string
  }
  matched_category_id: number | null
  matched_topic_id: number | null
}

function AdminContentPage() {
  const { authFetch } = useAuth()
  const { showToast } = useToast()

  const [status, setStatus] = useState<PipelineStatus | null>(null)
  const [articles, setArticles] = useState<SourceArticle[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [replenishing, setReplenishing] = useState(false)

  const [classifyArticleId, setClassifyArticleId] = useState('1')
  const [classifyLoading, setClassifyLoading] = useState(false)
  const [classification, setClassification] = useState<ClassificationResult | null>(null)
  const [classifyError, setClassifyError] = useState<string | null>(null)

  const load = useCallback(() => {
    setError(null)
    Promise.all([fetchPipelineStatus(authFetch), fetchSourceArticles(authFetch, 15)])
      .then(([statusData, articleData]) => {
        setStatus(statusData)
        setArticles(articleData)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [authFetch])

  useEffect(() => {
    load()
  }, [load])

  const handleReplenish = () => {
    setReplenishing(true)
    replenishContent(authFetch)
      .then((result) => {
        showToast(`Generated ${result.generated} draft(s)`, 'success')
        load()
      })
      .catch(() => showToast('Replenish failed', 'error'))
      .finally(() => setReplenishing(false))
  }

  const runClassification = () => {
    setClassifyLoading(true)
    setClassifyError(null)
    setClassification(null)
    authFetch(`/api/content/classify/${classifyArticleId}`, { method: 'POST' })
      .then(async (r) => {
        const body = await r.json().catch(() => ({}))
        if (!r.ok) throw new Error(body.detail || `Request failed (${r.status})`)
        return body
      })
      .then(setClassification)
      .catch((err: Error) => setClassifyError(err.message))
      .finally(() => setClassifyLoading(false))
  }

  return (
    <div className="admin-page">
      <h1>Content Pipeline</h1>
      <p className="admin-subtitle">Ingested articles, pool health, and content classification.</p>

      {error && <ErrorState message={error} onRetry={load} />}

      <div className="admin-card">
        <h2>Pool Health</h2>
        {loading ? (
          <Skeleton height={80} />
        ) : (
          status && (
            <>
              <div className="admin-stat-grid">
                <div className="admin-stat">
                  <span className="admin-stat-value">{status.total_source_articles}</span>
                  <span className="admin-stat-label">Source Articles</span>
                </div>
                <div className="admin-stat">
                  <span className="admin-stat-value">{status.classified_articles}</span>
                  <span className="admin-stat-label">Classified</span>
                </div>
                <div className="admin-stat">
                  <span className="admin-stat-value">{status.approved_questions}</span>
                  <span className="admin-stat-label">Approved Questions</span>
                </div>
                <div className="admin-stat">
                  <span className="admin-stat-value">{status.recommended_generation_count}</span>
                  <span className="admin-stat-label">Recommended to Generate</span>
                </div>
              </div>
              <button type="button" className="admin-button" onClick={handleReplenish} disabled={replenishing}>
                {replenishing ? 'Replenishing...' : 'Replenish Content'}
              </button>
            </>
          )
        )}
      </div>

      <div className="admin-card">
        <h2>Content Classification</h2>
        <p className="admin-subtitle">Ask Groq which category/topic a source article best fits — read-only recommendation.</p>
        <div className="admin-form-row">
          <input
            type="text"
            value={classifyArticleId}
            onChange={(e) => setClassifyArticleId(e.target.value)}
            placeholder="Source article id"
          />
          <button type="button" className="admin-button" onClick={runClassification} disabled={classifyLoading}>
            {classifyLoading ? 'Classifying...' : 'Classify'}
          </button>
        </div>
        {classifyError && <ErrorState message={classifyError} />}
        {classification && (
          <div className="admin-result-message">
            <strong>{classification.classification.category}</strong> / {classification.classification.topic} —{' '}
            {classification.classification.difficulty}, relevance {classification.classification.relevance_score}/5
            <br />
            {classification.classification.reasoning}
          </div>
        )}
      </div>

      <div className="admin-card">
        <h2>Source Articles</h2>
        {loading ? (
          <Skeleton height={100} />
        ) : articles.length === 0 ? (
          <EmptyState title="No articles ingested yet" />
        ) : (
          <ul className="admin-list">
            {articles.map((a) => (
              <li key={a.id}>
                {a.title}{' '}
                <span className="admin-list-meta">
                  ({a.source_name}
                  {a.published_at ? `, ${a.published_at.slice(0, 10)}` : ''})
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export default AdminContentPage
