import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './LandingPage.css'

function LandingPage() {
  const { currentUser, authChecked } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (authChecked && currentUser) navigate('/dashboard', { replace: true })
  }, [authChecked, currentUser, navigate])

  return (
    <div className="landing-page">
      <div className="landing-hero">
        <div className="landing-badge">📘 DailyTechLearn</div>
        <h1>Learn AI &amp; software engineering, 10 minutes a day.</h1>
        <p className="landing-subtitle">
          5 new questions and 5 revisions a day, with simple explanations, real-world examples, and an AI
          tutor for whenever you're stuck.
        </p>
        <div className="landing-cta-row">
          <Link to="/register" className="landing-cta-primary">
            Get Started Free
          </Link>
          <Link to="/login" className="landing-cta-secondary">
            Log In
          </Link>
        </div>
      </div>

      <div className="landing-features">
        <div className="landing-feature-card">
          <span className="landing-feature-icon">📚</span>
          <h3>Daily Learning</h3>
          <p>New questions ranked by real-world importance, with simple explanations and examples.</p>
        </div>
        <div className="landing-feature-card">
          <span className="landing-feature-icon">🔄</span>
          <h3>Spaced Revision</h3>
          <p>A proven spaced-repetition schedule brings questions back exactly when you're about to forget them.</p>
        </div>
        <div className="landing-feature-card">
          <span className="landing-feature-icon">🤖</span>
          <h3>AI Tutor</h3>
          <p>Ask follow-up questions about anything you're studying and get a clear, grounded answer.</p>
        </div>
        <div className="landing-feature-card">
          <span className="landing-feature-icon">📈</span>
          <h3>Track Progress</h3>
          <p>See your learning streak, topic-by-topic progress, and what you've mastered.</p>
        </div>
      </div>
    </div>
  )
}

export default LandingPage
