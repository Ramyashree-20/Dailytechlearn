import type { ReactNode } from 'react'
import './Feedback.css'

export function Skeleton({ height = 16, width = '100%', className = '' }: { height?: number; width?: string | number; className?: string }) {
  return <div className={`skeleton ${className}`} style={{ height, width }} />
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="error-state" role="alert">
      <span>⚠️ {message}</span>
      {onRetry && (
        <button type="button" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}

export function EmptyState({ icon, title, subtitle, action }: { icon?: string; title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="empty-state">
      {icon && <div className="empty-state-icon">{icon}</div>}
      <p className="empty-state-title">{title}</p>
      {subtitle && <p className="empty-state-subtitle">{subtitle}</p>}
      {action}
    </div>
  )
}
