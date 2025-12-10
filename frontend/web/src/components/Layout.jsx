import { Link, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getProgress } from '../api/missions'
import './Layout.css'

function Layout({ children }) {
  const location = useLocation()
  const { data: progress } = useQuery({
    queryKey: ['progress'],
    queryFn: () => getProgress(),
    retry: false
  })

  const stats = progress || {
    total_score: 0,
    total_missions_completed: 0,
    level_progress: { A: 0, B: 0, C: 0 }
  }

  const totalMissions = stats.total_missions_completed || 0
  const level = totalMissions < 5 ? 'Новичок' : totalMissions < 10 ? 'Специалист' : 'Эксперт'

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <Link to="/" className="logo">
            <h1>🛡️ Тренажёр Astra Linux</h1>
          </Link>
          <div className="header-stats">
            <div className="stat-item">
              <span className="stat-icon">🏆</span>
              <span className="stat-label">Уровень:</span>
              <span className="stat-value">{level}</span>
            </div>
            <div className="stat-item">
              <span className="stat-icon">⭐</span>
              <span className="stat-label">XP:</span>
              <span className="stat-value">{stats.total_score || 0}</span>
            </div>
            <div className="stat-item">
              <span className="stat-icon">🎯</span>
              <span className="stat-label">Миссий:</span>
              <span className="stat-value">{totalMissions}</span>
            </div>
          </div>
        </div>
        <div className="header-status">
          <div className="status-item">
            <span className="status-dot active"></span>
            <span>Контейнер: активен</span>
          </div>
          <div className="status-item">
            <span className="status-dot secure"></span>
            <span>Безопасность: включена</span>
          </div>
        </div>
      </header>
      <div className="layout-body">
        <aside className="sidebar">
          <nav className="sidebar-nav">
            <Link to="/" className={`nav-item ${location.pathname === '/' ? 'active' : ''}`}>
              <span className="nav-icon">📊</span>
              <span>Обзор</span>
            </Link>
            <Link to="/missions" className={`nav-item ${location.pathname.startsWith('/missions') ? 'active' : ''}`}>
              <span className="nav-icon">🎯</span>
              <span>Миссии</span>
            </Link>
            <div className="nav-item">
              <span className="nav-icon">⚙️</span>
              <span>Процессы</span>
            </div>
            <div className="nav-item">
              <span className="nav-icon">📁</span>
              <span>Файловая система</span>
            </div>
            <div className="nav-item">
              <span className="nav-icon">🌐</span>
              <span>Сеть</span>
            </div>
          </nav>
        </aside>
        <main className="main-content">
          {children}
        </main>
      </div>
    </div>
  )
}

export default Layout

