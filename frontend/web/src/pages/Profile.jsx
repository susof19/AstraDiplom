import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { 
  getCurrentUser, 
  changePassword, 
  updateUsername, 
  deleteAccount, 
  getSecretCodeInfo 
} from '../api/auth'
import { getProgress } from '../api/missions'
import axios from 'axios'
import './Profile.css'

function Profile() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [activeTab, setActiveTab] = useState('achievements')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deletePassword, setDeletePassword] = useState('')
  const [deleteError, setDeleteError] = useState('')
  
  // Загрузка данных пользователя
  const { data: userInfo } = useQuery({
    queryKey: ['userInfo'],
    queryFn: getCurrentUser,
    enabled: !!user
  })
  
  // Загрузка прогресса
  const { data: progress } = useQuery({
    queryKey: ['progress'],
    queryFn: getProgress,
    enabled: !!user
  })
  
  // Загрузка достижений
  const { data: achievementsData } = useQuery({
    queryKey: ['achievements'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/progress/achievements')
      return response.data
    },
    enabled: !!user
  })
  
  // Загрузка информации о секретном коде
  const { data: secretCodeInfo } = useQuery({
    queryKey: ['secretCodeInfo'],
    queryFn: getSecretCodeInfo,
    enabled: !!user
  })
  
  // Мутация для изменения пароля
  const changePasswordMutation = useMutation({
    mutationFn: ({ oldPassword, newPassword }) => changePassword(oldPassword, newPassword),
    onSuccess: () => {
      alert('Пароль успешно изменён')
      setActiveTab('settings')
    },
    onError: (error) => {
      alert(error.response?.data?.detail || 'Ошибка при изменении пароля')
    }
  })
  
  // Мутация для изменения имени
  const updateUsernameMutation = useMutation({
    mutationFn: (newUsername) => updateUsername(newUsername),
    onSuccess: (data) => {
      alert('Имя пользователя успешно изменено')
      // Обновляем данные пользователя
      queryClient.invalidateQueries(['userInfo'])
      // Обновляем токен, если нужно
      window.location.reload()
    },
    onError: (error) => {
      alert(error.response?.data?.detail || 'Ошибка при изменении имени пользователя')
    }
  })
  
  // Мутация для удаления аккаунта
  const deleteAccountMutation = useMutation({
    mutationFn: (password) => deleteAccount(password),
    onSuccess: () => {
      logout()
      navigate('/login')
      alert('Аккаунт успешно удалён')
    },
    onError: (error) => {
      setDeleteError(error.response?.data?.detail || 'Ошибка при удалении аккаунта')
    }
  })
  
  const handleChangePassword = (e) => {
    e.preventDefault()
    const formData = new FormData(e.target)
    const oldPassword = formData.get('oldPassword')
    const newPassword = formData.get('newPassword')
    const confirmPassword = formData.get('confirmPassword')
    
    if (newPassword !== confirmPassword) {
      alert('Новые пароли не совпадают')
      return
    }
    
    changePasswordMutation.mutate({ oldPassword, newPassword })
  }
  
  const handleChangeUsername = (e) => {
    e.preventDefault()
    const formData = new FormData(e.target)
    const newUsername = formData.get('newUsername')
    
    if (!newUsername || newUsername.trim() === '') {
      alert('Имя пользователя не может быть пустым')
      return
    }
    
    if (newUsername === user?.username) {
      alert('Новое имя должно отличаться от текущего')
      return
    }
    
    if (!window.confirm('Вы уверены, что хотите изменить имя пользователя? Это действие нельзя отменить.')) {
      return
    }
    
    updateUsernameMutation.mutate(newUsername.trim())
  }
  
  const handleDeleteAccount = (e) => {
    e.preventDefault()
    const formData = new FormData(e.target)
    const password = formData.get('password')
    
    if (!password) {
      setDeleteError('Введите пароль для подтверждения')
      return
    }
    
    deleteAccountMutation.mutate(password)
  }
  
  const stats = progress || {
    total_score: 0,
    total_missions_completed: 0,
    level_progress: { A: 0, B: 0 }
  }
  
  const achievements = achievementsData?.achievements || []
  const totalMissions = stats.total_missions_completed || 0
  const level = totalMissions < 5 ? 'Новичок' : totalMissions < 10 ? 'Специалист' : 'Эксперт'
  
  return (
    <div className="profile-page">
      <div className="profile-container">
        <h1>Личный кабинет</h1>
        
        <div className="profile-tabs">
          <button 
            className={activeTab === 'achievements' ? 'active' : ''}
            onClick={() => setActiveTab('achievements')}
          >
            🏆 Достижения
          </button>
          <button 
            className={activeTab === 'settings' ? 'active' : ''}
            onClick={() => setActiveTab('settings')}
          >
            ⚙️ Настройки
          </button>
          <button 
            className={activeTab === 'security' ? 'active' : ''}
            onClick={() => setActiveTab('security')}
          >
            🔒 Безопасность
          </button>
        </div>
        
        <div className="profile-content">
          {activeTab === 'achievements' && (
            <div className="achievements-section">
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon">👤</div>
                  <div className="stat-label">Пользователь</div>
                  <div className="stat-value">{user?.username || 'Гость'}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">🏆</div>
                  <div className="stat-label">Уровень</div>
                  <div className="stat-value">{level}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">⭐</div>
                  <div className="stat-label">XP</div>
                  <div className="stat-value">{stats.total_score || 0}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">🎯</div>
                  <div className="stat-label">Миссий пройдено</div>
                  <div className="stat-value">{totalMissions}</div>
                </div>
              </div>
              
              <div className="achievements-list">
                <h2>Достижения</h2>
                {achievements.length > 0 ? (
                  <div className="achievements-grid">
                    {achievements.map((achievement) => (
                      <div key={achievement.id} className="achievement-card">
                        <div className="achievement-icon">🏅</div>
                        <div className="achievement-name">{achievement.name}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="no-achievements">Пока нет достижений. Пройдите миссии, чтобы получить достижения!</p>
                )}
              </div>
              
              <div className="progress-details">
                <h2>Прогресс по уровням</h2>
                <div className="level-progress">
                  <div className="level-item">
                    <span className="level-label">Уровень A:</span>
                    <span className="level-count">{stats.level_progress?.A || 0} миссий</span>
                  </div>
                  <div className="level-item">
                    <span className="level-label">Уровень B:</span>
                    <span className="level-count">{stats.level_progress?.B || 0} миссий</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'settings' && (
            <div className="settings-section">
              <div className="user-info-card">
                <h2>Информация о пользователе</h2>
                <div className="info-item">
                  <span className="info-label">Имя пользователя:</span>
                  <span className="info-value">{user?.username || 'Не указано'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Дата регистрации:</span>
                  <span className="info-value">
                    {userInfo?.created_at 
                      ? new Date(userInfo.created_at).toLocaleDateString('ru-RU')
                      : 'Не указано'}
                  </span>
                </div>
                <div className="info-item">
                  <span className="info-label">Последний вход:</span>
                  <span className="info-value">
                    {userInfo?.last_login 
                      ? new Date(userInfo.last_login).toLocaleString('ru-RU')
                      : 'Никогда'}
                  </span>
                </div>
                <div className="info-item">
                  <span className="info-label">Секретный код:</span>
                  <span className="info-value">
                    {secretCodeInfo?.has_secret_code ? '✅ Установлен' : '❌ Не установлен'}
                  </span>
                </div>
              </div>
              
              <form onSubmit={handleChangeUsername} className="settings-form">
                <h2>Изменить имя пользователя</h2>
                <div className="form-group">
                  <label htmlFor="newUsername">Новое имя пользователя</label>
                  <input
                    type="text"
                    id="newUsername"
                    name="newUsername"
                    placeholder="Введите новое имя"
                    required
                    minLength={3}
                    maxLength={50}
                    pattern="[a-zA-Z0-9_-]+"
                  />
                  <small>Только латинские буквы, цифры, подчеркивание и дефис (3-50 символов)</small>
                </div>
                <button 
                  type="submit" 
                  className="btn-primary"
                  disabled={updateUsernameMutation.isLoading}
                >
                  {updateUsernameMutation.isLoading ? 'Изменение...' : 'Изменить имя'}
                </button>
              </form>
            </div>
          )}
          
          {activeTab === 'security' && (
            <div className="security-section">
              <form onSubmit={handleChangePassword} className="settings-form">
                <h2>Изменить пароль</h2>
                <div className="form-group">
                  <label htmlFor="oldPassword">Текущий пароль</label>
                  <input
                    type="password"
                    id="oldPassword"
                    name="oldPassword"
                    placeholder="Введите текущий пароль"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="newPassword">Новый пароль</label>
                  <input
                    type="password"
                    id="newPassword"
                    name="newPassword"
                    placeholder="Введите новый пароль"
                    required
                    minLength={6}
                  />
                  <small>Минимум 6 символов, должна быть хотя бы одна буква и одна цифра</small>
                </div>
                <div className="form-group">
                  <label htmlFor="confirmPassword">Подтвердите новый пароль</label>
                  <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    placeholder="Повторите новый пароль"
                    required
                    minLength={6}
                  />
                </div>
                <button 
                  type="submit" 
                  className="btn-primary"
                  disabled={changePasswordMutation.isLoading}
                >
                  {changePasswordMutation.isLoading ? 'Изменение...' : 'Изменить пароль'}
                </button>
              </form>
              
              <div className="danger-zone">
                <h2>Опасная зона</h2>
                <p>Удаление аккаунта необратимо. Все ваши данные, прогресс и персональные миссии будут удалены.</p>
                {!showDeleteConfirm ? (
                  <button 
                    className="btn-danger"
                    onClick={() => setShowDeleteConfirm(true)}
                  >
                    Удалить аккаунт
                  </button>
                ) : (
                  <form onSubmit={handleDeleteAccount} className="delete-form">
                    <div className="form-group">
                      <label htmlFor="password">Введите пароль для подтверждения</label>
                      <input
                        type="password"
                        id="password"
                        name="password"
                        placeholder="Введите пароль"
                        required
                        value={deletePassword}
                        onChange={(e) => {
                          setDeletePassword(e.target.value)
                          setDeleteError('')
                        }}
                      />
                      {deleteError && <div className="error-message">{deleteError}</div>}
                    </div>
                    <div className="delete-actions">
                      <button 
                        type="submit" 
                        className="btn-danger"
                        disabled={deleteAccountMutation.isLoading}
                      >
                        {deleteAccountMutation.isLoading ? 'Удаление...' : 'Подтвердить удаление'}
                      </button>
                      <button 
                        type="button" 
                        className="btn-secondary"
                        onClick={() => {
                          setShowDeleteConfirm(false)
                          setDeletePassword('')
                          setDeleteError('')
                        }}
                      >
                        Отмена
                      </button>
                    </div>
                  </form>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Profile
