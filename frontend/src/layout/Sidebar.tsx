import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Sidebar.css'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: '🏠', end: true },
  { to: '/dashboard/learn', label: 'Learn', icon: '📚', end: false },
  { to: '/dashboard/revision', label: 'Revision', icon: '🔄', end: false },
  { to: '/dashboard/progress', label: 'Progress', icon: '📈', end: false },
  { to: '/ai', label: 'AI Assistant', icon: '🤖', end: false },
]

const ADMIN_NAV_ITEMS = [
  { to: '/admin', label: 'Admin Overview', icon: '🛠️', end: true },
  { to: '/admin/content', label: 'Content Pipeline', icon: '📥', end: false },
  { to: '/admin/candidates', label: 'Candidates', icon: '🎯', end: false },
  { to: '/admin/drafts', label: 'AI Drafts', icon: '📝', end: false },
  { to: '/admin/taxonomy', label: 'Taxonomy', icon: '🗂️', end: false },
]

type SidebarProps = {
  mobileOpen: boolean
  onCloseMobile: () => void
}

function Sidebar({ mobileOpen, onCloseMobile }: SidebarProps) {
  const { currentUser } = useAuth()

  return (
    <>
      {mobileOpen && <div className="sidebar-backdrop" onClick={onCloseMobile} />}
      <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-brand">📘 DailyTechLearn</div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
              onClick={onCloseMobile}
            >
              <span className="sidebar-icon">{item.icon}</span> {item.label}
            </NavLink>
          ))}
        </nav>

        {currentUser?.is_admin && (
          <>
            <div className="sidebar-section-label">Admin</div>
            <nav className="sidebar-nav">
              {ADMIN_NAV_ITEMS.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                  onClick={onCloseMobile}
                >
                  <span className="sidebar-icon">{item.icon}</span> {item.label}
                </NavLink>
              ))}
            </nav>
          </>
        )}
      </aside>
    </>
  )
}

export default Sidebar
