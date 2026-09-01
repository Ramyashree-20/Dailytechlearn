import type { DailyLearning, DashboardData, LearningProgressResult, Question } from '../types'

type AuthFetch = (path: string, options?: RequestInit) => Promise<Response>

async function parseJsonOrThrow(response: Response) {
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`)
  return body
}

export function fetchToday(authFetch: AuthFetch): Promise<DailyLearning> {
  return authFetch('/api/learning/today').then(parseJsonOrThrow)
}

export function fetchDashboard(authFetch: AuthFetch): Promise<DashboardData> {
  return authFetch('/api/learning/dashboard').then(parseJsonOrThrow)
}

export function markLearned(
  authFetch: AuthFetch,
  questionId: number,
  result: 'easy' | 'hard' = 'easy',
): Promise<LearningProgressResult> {
  return authFetch('/api/learning/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_id: questionId, result }),
  }).then(parseJsonOrThrow)
}

export function fetchTopics(): Promise<
  { id: number; name: string; description: string | null; category_id: number | null; importance: number; active: boolean }[]
> {
  return fetch(`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}/api/topics`).then((r) => r.json())
}

export function fetchQuestion(authFetch: AuthFetch, questionId: number): Promise<Question> {
  return authFetch(`/api/questions/${questionId}`).then(parseJsonOrThrow)
}
