import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchDashboard, fetchToday } from '../api/learning'
import { EmptyState, ErrorState, Skeleton } from '../components/Feedback'
import { useAuth } from '../context/AuthContext'
import type { DailyLearning, DashboardData } from '../types'
import './DashboardPage.css'

const EMPTY_DAILY: DailyLearning = { new_questions: [], revision_questions: [] }

function greeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

function DashboardPage() {
  const { authFetch, currentUser } = useAuth()
  const navigate = useNavigate()

  const [daily, setDaily] = useState<DailyLearning>(EMPTY_DAILY)
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    setError(null)
    Promise.all([fetchToday(authFetch), fetchDashboard(authFetch)])
      .then(([dailyData, dashboardData]) => {
        setDaily(dailyData)
        setDashboard(dashboardData)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [authFetch])

  useEffect(() => {
    load()
  }, [load])

  const firstName = currentUser?.username ?? currentUser?.email.split('@')[0] ?? ''

  if (error) {
    return <ErrorState message={error} onRetry={load} />
  }

  return (
    <div className="dashboard-page">
      <h1 className="dashboard-greeting">
        {greeting()} 👋 <span className="dashboard-name">{firstName}</span>
      </h1>

      <section className="dashboard-stats">
        {loading || !dashboard ? (
          <>
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} height={78} className="stat-skeleton" />
            ))}
          </>
        ) : (
          <>
            <div className="stat-card stat-streak">
              <span className="stat-icon">🔥</span>
              <span className="stat-value">{dashboard.current_streak_days}</span>
              <span className="stat-label">Current Streak</span>
            </div>
            <div className="stat-card stat-learned">
              <span className="stat-icon">📚</span>
              <span className="stat-value">{dashboard.learned_count}</span>
              <span className="stat-label">Questions Learned</span>
            </div>
            <div className="stat-card stat-mastered">
              <span className="stat-icon">🧠</span>
              <span className="stat-value">{dashboard.mastered_count}</span>
              <span className="stat-label">Questions Mastered</span>
            </div>
            <div className="stat-card stat-progress">
              <span className="stat-icon">📈</span>
              <span className="stat-value">{dashboard.progress_percent}%</span>
              <span className="stat-label">Progress</span>
            </div>
          </>
        )}
      </section>

      <section className="dashboard-section">
        <h2>Today's Learning</h2>
        {loading ? (
          <div className="today-learning-grid">
            <Skeleton height={150} />
            <Skeleton height={150} />
          </div>
        ) : daily.new_questions.length === 0 && daily.revision_questions.length === 0 ? (
          <EmptyState
            icon="🎉"
            title="You're done for today!"
            subtitle="Come back tomorrow for fresh learning."
          />
        ) : (
          <div className="today-learning-grid">
            <div className="today-card today-card-new">
              <span className="today-card-icon">🆕</span>
              <h3>New Learning</h3>
              {daily.new_questions.length > 0 ? (
                <>
                  <p className="today-card-count">
                    {daily.new_questions.length} question{daily.new_questions.length === 1 ? '' : 's'}
                  </p>
                  <button type="button" className="today-card-cta" onClick={() => navigate('/dashboard/learn')}>
                    Start Learning →
                  </button>
                </>
              ) : (
                <p className="today-card-empty">🎉 You're all caught up! No new questions available right now.</p>
              )}
            </div>
            <div className="today-card today-card-revision">
              <span className="today-card-icon">🔄</span>
              <h3>Today's Revision</h3>
              {daily.revision_questions.length > 0 ? (
                <>
                  <p className="today-card-count">
                    {daily.revision_questions.length} question{daily.revision_questions.length === 1 ? '' : 's'}
                  </p>
                  <button type="button" className="today-card-cta" onClick={() => navigate('/dashboard/revision')}>
                    Start Revision →
                  </button>
                </>
              ) : (
                <p className="today-card-empty">✨ No revisions due today. You're all caught up!</p>
              )}
            </div>
          </div>
        )}
      </section>

      <section className="dashboard-section">
        <h2>Topics</h2>
        {loading ? (
          <Skeleton height={32} />
        ) : !dashboard || dashboard.topics_in_progress.length === 0 ? (
          <EmptyState title="No topics yet" subtitle="Learn a few questions to see your topics here." />
        ) : (
          <div className="topic-chip-row">
            {dashboard.topics_in_progress.slice(0, 8).map((t) => (
              <span key={t.topic_id} className="topic-chip">
                {t.topic_name} <em>({t.learned_count})</em>
              </span>
            ))}
          </div>
        )}
      </section>

      <section className="dashboard-section">
        <h2>Recent Activity</h2>
        {loading ? (
          <Skeleton height={80} />
        ) : !dashboard || dashboard.recent_activity.length === 0 ? (
          <EmptyState title="No activity yet" subtitle="Mark a question as learned to get started." />
        ) : (
          <ul className="activity-list">
            {dashboard.recent_activity.map((item) => (
              <li key={item.question_id}>
                <span className="activity-text">{item.question_text}</span>
                <span className="activity-meta">reviewed {item.review_count}x</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="dashboard-section dashboard-ai-cta">
        <h2>AI Assistant</h2>
        <p className="dashboard-ai-cta-subtitle">Have a doubt? Ask the AI tutor anything.</p>
        <button type="button" className="dashboard-ask-ai-button" onClick={() => navigate('/ai')}>
          Ask AI 🤖
        </button>
      </section>
    </div>
  )
}

export default DashboardPage
