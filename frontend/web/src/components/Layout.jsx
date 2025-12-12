import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getProgress } from '../api/missions'
import { useAuth } from '../contexts/AuthContext'
import './Layout.css'

function Layout({ children }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout, isAuthenticated } = useAuth()
  
  // Не показываем Layout на страницах аутентификации
  const isAuthPage = ['/login', '/register', '/recover-password'].includes(location.pathname)
  
  // Хуки должны вызываться до условных возвратов
  const { data: progress } = useQuery({
    queryKey: ['progress'],
    queryFn: () => getProgress(),
    retry: false,
    enabled: isAuthenticated && !isAuthPage  // Не выполняем запрос на страницах аутентификации
  })
  
  if (isAuthPage) {
    return <>{children}</>
  }
  
  const handleLogout = () => {
    logout()
    navigate('/login')
  }

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
            <h1>🛡️ Linux Training Simulator</h1>
          </Link>
          <div className="header-stats">
            <div className="stat-item">
              <span className="stat-icon">👤</span>
              <span className="stat-label">Пользователь:</span>
              <span className="stat-value">{user?.username || 'Гость'}</span>
            </div>
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
            <button onClick={handleLogout} className="logout-button">
              Выйти
            </button>
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

