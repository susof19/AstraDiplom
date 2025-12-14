import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { getMissions } from '../api/missions'
import './MissionList.css'

function MissionList() {
  const [searchParams] = useSearchParams()
  const level = searchParams.get('level')
  
  const { data: missions = [], isLoading } = useQuery({
    queryKey: ['missions', level],
    queryFn: () => getMissions(level)
  })

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
        <h1>Миссии</h1>
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

