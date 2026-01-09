import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { getMissions } from '../api/missions'
import MissionGeneratorChat from '../components/MissionGeneratorChat'
import './MissionList.css'

function MissionList() {
  const [searchParams] = useSearchParams()
  const level = searchParams.get('level')
  const [showGenerator, setShowGenerator] = useState(false)
  const [mounted, setMounted] = useState(false)
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  
  const { data: missions = [], isLoading } = useQuery({
    queryKey: ['missions', level],
    queryFn: () => getMissions(level)
  })

  useEffect(() => {
    setMounted(true)
    return () => setMounted(false)
  }, [])

  // Отладка
  console.log('MissionList render:', { showGenerator, level, mounted })

  const handleMissionCreated = (mission) => {
    // Обновляем список миссий
    queryClient.invalidateQueries(['missions', level])
    // Закрываем генератор
    setShowGenerator(false)
    // Переходим к созданной миссии
    setTimeout(() => {
      navigate(`/missions/${mission.id}`)
    }, 1000)
  }

  if (isLoading) {
    return <div className="loading">Загрузка миссий...</div>
  }

  const levelNames = {
    A: 'Новички',
    B: 'Продвинутые пользователи'
  }

  return (
    <div className="mission-list">
      <div className="header-section">
        <div className="header-top">
          <h1>Миссии</h1>
          <button 
            type="button"
            className="create-personal-mission-btn"
            onClick={() => {
              console.log('Кнопка нажата, текущее состояние showGenerator:', showGenerator)
              setShowGenerator(true)
              console.log('showGenerator установлен в true')
            }}
          >
            ✨ Создать личную миссию
          </button>
        </div>
        <div className="level-tabs">
          <Link 
            to="/missions?level=A" 
            className={`level-tab ${(!level || level === 'A') ? 'active' : ''}`}
          >
            Уровень A: Новички
          </Link>
          <Link 
            to="/missions?level=B" 
            className={`level-tab ${level === 'B' ? 'active' : ''}`}
          >
            Уровень B: Продвинутые пользователи
          </Link>
        </div>
        {level && (
          <div className="level-badge">
            Уровень {level}: {levelNames[level]}
          </div>
        )}
      </div>

      {showGenerator && mounted && createPortal(
        <div 
          className="modal-overlay" 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: '2rem'
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              console.log('Клик по overlay, закрываем')
              setShowGenerator(false)
            }
          }}
        >
          <div 
            className="modal-content" 
            style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              maxWidth: '900px',
              width: '100%',
              maxHeight: '90vh',
              overflow: 'hidden',
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
              position: 'relative'
            }}
            onClick={(e) => {
              e.stopPropagation()
            }}
          >
            <MissionGeneratorChat
              onMissionCreated={handleMissionCreated}
              onClose={() => {
                console.log('Закрываем генератор из компонента')
                setShowGenerator(false)
              }}
              initialLevel={level || 'A'}
            />
          </div>
        </div>,
        document.body
      )}

      {missions.length === 0 ? (
        <div className="empty-state">
          <p>Миссии не найдены</p>
        </div>
      ) : (
        <div className="missions-grid">
          {missions.map(mission => (
            <Link
              key={mission.id}
              to={`/missions/${mission.id}`}
              className={`mission-card ${mission.completed ? 'completed' : ''}`}
            >
              {mission.completed && (
                <div className="mission-completed-badge">
                  <span className="checkmark">✓</span>
                  <span className="score">{mission.score}%</span>
                </div>
              )}
              <div className="mission-header">
                <span className={`level-tag level-${mission.level}`}>
                  Уровень {mission.level}
                </span>
                {mission.is_personal && (
                  <span className="personal-badge">⭐ Личная</span>
                )}
                <span className="difficulty">
                  Сложность: {'⭐'.repeat(mission.difficulty || 1)}
                </span>
              </div>
              <h3>{mission.name}</h3>
              <p>{mission.description}</p>
              <div className="mission-footer">
                <span className="time">⏱️ {mission.estimated_time} мин</span>
                {mission.completed ? (
                  <span className="completed-indicator">✓ Пройдено</span>
                ) : (
                  <span className="arrow">→</span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

export default MissionList

