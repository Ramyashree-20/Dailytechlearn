import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { deleteSession, getSession, sendChatMessage } from '../api/chat'
import { fetchQuestion } from '../api/learning'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import type { ChatMessageDTO, ChatSessionDetailDTO, Question } from '../types'
import './AiChatPage.css'

const QUESTION_PROMPTS = [
  'Explain this in very simple terms.',
  'Give me a real-world example.',
  "Explain like I'm a complete beginner.",
  'Why does this matter in practice?',
]
const GENERAL_PROMPTS = [
  "What's the difference between REST and GraphQL?",
  'Explain Docker vs. a virtual machine.',
  'What does "idempotent" mean?',
]

function AiChatPage() {
  const { id } = useParams<{ id: string }>()
  const sessionId = Number(id)
  const location = useLocation()
  const navigate = useNavigate()
  const { authFetch } = useAuth()
  const { showToast } = useToast()

  const [session, setSession] = useState<ChatSessionDetailDTO | null>(null)
  const [question, setQuestion] = useState<Question | null>(null)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [input, setInput] = useState('')
  const [loadingSession, setLoadingSession] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    setLoadingSession(true)
    setSession(null)
    setQuestion(null)
    setSuggestions([])
    setError(null)

    getSession(authFetch, sessionId)
      .then((detail) => {
        setSession(detail)
        if (detail.question_id) {
          return fetchQuestion(authFetch, detail.question_id).then(setQuestion)
        }
      })
      .catch(() => setError('This conversation could not be found.'))
      .finally(() => setLoadingSession(false))

    const prefill = (location.state as { prefill?: string } | null)?.prefill
    if (prefill) {
      setInput(prefill)
      navigate(location.pathname, { replace: true, state: null })
    }

    const focusTimer = setTimeout(() => textareaRef.current?.focus(), 150)
    return () => clearTimeout(focusTimer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [session?.messages, sending])

  const sendMessage = (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || sending || !session) return

    const optimisticMessage: ChatMessageDTO = {
      id: -Date.now(),
      role: 'user',
      content: trimmed,
      created_at: new Date().toISOString(),
    }
    setSession((prev) => (prev ? { ...prev, messages: [...prev.messages, optimisticMessage] } : prev))
    setInput('')
    setError(null)
    setSuggestions([])
    setSending(true)

    sendChatMessage(authFetch, session.id, trimmed)
      .then((data) => {
        setSession((prev) => (prev ? { ...prev, messages: [...prev.messages, data.message] } : prev))
        setSuggestions(data.follow_up_suggestions ?? [])
      })
      .catch((err: Error) => {
        setSession((prev) =>
          prev ? { ...prev, messages: prev.messages.filter((m) => m.id !== optimisticMessage.id) } : prev,
        )
        setError(err.message)
        setInput(trimmed)
      })
      .finally(() => setSending(false))
  }

  const handleDelete = () => {
    if (!session) return
    deleteSession(authFetch, session.id)
      .then(() => {
        showToast('Conversation deleted', 'success')
        navigate('/ai')
      })
      .catch(() => showToast('Could not delete that conversation', 'error'))
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  if (loadingSession) {
    return <div className="ai-chat-loading">Loading conversation...</div>
  }

  if (!session) {
    return (
      <div className="ai-chat-error">
        <p>⚠️ {error ?? 'This conversation could not be found.'}</p>
        <button type="button" onClick={() => navigate('/ai')}>
          Back to conversations
        </button>
      </div>
    )
  }

  const examplePrompts = question ? QUESTION_PROMPTS : GENERAL_PROMPTS
  const isEmpty = session.messages.length === 0

  return (
    <div className="ai-chat-page">
      <header className="ai-chat-header">
        <button type="button" className="ai-chat-back" onClick={() => navigate('/ai')} aria-label="Back to conversations">
          ← Back
        </button>
        <div className="ai-chat-header-text">
          <span className="ai-chat-title">{session.title}</span>
          {question && (
            <span className="ai-chat-context-chip" title={question.question_text}>
              About: {question.question_text}
            </span>
          )}
        </div>
        <button type="button" className="ai-chat-delete" onClick={handleDelete} aria-label="Delete conversation">
          🗑
        </button>
      </header>

      <div className="ai-chat-messages">
        {isEmpty && (
          <div className="ai-chat-empty">
            <p className="ai-chat-empty-title">
              {question ? 'Ask anything about this question.' : 'Ask me anything about tech concepts.'}
            </p>
            <div className="ai-chat-prompt-grid">
              {examplePrompts.map((prompt) => (
                <button key={prompt} type="button" className="ai-chat-prompt-chip" onClick={() => sendMessage(prompt)}>
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {session.messages.map((message) => (
          <div key={message.id} className={`ai-chat-bubble-row ${message.role}`}>
            <div className={`ai-chat-bubble ${message.role}`}>{message.content}</div>
          </div>
        ))}

        {sending && (
          <div className="ai-chat-bubble-row assistant">
            <div className="ai-chat-bubble assistant ai-chat-typing" aria-label="AI is typing">
              <span className="ai-chat-typing-dot" />
              <span className="ai-chat-typing-dot" />
              <span className="ai-chat-typing-dot" />
            </div>
          </div>
        )}

        {error && (
          <div className="ai-chat-error-banner" role="alert">
            <span>⚠️ {error}</span>
            <button type="button" onClick={() => sendMessage(input)}>
              Retry
            </button>
          </div>
        )}

        {!sending && suggestions.length > 0 && (
          <div className="ai-chat-suggestions">
            {suggestions.map((s) => (
              <button key={s} type="button" className="ai-chat-suggestion-chip" onClick={() => sendMessage(s)}>
                {s}
              </button>
            ))}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="ai-chat-input-row">
        <textarea
          ref={textareaRef}
          className="ai-chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={question ? 'Ask about this question...' : 'Ask a learning question...'}
          rows={1}
          maxLength={2000}
          disabled={sending}
          aria-label="Message the AI Learning Assistant"
        />
        <button
          type="button"
          className="ai-chat-send"
          onClick={() => sendMessage(input)}
          disabled={sending || !input.trim()}
          aria-label="Send message"
        >
          {sending ? '...' : 'Send'}
        </button>
      </div>
    </div>
  )
}

export default AiChatPage
