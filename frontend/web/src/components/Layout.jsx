import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getProgress, getActiveSandbox } from '../api/missions'
import { getUserInfo } from '../api/admin'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import axios from 'axios'
import { useState } from 'react'
import SandboxInfoDrawer from './SandboxInfoDrawer'
import './Layout.css'

function Layout({ children }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout, isAuthenticated, token } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [drawerView, setDrawerView] = useState(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  
  // Не показываем Layout на страницах аутентификации
  const isAuthPage = ['/login', '/register', '/recover-password'].includes(location.pathname)
  
  // Хуки должны вызываться до условных возвратов
  // Запрос на progress делаем только после полной загрузки пользователя И наличия токена
  const { data: progress, isLoading: progressLoading } = useQuery({
    queryKey: ['progress'],
    queryFn: () => getProgress(),
    retry: false,
    enabled: Boolean(
      isAuthenticated && 
      !isAuthPage && 
      user && 
      user.username && 
      token && 
      axios.defaults.headers.common['Authorization']
    ),  // Не выполняем запрос пока нет токена в axios
    staleTime: 30000  // Кешируем на 30 секунд
  })
  
  // Проверяем наличие активной песочницы
  const { data: activeSandbox } = useQuery({
    queryKey: ['activeSandbox'],
    queryFn: () => getActiveSandbox(),
    enabled: !isAuthPage && isAuthenticated,
    refetchInterval: 5000, // Обновляем каждые 5 секунд
    retry: false
  })
  
  // Проверяем права администратора
  // Делаем запрос сразу при входе для быстрого отображения вкладки
  const { data: userInfo, isLoading: userInfoLoading } = useQuery({
    queryKey: ['userInfo'],
    queryFn: getUserInfo,
    enabled: !isAuthPage && isAuthenticated,
    retry: false,
    staleTime: 60000,  // Кешируем на минуту
    cacheTime: 300000  // Храним в кеше 5 минут
  })
  
  const hasActiveSandbox = activeSandbox?.has_active || false
  // Вкладка «Администрирование» всегда видна для администраторов (и при загрузке, чтобы не мигала)
  const isAdmin = userInfo?.is_admin === true
  const showAdminTab = isAdmin || userInfoLoading
  
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
    level_progress: { A: 0 }
  }

  const totalMissions = stats.total_missions_completed || 0
  const level = totalMissions < 5 ? 'Новичок' : totalMissions < 10 ? 'Специалист' : 'Эксперт'
  
  const handleNavClick = (view) => {
    if (hasActiveSandbox) {
      setDrawerView(view)
      setDrawerOpen(true)
    }
  }
  
  const handleCloseDrawer = () => {
    setDrawerOpen(false)
    setDrawerView(null)
  }

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <Link to="/" className="logo">
            <h1>🛡️ Тренажер Astra Linux</h1>
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
            <button
              type="button"
              onClick={toggleTheme}
              className="theme-toggle"
              title={theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
              aria-label={theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
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
            <Link to="/missions" className={`nav-item ${location.pathname.startsWith('/missions') && !location.pathname.startsWith('/admin') ? 'active' : ''}`}>
              <span className="nav-icon">🎯</span>
              <span>Миссии</span>
            </Link>
            <Link to="/profile" className={`nav-item ${location.pathname === '/profile' ? 'active' : ''}`}>
              <span className="nav-icon">👤</span>
              <span>Профиль</span>
            </Link>
            {showAdminTab && (
              <Link to="/admin" className={`nav-item ${location.pathname.startsWith('/admin') ? 'active' : ''}`}>
                <span className="nav-icon">⚙️</span>
                <span>Администрирование</span>
              </Link>
            )}
            {hasActiveSandbox && (
              <>
                <div 
                  className={`nav-item ${drawerOpen && drawerView === 'processes' ? 'active' : ''}`}
                  onClick={() => handleNavClick('processes')}
                >
                  <span className="nav-icon">⚙️</span>
                  <span>Процессы</span>
                </div>
                <div 
                  className={`nav-item ${drawerOpen && drawerView === 'filesystem' ? 'active' : ''}`}
                  onClick={() => handleNavClick('filesystem')}
                >
                  <span className="nav-icon">📁</span>
                  <span>Файловая система</span>
                </div>
                <div 
                  className={`nav-item ${drawerOpen && drawerView === 'network' ? 'active' : ''}`}
                  onClick={() => handleNavClick('network')}
                >
                  <span className="nav-icon">🌐</span>
                  <span>Сеть</span>
                </div>
              </>
            )}
          </nav>
        </aside>
        <main className="main-content">
          {children}
        </main>
      </div>
      <SandboxInfoDrawer 
        isOpen={drawerOpen} 
        onClose={handleCloseDrawer} 
        view={drawerView}
      />
    </div>
  )
}

export default Layout

