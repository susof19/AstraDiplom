import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMissions, getMission } from '../api/missions'
import { getUserInfo, createMission, updateMission, deleteMission, uploadMissionFile, getUsers, getUserProgressAdmin } from '../api/admin'
import toast from 'react-hot-toast'
import './AdminPanel.css'

function AdminPanel() {
  const queryClient = useQueryClient()
  const [editingMission, setEditingMission] = useState(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [selectedLevel, setSelectedLevel] = useState('A')
  const [activeTab, setActiveTab] = useState('missions') // 'missions' или 'users'
  const [selectedUser, setSelectedUser] = useState(null)

  // Получаем информацию о пользователе (проверка прав администратора)
  const { data: userInfo, isLoading: userLoading } = useQuery({
    queryKey: ['userInfo'],
    queryFn: getUserInfo,
    retry: false,
    onError: (error) => {
      if (error.response?.status === 403) {
        toast.error('Доступ запрещен. Требуются права администратора')
      }
    }
  })

  // Получаем список миссий
  const { data: missions = [], isLoading: missionsLoading } = useQuery({
    queryKey: ['missions', selectedLevel],
    queryFn: () => getMissions(selectedLevel),
    enabled: !!userInfo?.is_admin && activeTab === 'missions'
  })

  // Получаем список пользователей
  const { data: users = [], isLoading: usersLoading } = useQuery({
    queryKey: ['adminUsers'],
    queryFn: getUsers,
    enabled: !!userInfo?.is_admin && activeTab === 'users'
  })

  // Получаем прогресс выбранного пользователя (только для не-администраторов)
  const selectedUserData = users.find(u => u.username === selectedUser)
  const { data: userProgress, isLoading: progressLoading } = useQuery({
    queryKey: ['adminUserProgress', selectedUser],
    queryFn: () => getUserProgressAdmin(selectedUser),
    enabled: !!userInfo?.is_admin && !!selectedUser && selectedUserData && !selectedUserData.is_admin
  })

  // Мутация для создания миссии
  const createMissionMutation = useMutation({
    mutationFn: createMission,
    onSuccess: () => {
      toast.success('Миссия успешно создана')
      queryClient.invalidateQueries(['missions'])
      setShowCreateForm(false)
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Ошибка создания миссии')
    }
  })

  // Мутация для обновления миссии
  const updateMissionMutation = useMutation({
    mutationFn: ({ missionId, level, data }) => updateMission(missionId, { ...data, level }),
    onSuccess: () => {
      toast.success('Миссия успешно обновлена')
      queryClient.invalidateQueries(['missions'])
      setEditingMission(null)
      setShowCreateForm(false)
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Ошибка обновления миссии')
    }
  })

  // Мутация для удаления миссии
  const deleteMissionMutation = useMutation({
    mutationFn: ({ missionId, level }) => deleteMission(missionId, level),
    onSuccess: () => {
      toast.success('Миссия успешно удалена')
      queryClient.invalidateQueries(['missions'])
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Ошибка удаления миссии')
    }
  })

  const handleDelete = (missionId, level) => {
    if (window.confirm(`Вы уверены, что хотите удалить миссию ${missionId}?`)) {
      deleteMissionMutation.mutate({ missionId, level })
    }
  }

  const handleEdit = async (missionId, level) => {
    try {
      const mission = await getMission(missionId)
      setEditingMission({ ...mission, mission_id: missionId, originalLevel: level })
      setShowCreateForm(true)
    } catch (error) {
      toast.error('Ошибка загрузки миссии')
    }
  }

  if (userLoading) {
    return <div className="loading">Загрузка...</div>
  }

  if (!userInfo?.is_admin) {
    return (
      <div className="admin-panel">
        <div className="error-message">
          <h2>Доступ запрещен</h2>
          <p>Для доступа к панели администратора требуются соответствующие права.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <h1>Панель администратора</h1>
        <div className="admin-controls">
          {activeTab === 'missions' && (
            <button 
              className="btn btn-primary"
              onClick={() => {
                setEditingMission(null)
                setShowCreateForm(true)
              }}
            >
              ➕ Создать миссию
            </button>
          )}
        </div>
      </div>

      <div className="admin-tabs">
        <button 
          className={`admin-tab ${activeTab === 'missions' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('missions')
            setSelectedUser(null)
          }}
        >
          🎯 Миссии
        </button>
        <button 
          className={`admin-tab ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('users')
            setSelectedUser(null)
          }}
        >
          👥 Пользователи
        </button>
      </div>

      {activeTab === 'missions' && (
        <>
          <div className="level-tabs">
            <button 
              className={`level-tab ${selectedLevel === 'A' ? 'active' : ''}`}
              onClick={() => setSelectedLevel('A')}
            >
              Уровень A
            </button>
            <button 
              className={`level-tab ${selectedLevel === 'B' ? 'active' : ''}`}
              onClick={() => setSelectedLevel('B')}
            >
              Уровень B
            </button>
          </div>

          {showCreateForm && (
            <MissionForm
              mission={editingMission}
              onSave={(data) => {
                if (editingMission) {
                  updateMissionMutation.mutate({ 
                    missionId: editingMission.mission_id, 
                    level: editingMission.originalLevel || editingMission.level,
                    data 
                  })
                } else {
                  createMissionMutation.mutate(data)
                }
              }}
              onCancel={() => {
                setShowCreateForm(false)
                setEditingMission(null)
              }}
            />
          )}

          {missionsLoading ? (
            <div className="loading">Загрузка миссий...</div>
          ) : (
            <div className="missions-table">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Название</th>
                    <th>Сложность</th>
                    <th>Время</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {missions.map((mission) => (
                    <tr key={mission.id}>
                      <td>{mission.id}</td>
                      <td>{mission.name}</td>
                      <td>{'⭐'.repeat(mission.difficulty || 1)}</td>
                      <td>{mission.estimated_time} мин</td>
                      <td>
                        <button 
                          className="btn btn-small btn-secondary"
                          onClick={() => handleEdit(mission.id, mission.level)}
                        >
                          ✏️ Редактировать
                        </button>
                        <button 
                          className="btn btn-small btn-danger"
                          onClick={() => handleDelete(mission.id, mission.level)}
                          disabled={deleteMissionMutation.isLoading}
                        >
                          🗑️ Удалить
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {activeTab === 'users' && (
        <div className="users-section">
          {usersLoading ? (
            <div className="loading">Загрузка пользователей...</div>
          ) : (
            <div className="users-cards">
              {users.map((user) => (
                <UserCard
                  key={user.username}
                  user={user}
                  isSelected={selectedUser === user.username}
                  progress={selectedUser === user.username ? userProgress : null}
                  isLoading={selectedUser === user.username && progressLoading}
                  onSelect={() => {
                    if (selectedUser === user.username) {
                      setSelectedUser(null)
                    } else {
                      setSelectedUser(user.username)
                    }
                  }}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Компонент карточки пользователя
function UserCard({ user, isSelected, progress, isLoading, onSelect }) {
  return (
    <div className={`user-card ${isSelected ? 'selected' : ''}`}>
      <div className="user-card-header" onClick={onSelect}>
        <div className="user-card-info">
          <div className="user-card-title">
            {user.is_admin ? '👑' : '👤'} {user.username}
            {user.is_admin && <span className="admin-badge">Администратор</span>}
          </div>
          <div className="user-card-meta">
            <div className="user-meta-item">
              <span className="meta-label">Зарегистрирован:</span>
              <span className="meta-value">
                {user.created_at 
                  ? new Date(user.created_at).toLocaleDateString('ru-RU', { 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })
                  : '-'}
              </span>
            </div>
            <div className="user-meta-item">
              <span className="meta-label">Последний вход:</span>
              <span className="meta-value">
                {user.last_login 
                  ? new Date(user.last_login).toLocaleString('ru-RU', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })
                  : 'Никогда'}
              </span>
            </div>
          </div>
        </div>
        <button className="user-card-toggle">
          {isSelected ? '▼' : '▶'}
        </button>
      </div>

      {isSelected && !user.is_admin && (
        <div className="user-card-content">
          {isLoading ? (
            <div className="loading">Загрузка прогресса...</div>
          ) : progress ? (
            <UserProgressContent progress={progress} />
          ) : (
            <div className="error-message">
              <p>Прогресс не найден</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Компонент содержимого прогресса пользователя
function UserProgressContent({ progress }) {
  const stats = progress.stats || {}
  const missions = progress.missions_completed || {}

  return (
    <>
      <div className="user-progress-stats">
        <div className="stat-card">
          <div className="stat-card-label">Выполнено миссий</div>
          <div className="stat-card-value">{stats.total_missions_completed || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Общий счет</div>
          <div className="stat-card-value">{stats.total_score || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Средний балл</div>
          <div className="stat-card-value">{stats.average_score?.toFixed(1) || '0.0'}</div>
        </div>
      </div>

      {Object.keys(missions).length > 0 ? (
        <div className="missions-list">
          <h4>Выполненные миссии:</h4>
          {Object.entries(missions).map(([missionId, missionData]) => (
            <div key={missionId} className="mission-item">
              <div>
                <span className="mission-item-name">{missionId}</span>
                <div className="mission-item-details">
                  Уровень: {missionData.level || 'N/A'} | 
                  Попыток: {missionData.attempts || 1}
                  {missionData.completed_at && (
                    <> | Завершено: {new Date(missionData.completed_at).toLocaleDateString('ru-RU')}</>
                  )}
                </div>
              </div>
              <span className="mission-item-score">{missionData.score || 0}%</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="no-missions-message">
          <p>Пользователь еще не выполнил ни одной миссии</p>
        </div>
      )}
    </>
  )
}

// Компонент формы создания/редактирования миссии
function MissionForm({ mission, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    mission_id: mission?.mission_id || '',
    level: mission?.level || 'A',
    name: mission?.name || '',
    description: mission?.description || '',
    difficulty: mission?.difficulty || 1,
    estimated_time: mission?.estimated_time || 5,
    objectives: mission?.objectives ? JSON.stringify(mission.objectives, null, 2) : JSON.stringify([], null, 2),
    hints: mission?.hints ? JSON.stringify(mission.hints, null, 2) : JSON.stringify([], null, 2),
    checks: mission?.checks ? JSON.stringify(mission.checks, null, 2) : JSON.stringify([], null, 2),
    setup: mission?.setup ? JSON.stringify(mission.setup, null, 2) : ''
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    
    try {
      // Валидация JSON
      const objectives = JSON.parse(formData.objectives)
      const checks = JSON.parse(formData.checks)
      const hints = formData.hints ? JSON.parse(formData.hints) : []
      const setup = formData.setup ? JSON.parse(formData.setup) : null

      onSave({
        ...formData,
        objectives,
        checks,
        hints,
        setup
      })
    } catch (error) {
      toast.error(`Ошибка в JSON данных: ${error.message}`)
    }
  }

  return (
    <div className="mission-form-overlay">
      <div className="mission-form">
        <h2>{mission ? 'Редактировать миссию' : 'Создать новую миссию'}</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>ID миссии:</label>
            <input
              type="text"
              value={formData.mission_id}
              onChange={(e) => setFormData({ ...formData, mission_id: e.target.value })}
              required
              disabled={!!mission}
            />
          </div>

          <div className="form-group">
            <label>Уровень:</label>
            <select
              value={formData.level}
              onChange={(e) => setFormData({ ...formData, level: e.target.value })}
              required
            >
              <option value="A">A - Новички</option>
              <option value="B">B - Продвинутые</option>
            </select>
          </div>

          <div className="form-group">
            <label>Название:</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label>Описание:</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Сложность (1-5):</label>
              <input
                type="number"
                min="1"
                max="5"
                value={formData.difficulty}
                onChange={(e) => setFormData({ ...formData, difficulty: parseInt(e.target.value) })}
                required
              />
            </div>

            <div className="form-group">
              <label>Время (мин):</label>
              <input
                type="number"
                min="1"
                value={formData.estimated_time}
                onChange={(e) => setFormData({ ...formData, estimated_time: parseInt(e.target.value) })}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Цели (JSON массив строк):</label>
            <textarea
              value={formData.objectives}
              onChange={(e) => setFormData({ ...formData, objectives: e.target.value })}
              rows={4}
              required
            />
          </div>

          <div className="form-group">
            <label>Подсказки (JSON массив строк, опционально):</label>
            <textarea
              value={formData.hints}
              onChange={(e) => setFormData({ ...formData, hints: e.target.value })}
              rows={4}
            />
          </div>

          <div className="form-group">
            <label>Проверки (JSON массив объектов):</label>
            <textarea
              value={formData.checks}
              onChange={(e) => setFormData({ ...formData, checks: e.target.value })}
              rows={10}
              required
            />
          </div>

          <div className="form-group">
            <label>Настройка (JSON объект, опционально):</label>
            <textarea
              value={formData.setup}
              onChange={(e) => setFormData({ ...formData, setup: e.target.value })}
              rows={6}
            />
          </div>

          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={onCancel}>
              Отмена
            </button>
            <button type="submit" className="btn btn-primary">
              {mission ? 'Сохранить' : 'Создать'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default AdminPanel
