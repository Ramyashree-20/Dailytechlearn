import { useCallback, useEffect, useState } from 'react'
import { fetchDashboard } from '../api/learning'
import { EmptyState, ErrorState, Skeleton } from '../components/Feedback'
import { useAuth } from '../context/AuthContext'
import type { DashboardData } from '../types'
import './ProgressPage.css'

const DIFFICULTY_ORDER = ['beginner', 'intermediate', 'advanced']
const DIFFICULTY_LABEL: Record<string, string> = { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced' }

function ProgressPage() {
  const { authFetch } = useAuth()
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    setError(null)
    fetchDashboard(authFetch)
      .then(setDashboard)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [authFetch])

  useEffect(() => {
    load()
  }, [load])

  if (error) return <ErrorState message={error} onRetry={load} />

  const maxDifficultyCount = dashboard ? Math.max(1, ...Object.values(dashboard.difficulty_breakdown)) : 1

  return (
    <div className="progress-page">
      <h1>Your Progress</h1>
      <p className="progress-subtitle">A closer look at how your learning is going.</p>

      <section className="progress-stats">
        {loading || !dashboard ? (
          <>
            <Skeleton height={90} />
            <Skeleton height={90} />
            <Skeleton height={90} />
            <Skeleton height={90} />
          </>
        ) : (
          <>
            <div className="progress-stat-card">
              <span className="progress-stat-value">{dashboard.learned_count}</span>
              <span className="progress-stat-label">Total Learned</span>
            </div>
            <div className="progress-stat-card">
              <span className="progress-stat-value">{dashboard.total_reviews_completed}</span>
              <span className="progress-stat-label">Reviews Completed</span>
            </div>
            <div className="progress-stat-card">
              <span className="progress-stat-value">🔥 {dashboard.current_streak_days}</span>
              <span className="progress-stat-label">Day Streak</span>
            </div>
            <div className="progress-stat-card">
              <span className="progress-stat-value">{dashboard.mastered_count}</span>
              <span className="progress-stat-label">Questions Mastered</span>
            </div>
          </>
        )}
      </section>

      <section className="progress-section">
        <h2>Topic-wise Progress</h2>
        {loading ? (
          <Skeleton height={120} />
        ) : !dashboard || dashboard.topics_in_progress.length === 0 ? (
          <EmptyState title="No progress yet" subtitle="Learn a few questions to see your topic breakdown here." />
        ) : (
          <div className="topic-progress-list">
            {dashboard.topics_in_progress.map((t) => (
              <div key={t.topic_id} className="topic-progress-row">
                <div className="topic-progress-label">
                  <span>{t.topic_name}</span>
                  <span className="topic-progress-count">
                    {t.learned_count}/{t.total_questions}
                  </span>
                </div>
                <div className="progress-bar-track">
                  <div
                    className="progress-bar-fill"
                    style={{ width: `${Math.min(100, (t.learned_count / (t.total_questions || 1)) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="progress-section">
        <h2>Difficulty Breakdown</h2>
        {loading ? (
          <Skeleton height={100} />
        ) : !dashboard || Object.keys(dashboard.difficulty_breakdown).length === 0 ? (
          <EmptyState title="No data yet" subtitle="Learn a few questions to see this breakdown." />
        ) : (
          <div className="difficulty-breakdown">
            {DIFFICULTY_ORDER.filter((d) => dashboard.difficulty_breakdown[d]).map((d) => (
              <div key={d} className="difficulty-row">
                <span className={`difficulty-label difficulty-${d}`}>{DIFFICULTY_LABEL[d]}</span>
                <div className="progress-bar-track">
                  <div
                    className={`progress-bar-fill difficulty-fill-${d}`}
                    style={{ width: `${(dashboard.difficulty_breakdown[d] / maxDifficultyCount) * 100}%` }}
                  />
                </div>
                <span className="difficulty-count">{dashboard.difficulty_breakdown[d]}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export default ProgressPage
