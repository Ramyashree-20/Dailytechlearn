import { useAuth } from '../context/AuthContext'
import './TopBar.css'

function TopBar({ onMenuClick }: { onMenuClick: () => void }) {
  const { currentUser, logout } = useAuth()

  return (
    <header className="topbar">
      <button type="button" className="topbar-menu-button" onClick={onMenuClick} aria-label="Open menu">
        ☰
      </button>
      <div className="topbar-spacer" />
      {currentUser && (
        <div className="topbar-user">
          <span className="topbar-email">{currentUser.username ?? currentUser.email}</span>
          {currentUser.is_admin && <span className="topbar-admin-badge">Admin</span>}
          <button type="button" className="topbar-logout" onClick={logout}>
            Log Out
          </button>
        </div>
      )}
    </header>
  )
}

export default TopBar
