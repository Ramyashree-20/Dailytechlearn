import type { ChatMessageDTO, ChatSessionDetailDTO, ChatSessionSummaryDTO } from '../types'

type AuthFetch = (path: string, options?: RequestInit) => Promise<Response>

type SendMessageResponse = {
  message: ChatMessageDTO
  follow_up_suggestions: string[]
}

async function parseJsonOrThrow(response: Response) {
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`)
  return body
}

export function listSessions(authFetch: AuthFetch): Promise<ChatSessionSummaryDTO[]> {
  return authFetch('/api/learning/chat/sessions').then(parseJsonOrThrow)
}

export function getSession(authFetch: AuthFetch, sessionId: number): Promise<ChatSessionDetailDTO> {
  return authFetch(`/api/learning/chat/sessions/${sessionId}`).then(parseJsonOrThrow)
}

export function createSession(authFetch: AuthFetch, questionId: number | null): Promise<ChatSessionDetailDTO> {
  return authFetch('/api/learning/chat/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_id: questionId }),
  }).then(parseJsonOrThrow)
}

export function deleteSession(authFetch: AuthFetch, sessionId: number): Promise<void> {
  return authFetch(`/api/learning/chat/sessions/${sessionId}`, { method: 'DELETE' }).then((r) => {
    if (!r.ok) throw new Error(`Request failed (${r.status})`)
  })
}

export function sendChatMessage(authFetch: AuthFetch, sessionId: number, message: string): Promise<SendMessageResponse> {
  return authFetch(`/api/learning/chat/sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  }).then(parseJsonOrThrow)
}

/** Find-or-create: resumes an existing conversation about this question if
 * one exists, otherwise starts a new one — so the learner never has to
 * manually hunt for a prior chat about the same question. */
export async function resolveSessionForQuestion(authFetch: AuthFetch, questionId: number): Promise<number> {
  const sessions = await listSessions(authFetch)
  const existing = sessions.find((s) => s.question_id === questionId)
  if (existing) return existing.id
  const created = await createSession(authFetch, questionId)
  return created.id
}
