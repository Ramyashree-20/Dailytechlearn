import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { resolveSessionForQuestion } from '../api/chat'
import { fetchToday, fetchTopics, markLearned } from '../api/learning'
import { EmptyState, ErrorState, Skeleton } from '../components/Feedback'
import QuestionCard from '../components/QuestionCard'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import type { Question } from '../types'
import './LearnPage.css'

function LearnPage() {
  const { authFetch } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const [questions, setQuestions] = useState<Question[]>([])
  const [topicNames, setTopicNames] = useState<Record<number, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [completingId, setCompletingId] = useState<number | null>(null)
  // Captured once per load — lets the empty state tell "there was never
  // anything today" apart from "you just finished everything today."
  const [initialCount, setInitialCount] = useState(0)

  const load = useCallback(() => {
    setError(null)
    Promise.all([fetchToday(authFetch), fetchTopics()])
      .then(([daily, topics]) => {
        setQuestions(daily.new_questions)
        setInitialCount(daily.new_questions.length)
        setTopicNames(Object.fromEntries(topics.map((t) => [t.id, t.name])))
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [authFetch])

  useEffect(() => {
    load()
  }, [load])

  const handleMarkLearned = (questionId: number) => {
    setCompletingId(questionId)
    markLearned(authFetch, questionId)
      .then(() => {
        showToast('Marked as learned 🎉', 'success')
        setQuestions((prev) => prev.filter((q) => q.id !== questionId))
      })
      .catch(() => showToast('Could not save that — try again', 'error'))
      .finally(() => setCompletingId(null))
  }

  const handleAskAi = (questionId: number) => {
    resolveSessionForQuestion(authFetch, questionId)
      .then((sessionId) => navigate(`/ai/chat/${sessionId}`))
      .catch(() => showToast('Could not open the AI assistant', 'error'))
  }

  const completedCount = initialCount - questions.length

  return (
    <div className="learn-page">
      <div className="learn-header">
        <div>
          <h1>Today's New Learning</h1>
          {initialCount > 0 && (
            <p className="learn-subtitle">
              {initialCount} question{initialCount === 1 ? '' : 's'} available today, ranked by topic importance.
            </p>
          )}
        </div>
        {initialCount > 0 && (
          <span className="learn-progress">
            {completedCount}/{initialCount}
          </span>
        )}
      </div>

      {error && <ErrorState message={error} onRetry={load} />}

      {loading ? (
        <div className="learn-grid">
          <Skeleton height={220} />
          <Skeleton height={220} />
          <Skeleton height={220} />
        </div>
      ) : initialCount === 0 ? (
        <EmptyState
          icon="🎉"
          title="You're all caught up!"
          subtitle="There are no new questions available right now."
        />
      ) : questions.length === 0 ? (
        <EmptyState icon="🎉" title="Today's new learning complete!" subtitle="Nice work — check Revision or come back tomorrow." />
      ) : (
        <div className="learn-grid">
          {questions.map((q) => (
            <QuestionCard
              key={q.id}
              question={q}
              topicName={topicNames[q.topic_id]}
              variant="detailed"
              onAskAi={() => handleAskAi(q.id)}
              onMarkLearned={() => handleMarkLearned(q.id)}
              busy={completingId === q.id}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default LearnPage
