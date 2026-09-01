import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchPipelineStatus } from '../api/admin'
import { ErrorState, Skeleton } from '../components/Feedback'
import { useAuth } from '../context/AuthContext'
import type { PipelineStatus } from '../types'
import './AdminPages.css'

function AdminOverviewPage() {
  const { authFetch } = useAuth()
  const [status, setStatus] = useState<PipelineStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    setError(null)
    fetchPipelineStatus(authFetch)
      .then(setStatus)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [authFetch])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="admin-page">
      <h1>Admin Overview</h1>
      <p className="admin-subtitle">Content pipeline health and quick access to admin tools.</p>

      {error && <ErrorState message={error} onRetry={load} />}

      <div className="admin-card">
        <h2>Pipeline Health</h2>
        {loading ? (
          <Skeleton height={80} />
        ) : (
          status && (
            <div className="admin-stat-grid">
              <div className="admin-stat">
                <span className="admin-stat-value">{status.approved_questions}</span>
                <span className="admin-stat-label">Approved Questions</span>
              </div>
              <div className="admin-stat">
                <span className="admin-stat-value">{status.pending_drafts}</span>
                <span className="admin-stat-label">Pending Drafts</span>
              </div>
              <div className="admin-stat">
                <span className="admin-stat-value">{status.eligible_candidates}</span>
                <span className="admin-stat-label">Eligible Candidates</span>
              </div>
              <div className="admin-stat">
                <span className="admin-stat-value">{status.target_new_pool_size}</span>
                <span className="admin-stat-label">Target Pool Size</span>
              </div>
              <div className="admin-stat">
                <span className="admin-stat-value">{status.pool_status}</span>
                <span className="admin-stat-label">Pool Status</span>
              </div>
            </div>
          )
        )}
      </div>

      <div className="admin-quick-links">
        <Link to="/admin/content" className="admin-quick-link">
          <span className="admin-quick-link-icon">📥</span>
          <span className="admin-quick-link-title">Content Pipeline</span>
          <span className="admin-quick-link-desc">Ingest, classify, and replenish content.</span>
        </Link>
        <Link to="/admin/candidates" className="admin-quick-link">
          <span className="admin-quick-link-icon">🎯</span>
          <span className="admin-quick-link-title">Candidates</span>
          <span className="admin-quick-link-desc">Eligible articles ranked for generation.</span>
        </Link>
        <Link to="/admin/drafts" className="admin-quick-link">
          <span className="admin-quick-link-icon">📝</span>
          <span className="admin-quick-link-title">AI Drafts</span>
          <span className="admin-quick-link-desc">Review, approve, or reject generated drafts.</span>
        </Link>
        <Link to="/admin/taxonomy" className="admin-quick-link">
          <span className="admin-quick-link-icon">🗂️</span>
          <span className="admin-quick-link-title">Taxonomy</span>
          <span className="admin-quick-link-desc">Browse categories and topics.</span>
        </Link>
      </div>
    </div>
  )
}

export default AdminOverviewPage
