import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { resolveSessionForQuestion } from '../api/chat'
import { fetchToday, markLearned } from '../api/learning'
import { EmptyState, ErrorState, Skeleton } from '../components/Feedback'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import type { Question } from '../types'
import './RevisionPage.css'

const ADVANCE_DELAY_MS = 1400

function formatNextReview(isoString: string): string {
  const target = new Date(isoString)
  const diffDays = Math.round((target.getTime() - Date.now()) / (1000 * 60 * 60 * 24))
  if (diffDays <= 0) return 'later today'
  if (diffDays === 1) return 'tomorrow'
  if (diffDays < 14) return `in ${diffDays} days`
  return `on ${target.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}`
}

type Feedback = { result: 'easy' | 'hard'; nextReviewAt: string }

function RevisionPage() {
  const { authFetch } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const [questions, setQuestions] = useState<Question[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [revealed, setRevealed] = useState(false)
  const [feedback, setFeedback] = useState<Feedback | null>(null)
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [completedCount, setCompletedCount] = useState(0)

  const load = useCallback(() => {
    setError(null)
    fetchToday(authFetch)
      .then((daily) => {
        setQuestions(daily.revision_questions)
        setCurrentIndex(0)
        setCompletedCount(0)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [authFetch])

  useEffect(() => {
    load()
  }, [load])

  // Auto-advance to the next card a moment after showing the result, so
  // the learner sees the "Next review: ..." confirmation before moving on.
  useEffect(() => {
    if (!feedback) return
    const timer = setTimeout(() => {
      setFeedback(null)
      setRevealed(false)
      setCurrentIndex((i) => i + 1)
    }, ADVANCE_DELAY_MS)
    return () => clearTimeout(timer)
  }, [feedback])

  const currentQuestion = questions[currentIndex]

  const handleResult = (result: 'easy' | 'hard') => {
    if (!currentQuestion || busy) return
    setBusy(true)
    markLearned(authFetch, currentQuestion.id, result)
      .then((progress) => {
        setFeedback({ result, nextReviewAt: progress.next_review_at })
        setCompletedCount((c) => c + 1)
      })
      .catch(() => showToast('Could not save that — try again', 'error'))
      .finally(() => setBusy(false))
  }

  const handleAskAi = () => {
    if (!currentQuestion) return
    resolveSessionForQuestion(authFetch, currentQuestion.id)
      .then((sessionId) => navigate(`/ai/chat/${sessionId}`))
      .catch(() => showToast('Could not open the AI assistant', 'error'))
  }

  if (loading) {
    return (
      <div className="revision-page">
        <h1>Today's Revision</h1>
        <Skeleton height={220} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="revision-page">
        <h1>Today's Revision</h1>
        <ErrorState message={error} onRetry={load} />
      </div>
    )
  }

  const isDone = currentIndex >= questions.length

  return (
    <div className="revision-page">
      <div className="revision-header">
        <h1>Today's Revision</h1>
        {questions.length > 0 && !isDone && (
          <span className="revision-progress">
            {currentIndex + 1} of {questions.length}
          </span>
        )}
      </div>
      {questions.length > 0 && !isDone && (
        <p className="revision-subtitle">Rate yourself honestly — it shapes when you'll see this question again.</p>
      )}

      {questions.length === 0 ? (
        <EmptyState icon="✨" title="No revisions due today." subtitle="You're all caught up!" />
      ) : isDone ? (
        <EmptyState
          icon="🎉"
          title="Today's revision complete!"
          subtitle={`You reviewed ${completedCount} question${completedCount === 1 ? '' : 's'}. Nice work.`}
        />
      ) : (
        <div className="revision-card-stage">
          <div key={currentQuestion.id} className="revision-card">
            <span className={`dq-difficulty dq-difficulty-${currentQuestion.difficulty}`}>{currentQuestion.difficulty}</span>
            <p className="revision-question">{currentQuestion.question_text}</p>

            {feedback ? (
              <div className={`revision-feedback revision-feedback-${feedback.result}`}>
                <span className="revision-feedback-icon">{feedback.result === 'easy' ? '✅' : '💪'}</span>
                <p className="revision-feedback-text">{feedback.result === 'easy' ? 'Nice!' : "No worries — you'll see this again soon"}</p>
                <p className="revision-feedback-next">Next review: {formatNextReview(feedback.nextReviewAt)}</p>
              </div>
            ) : revealed ? (
              <>
                <div className="revision-answer">{currentQuestion.answer}</div>
                <div className="revision-actions">
                  <button type="button" className="revision-hard" onClick={() => handleResult('hard')} disabled={busy}>
                    😅 Hard
                  </button>
                  <button type="button" className="revision-easy" onClick={() => handleResult('easy')} disabled={busy}>
                    😄 Easy
                  </button>
                </div>
                <button type="button" className="revision-ask-ai" onClick={handleAskAi}>
                  Ask AI 🤖
                </button>
              </>
            ) : (
              <button type="button" className="revision-reveal" onClick={() => setRevealed(true)}>
                Show Answer
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default RevisionPage
