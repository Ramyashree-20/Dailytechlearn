import { NavLink } from 'react-router-dom'
import './BottomNav.css'

const ITEMS = [
  { to: '/dashboard', icon: '🏠', label: 'Home', end: true },
  { to: '/dashboard/learn', icon: '📚', label: 'Learn', end: false },
  { to: '/dashboard/revision', icon: '🔄', label: 'Revise', end: false },
  { to: '/ai', icon: '🤖', label: 'AI', end: false },
  { to: '/dashboard/progress', icon: '📈', label: 'Progress', end: false },
]

function BottomNav() {
  return (
    <nav className="bottom-nav">
      {ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) => `bottom-nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="bottom-nav-icon">{item.icon}</span>
          <span className="bottom-nav-label">{item.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}

export default BottomNav
