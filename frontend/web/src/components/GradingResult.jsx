import './GradingResult.css'

function GradingResult({ result, currentMissionId, nextMission, missionLevel, onClose, onNextMission, onRetryMission }) {
  if (!result) return null

  const { 
    result: status, 
    score, 
    points, 
    checks = [], 
    message,
    mission_passed,
    xp_earned,
    total_xp,
    new_achievements = []
  } = result

  const getStatusIcon = () => {
    if (mission_passed) return '✅'
    if (status === 'partial') return '⚠️'
    return '❌'
  }

  const getStatusClass = () => {
    if (mission_passed) return 'passed'
    if (status === 'partial') return 'partial'
    return 'failed'
  }

  const getStatusText = () => {
    if (mission_passed) return 'Миссия пройдена!'
    if (status === 'partial') return 'Миссия выполнена частично'
    return 'Миссия не пройдена'
  }

  return (
    <div className="grading-result-overlay" onClick={onClose}>
      <div className="grading-result" onClick={(e) => e.stopPropagation()}>
        <div className={`grading-header ${getStatusClass()}`}>
          <div className="grading-status">
            <span className="status-icon">{getStatusIcon()}</span>
            <h2>{getStatusText()}</h2>
          </div>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="grading-content">
          <div className="score-section">
            <div className="score-circle">
              <div className="score-value">{score}%</div>
              <div className="score-label">Оценка</div>
            </div>
            {points && (
              <div className="points-info">
                <div className="points-earned">
                  <span className="points-label">Получено баллов:</span>
                  <span className="points-value">{points.earned} / {points.total}</span>
                </div>
              </div>
            )}
          </div>

          {mission_passed && xp_earned > 0 && (
            <div className="xp-section">
              <div className="xp-earned">
                <span className="xp-icon">⭐</span>
                <span className="xp-text">Получено XP: <strong>{xp_earned}</strong></span>
              </div>
              {total_xp !== undefined && (
                <div className="xp-total">
                  Всего XP: <strong>{total_xp}</strong>
                </div>
              )}
            </div>
          )}

          {new_achievements.length > 0 && (
            <div className="achievements-section">
              <h3>🏆 Новые достижения:</h3>
              <ul>
                {new_achievements.map((achievement, idx) => (
                  <li key={idx}>{achievement}</li>
                ))}
              </ul>
            </div>
          )}

          {checks.length > 0 && (
            <div className="checks-section">
              <h3>Детали проверки:</h3>
              <div className="checks-list">
                {checks.map((check, idx) => (
                  <div key={idx} className={`check-item ${check.passed ? 'passed' : 'failed'}`}>
                    <span className="check-icon">{check.passed ? '✓' : '✗'}</span>
                    <div className="check-details">
                      <div className="check-name">{check.name}</div>
                      <div className="check-message">{check.message}</div>
                      {check.points !== undefined && (
                        <div className="check-points">
                          {check.earned_points || 0} / {check.points} баллов
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {message && (
            <div className="message-section">
              <p>{message}</p>
            </div>
          )}
        </div>

        <div className="grading-footer">
          <div className="grading-actions">
            {onRetryMission && (
              <button 
                className="btn btn-secondary" 
                onClick={onRetryMission}
              >
                🔄 Попробовать еще раз
              </button>
            )}
            {onNextMission && nextMission && (
              <button 
                className="btn btn-primary" 
                onClick={onNextMission}
              >
                ➡️ Следующее задание
              </button>
            )}
            {!nextMission && mission_passed && (
              <button 
                className="btn btn-primary" 
                onClick={() => {
                  onClose?.()
                  // Если это последнее задание, можно вернуться к списку
                  if (missionLevel) {
                    window.location.href = `/missions?level=${missionLevel}`
                  } else {
                    window.location.href = '/missions'
                  }
                }}
              >
                📋 Вернуться к списку миссий
              </button>
            )}
            {!nextMission && !mission_passed && (
          <button className="btn btn-primary" onClick={onClose}>
            Закрыть
          </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default GradingResult

