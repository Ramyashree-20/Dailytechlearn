import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import Layout from './layout/Layout'
import { AdminRoute, ProtectedRoute } from './layout/RouteGuards'
import AdminCandidatesPage from './pages/AdminCandidatesPage'
import AdminContentPage from './pages/AdminContentPage'
import AdminDraftsPage from './pages/AdminDraftsPage'
import AdminOverviewPage from './pages/AdminOverviewPage'
import AdminTaxonomyPage from './pages/AdminTaxonomyPage'
import AiChatPage from './pages/AiChatPage'
import AiListPage from './pages/AiListPage'
import DashboardPage from './pages/DashboardPage'
import LandingPage from './pages/LandingPage'
import LearnPage from './pages/LearnPage'
import LoginPage from './pages/LoginPage'
import ProgressPage from './pages/ProgressPage'
import RegisterPage from './pages/RegisterPage'
import RevisionPage from './pages/RevisionPage'

function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/dashboard/learn" element={<LearnPage />} />
              <Route path="/dashboard/revision" element={<RevisionPage />} />
              <Route path="/dashboard/progress" element={<ProgressPage />} />
              <Route path="/ai" element={<AiListPage />} />
              <Route path="/ai/chat/:id" element={<AiChatPage />} />

              <Route element={<AdminRoute />}>
                <Route path="/admin" element={<AdminOverviewPage />} />
                <Route path="/admin/content" element={<AdminContentPage />} />
                <Route path="/admin/candidates" element={<AdminCandidatesPage />} />
                <Route path="/admin/drafts" element={<AdminDraftsPage />} />
                <Route path="/admin/taxonomy" element={<AdminTaxonomyPage />} />
              </Route>
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ToastProvider>
    </AuthProvider>
  )
}

export default App
