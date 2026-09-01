import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import './AuthPages.css'

function LoginPage() {
  const { login, currentUser, authChecked } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (authChecked && currentUser) navigate('/dashboard', { replace: true })
  }, [authChecked, currentUser, navigate])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    login(identifier, password)
      .then(() => {
        showToast('Welcome back 👋', 'success')
        navigate('/dashboard')
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <Link to="/" className="auth-brand">
          📘 DailyTechLearn
        </Link>
        <h1>Log In</h1>
        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Email or Username
            <input
              type="text"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              autoComplete="username"
              required
              autoFocus
            />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </label>
          {error && <p className="auth-error">{error}</p>}
          <button type="submit" className="auth-submit" disabled={loading}>
            {loading ? 'Logging in...' : 'Log In'}
          </button>
        </form>
        <p className="auth-switch">
          Don't have an account? <Link to="/register">Register</Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage
