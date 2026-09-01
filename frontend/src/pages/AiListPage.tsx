import { useCallback, useEffect, useState, type MouseEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { createSession, deleteSession, listSessions } from '../api/chat'
import { EmptyState, ErrorState, Skeleton } from '../components/Feedback'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import type { ChatSessionSummaryDTO } from '../types'
import './AiListPage.css'

const GENERAL_PROMPTS = [
  "What's the difference between REST and GraphQL?",
  'Explain Docker vs. a virtual machine.',
  'What does "idempotent" mean?',
  'How does OAuth actually work?',
]

function formatRelativeTime(isoString: string): string {
  const diffMs = Date.now() - new Date(isoString).getTime()
  const minutes = Math.round(diffMs / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  return `${days}d ago`
}

function AiListPage() {
  const { authFetch } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const [sessions, setSessions] = useState<ChatSessionSummaryDTO[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    setError(null)
    listSessions(authFetch)
      .then(setSessions)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [authFetch])

  useEffect(() => {
    load()
  }, [load])

  const startNewChat = (prefill?: string) => {
    createSession(authFetch, null)
      .then((session) => navigate(`/ai/chat/${session.id}`, { state: prefill ? { prefill } : undefined }))
      .catch(() => showToast('Could not start a new conversation', 'error'))
  }

  const handleDelete = (sessionId: number, e: MouseEvent) => {
    e.stopPropagation()
    deleteSession(authFetch, sessionId)
      .then(() => setSessions((prev) => prev.filter((s) => s.id !== sessionId)))
      .catch(() => showToast('Could not delete that conversation', 'error'))
  }

  return (
    <div className="ai-list-page">
      <div className="ai-list-header">
        <div>
          <h1>AI Assistant</h1>
          <p className="ai-list-subtitle">Ask a doubt, get a clear explanation, and pick up where you left off.</p>
        </div>
        <button type="button" className="ai-new-chat-button" onClick={() => startNewChat()}>
          + New Chat
        </button>
      </div>

      {error && <ErrorState message={error} onRetry={load} />}

      {loading ? (
        <div className="ai-session-grid">
          <Skeleton height={70} />
          <Skeleton height={70} />
          <Skeleton height={70} />
        </div>
      ) : sessions.length === 0 ? (
        <div className="ai-empty-wrap">
          <EmptyState icon="🤖" title="No conversations yet" subtitle="Start one, or try an example:" />
          <div className="ai-prompt-grid">
            {GENERAL_PROMPTS.map((prompt) => (
              <button key={prompt} type="button" className="ai-prompt-chip" onClick={() => startNewChat(prompt)}>
                {prompt}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="ai-session-grid">
          {sessions.map((s) => (
            <button key={s.id} type="button" className="ai-session-card" onClick={() => navigate(`/ai/chat/${s.id}`)}>
              <div className="ai-session-card-text">
                <span className="ai-session-title">{s.title}</span>
                <span className="ai-session-time">{formatRelativeTime(s.updated_at)}</span>
              </div>
              <span
                role="button"
                tabIndex={0}
                className="ai-session-delete"
                onClick={(e) => handleDelete(s.id, e)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleDelete(s.id, e as unknown as MouseEvent)
                }}
                aria-label={`Delete conversation: ${s.title}`}
              >
                🗑
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default AiListPage
