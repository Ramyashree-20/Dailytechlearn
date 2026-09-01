import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import BottomNav from './BottomNav'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import './Layout.css'

function Layout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="app-shell">
      <Sidebar mobileOpen={mobileMenuOpen} onCloseMobile={() => setMobileMenuOpen(false)} />
      <div className="app-shell-main">
        <TopBar onMenuClick={() => setMobileMenuOpen(true)} />
        <main className="app-shell-content">
          <Outlet />
        </main>
      </div>
      <BottomNav />
    </div>
  )
}

export default Layout
