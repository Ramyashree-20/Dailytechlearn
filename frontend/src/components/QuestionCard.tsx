import type { Question } from '../types'
import './QuestionCard.css'

type QuestionCardProps = {
  question: Question
  topicName?: string
  variant?: 'compact' | 'detailed'
  onAskAi: () => void
  onMarkLearned: () => void
  busy?: boolean
}

function DifficultyBadge({ difficulty }: { difficulty: string }) {
  return <span className={`dq-difficulty dq-difficulty-${difficulty}`}>{difficulty}</span>
}

function QuestionCard({ question, topicName, variant = 'compact', onAskAi, onMarkLearned, busy = false }: QuestionCardProps) {
  if (variant === 'compact') {
    return (
      <div className="dq-card">
        <div className="dq-card-body">
          <DifficultyBadge difficulty={question.difficulty} />
          <p className="dq-text">{question.question_text}</p>
        </div>
        <div className="dq-card-actions">
          <button type="button" className="dq-ask-ai" onClick={onAskAi}>
            Ask AI 🤖
          </button>
          <button type="button" className="dq-learned" onClick={onMarkLearned} disabled={busy}>
            {busy ? '...' : 'Learned'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="dq-card dq-card-detailed">
      <div className="dq-card-body">
        <div className="dq-detailed-header">
          {topicName && <span className="dq-topic-name">{topicName}</span>}
          <DifficultyBadge difficulty={question.difficulty} />
        </div>
        <p className="dq-question-heading">{question.question_text}</p>
        <p className="dq-answer">{question.answer}</p>
        {question.simple_explanation && (
          <div className="dq-detail-block">
            <span className="dq-detail-label">Simple explanation</span>
            <p>{question.simple_explanation}</p>
          </div>
        )}
        {question.real_world_example && (
          <div className="dq-detail-block">
            <span className="dq-detail-label">Real-world example</span>
            <p>{question.real_world_example}</p>
          </div>
        )}
        {question.keywords && (
          <div className="dq-keywords">
            {question.keywords.split(',').map((kw) => (
              <span key={kw} className="dq-keyword-chip">
                {kw.trim()}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="dq-card-actions">
        <button type="button" className="dq-ask-ai" onClick={onAskAi}>
          Ask AI 🤖
        </button>
        <button type="button" className="dq-learned" onClick={onMarkLearned} disabled={busy}>
          {busy ? '...' : 'Learned'}
        </button>
      </div>
    </div>
  )
}

export default QuestionCard
