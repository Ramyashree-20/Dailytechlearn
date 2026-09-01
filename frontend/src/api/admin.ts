import type { AIDraft, Candidate, Category, PipelineStatus, SourceArticle, Topic } from '../types'

type AuthFetch = (path: string, options?: RequestInit) => Promise<Response>

async function parseJsonOrThrow(response: Response) {
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`)
  return body
}

export function fetchPipelineStatus(authFetch: AuthFetch): Promise<PipelineStatus> {
  return authFetch('/api/content/pipeline-status').then(parseJsonOrThrow)
}

export function replenishContent(authFetch: AuthFetch) {
  return authFetch('/api/content/replenish', { method: 'POST' }).then(parseJsonOrThrow)
}

export function fetchSourceArticles(authFetch: AuthFetch, limit = 20): Promise<SourceArticle[]> {
  return authFetch(`/api/content/articles?limit=${limit}`).then(parseJsonOrThrow)
}

export function fetchCandidates(authFetch: AuthFetch, limit = 10): Promise<Candidate[]> {
  return authFetch(`/api/content/candidates?limit=${limit}`).then(parseJsonOrThrow)
}

export function generateDraftsBatch(authFetch: AuthFetch, limit = 5) {
  return authFetch(`/api/learning/generate-drafts?limit=${limit}`, { method: 'POST' }).then(parseJsonOrThrow)
}

export function fetchDrafts(authFetch: AuthFetch, status?: string): Promise<AIDraft[]> {
  const query = status ? `?status=${status}` : ''
  return authFetch(`/api/ai/drafts${query}`).then(parseJsonOrThrow)
}

export function approveDraft(authFetch: AuthFetch, draftId: number, topicId: number) {
  return authFetch(`/api/ai/drafts/${draftId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic_id: topicId }),
  }).then(parseJsonOrThrow)
}

export function rejectDraft(authFetch: AuthFetch, draftId: number) {
  return authFetch(`/api/ai/drafts/${draftId}/reject`, { method: 'POST' }).then(parseJsonOrThrow)
}

export function fetchCategories(): Promise<Category[]> {
  return fetch(`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}/api/categories`).then((r) => r.json())
}

export function fetchAllTopics(): Promise<Topic[]> {
  return fetch(`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}/api/topics`).then((r) => r.json())
}
