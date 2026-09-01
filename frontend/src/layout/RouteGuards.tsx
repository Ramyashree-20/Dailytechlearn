import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/** Redirects to /login until we've confirmed a valid session. Shared by
 * every authenticated route (learner and admin alike). */
export function ProtectedRoute() {
  const { authChecked, currentUser } = useAuth()

  if (!authChecked) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', color: '#888', fontFamily: 'system-ui, sans-serif' }}>
        Loading...
      </div>
    )
  }
  if (!currentUser) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}

/** Layered under ProtectedRoute — a normal (non-admin) user is redirected
 * to their dashboard rather than seeing a 403-style page. Backend
 * enforcement (get_current_admin_user) is still the real authorization
 * boundary; this only avoids showing UI a normal learner can't use. */
export function AdminRoute() {
  const { currentUser } = useAuth()

  if (!currentUser?.is_admin) {
    return <Navigate to="/dashboard" replace />
  }
  return <Outlet />
}
