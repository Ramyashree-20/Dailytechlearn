import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'

export type CurrentUser = {
  id: number
  email: string
  username: string | null
  is_admin: boolean
  created_at: string
}

type AuthContextValue = {
  token: string | null
  currentUser: CurrentUser | null
  authChecked: boolean
  // identifier: the account's email OR username — the backend resolves
  // whichever it is (see auth_service.authenticate_user).
  login: (identifier: string, password: string) => Promise<void>
  register: (email: string, password: string, username?: string) => Promise<void>
  logout: () => void
  authFetch: (path: string, options?: RequestInit) => Promise<Response>
}

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

// Storing the JWT in localStorage (rather than an httpOnly cookie) is the
// simplest option and fine for this project, but it's a real security
// tradeoff worth naming: any JavaScript running on this page (including an
// injected XSS payload) can read localStorage and steal the token. An
// httpOnly cookie can't be read by JavaScript at all, so it's the safer
// choice for a real production app. We're accepting that tradeoff here in
// exchange for a much simpler implementation — see docs/architecture.md.
const TOKEN_STORAGE_KEY = 'dailytechlearn_token'

const AuthContext = createContext<AuthContextValue | null>(null)

async function parseJsonOrThrow(response: Response) {
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`)
  return body
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY))
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null)
  const [authChecked, setAuthChecked] = useState(false)

  // Every protected request goes through this instead of plain fetch, so
  // the "Authorization: Bearer <token>" header is never forgotten on a
  // route that needs it. The backend never trusts anything else in the
  // request to say who's calling — only this header's JWT.
  const authFetch = useCallback(
    (path: string, options: RequestInit = {}) => {
      const headers = new Headers(options.headers)
      if (token) headers.set('Authorization', `Bearer ${token}`)
      return fetch(`${API_BASE_URL}${path}`, { ...options, headers })
    },
    [token],
  )

  // On load (and whenever the token changes), ask the backend who this
  // token belongs to. If it's missing, expired, or invalid, /api/auth/me
  // returns 401 and we drop back to logged-out state.
  useEffect(() => {
    if (!token) {
      setCurrentUser(null)
      setAuthChecked(true)
      return
    }
    authFetch('/api/auth/me')
      .then((response) => {
        if (!response.ok) throw new Error('Session expired')
        return response.json()
      })
      .then(setCurrentUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_STORAGE_KEY)
        setToken(null)
        setCurrentUser(null)
      })
      .finally(() => setAuthChecked(true))
  }, [token, authFetch])

  const login = useCallback(async (identifier: string, password: string) => {
    const data = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier, password }),
    }).then(parseJsonOrThrow)
    localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token)
    setToken(data.access_token)
  }, [])

  const register = useCallback(
    async (email: string, password: string, username?: string) => {
      await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, username: username || null }),
      }).then(parseJsonOrThrow)
      await login(email, password) // registration doesn't log you in by itself
    },
    [login],
  )

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    setToken(null)
    setCurrentUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ token, currentUser, authChecked, login, register, logout, authFetch }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
