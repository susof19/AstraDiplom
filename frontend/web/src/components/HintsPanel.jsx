import { useState, useEffect } from 'react'
import axios from 'axios'
import './HintsPanel.css'

const HintsPanel = ({ missionId, checkResult, sandbox, mission, onClose }) => {
  const [hints, setHints] = useState([]) // ML подсказки
  const [staticHints, setStaticHints] = useState([]) // Общие подсказки
  const [loading, setLoading] = useState(false)
  const [mlLoading, setMlLoading] = useState(false)
  const [hintsEnabled, setHintsEnabled] = useState(true)
  const [mlEnabled, setMlEnabled] = useState(true)
  const [activeTab, setActiveTab] = useState('general') // 'general' или 'ml'
  const [revealedStaticHints, setRevealedStaticHints] = useState([])
  const [revealedDynamicHints, setRevealedDynamicHints] = useState([])

  useEffect(() => {
    loadHintSettings()
  }, [])

  // Загружаем статические подсказки из конфигурации миссии
  useEffect(() => {
    if (mission?.hints && mission.hints.length > 0) {
      setStaticHints(mission.hints)
      // Сбрасываем открытые подсказки при смене миссии
      setRevealedStaticHints([])
    }
  }, [mission])

  // Сбрасываем открытые динамические подсказки при новой проверке
  useEffect(() => {
    if (checkResult) {
      setRevealedDynamicHints([])
    }
  }, [checkResult])

  // Загружаем ML подсказки во время прохождения миссии (realtime)
  useEffect(() => {
    if (sandbox?.status === 'running' && mlEnabled && !checkResult) {
      // Загружаем ML подсказки сразу при запуске
      loadRealtimeMLHints()
      
      // Затем обновляем каждые 20 секунд
      const interval = setInterval(() => {
        if (sandbox?.status === 'running' && !checkResult && mlEnabled) {
          loadRealtimeMLHints()
        }
      }, 20000) // Обновляем каждые 20 секунд для ML подсказок
      
      return () => clearInterval(interval)
    }
  }, [sandbox?.status, mlEnabled, missionId, checkResult])

  // Загружаем динамические подсказки после проверки (только если есть ошибки)
  useEffect(() => {
    if (checkResult && hintsEnabled) {
      // Проверяем, пройдена ли миссия
      const isPassed = checkResult.result === 'passed' || 
                      (checkResult.result === 'partial' && checkResult.score >= 70)
      
      // Загружаем подсказки только если миссия не пройдена
      if (!isPassed) {
        loadHints()
      } else {
        // Миссия пройдена - очищаем подсказки
        setHints([])
      }
    }
  }, [checkResult, missionId, hintsEnabled, mlEnabled])

  const loadHintSettings = async () => {
    try {
      const response = await axios.get('/api/v1/hints/settings')
      setHintsEnabled(response.data.hints_enabled)
      setMlEnabled(response.data.ml_enabled)
    } catch (error) {
      console.error('Ошибка загрузки настроек подсказок:', error)
    }
  }

  const loadHints = async () => {
    if (!missionId || !checkResult) return

    // Загружаем только ML подсказки при проверке
    if (mlEnabled) {
      setMlLoading(true)
      try {
        const response = await axios.post(
          `/api/v1/hints/check-result/${missionId}`,
          checkResult,
          {
            params: {
              use_ml: true
            }
          }
        )
        const newHints = response.data.hints || []
        
        // Добавляем новые подсказки без лимита
        setHints(prevHints => {
          const existingTexts = new Set(prevHints)
          const uniqueNewHints = newHints.filter(hint => !existingTexts.has(hint))
          return [...prevHints, ...uniqueNewHints]
        })
      } catch (error) {
        console.error('Ошибка загрузки ML подсказок:', error)
      } finally {
        setMlLoading(false)
      }
    }
  }

  const loadRealtimeMLHints = async () => {
    if (!missionId || !sandbox || sandbox.status !== 'running' || !mlEnabled) return

    setMlLoading(true)
    try {
      const response = await axios.get(
        `/api/v1/hints/check/${missionId}`,
        {
          params: {
            use_ml: true  // Всегда используем ML для realtime подсказок
          }
        }
      )
      const newHints = response.data.hints || []
      
      console.log('Получены ML подсказки:', newHints.length, newHints)
      
      // Добавляем только новые подсказки, которых еще нет (без лимита)
      setHints(prevHints => {
        const existingTexts = new Set(prevHints)
        const uniqueNewHints = newHints.filter(hint => hint && !existingTexts.has(hint))
        const updated = [...prevHints, ...uniqueNewHints]
        console.log('Обновленные подсказки:', updated.length)
        return updated
      })
    } catch (error) {
      console.error('Ошибка загрузки ML подсказок в реальном времени:', error)
      if (error.response) {
        console.error('Ответ сервера:', error.response.data)
      }
    } finally {
      setMlLoading(false)
    }
  }

  const toggleHints = async () => {
    const newValue = !hintsEnabled
    try {
      await axios.post('/api/v1/hints/settings', null, {
        params: {
          hints_enabled: newValue,
          ml_enabled: mlEnabled
        }
      })
      setHintsEnabled(newValue)
    } catch (error) {
      console.error('Ошибка обновления настроек:', error)
    }
  }

  const toggleML = async () => {
    const newValue = !mlEnabled
    try {
      await axios.post('/api/v1/hints/settings', null, {
        params: {
          hints_enabled: hintsEnabled,
          ml_enabled: newValue
        }
      })
      setMlEnabled(newValue)
      if (checkResult) {
        loadHints()
      }
    } catch (error) {
      console.error('Ошибка обновления настроек:', error)
    }
  }

  const revealNextStaticHint = () => {
    if (revealedStaticHints.length < staticHints.length) {
      setRevealedStaticHints([...revealedStaticHints, revealedStaticHints.length])
    }
  }

  const revealNextDynamicHint = () => {
    // Показываем подсказки постепенно, по одной
    if (revealedDynamicHints.length < hints.length) {
      setRevealedDynamicHints([...revealedDynamicHints, revealedDynamicHints.length])
    }
  }
  
  // Определяем видимые ML подсказки
  const visibleMLHints = revealedDynamicHints.map(index => hints[index]).filter(Boolean)
  const allMLRevealed = revealedDynamicHints.length >= hints.length
  
  // НЕ показываем ML подсказки автоматически - только по кнопке
  // Подсказки будут показываться постепенно при нажатии кнопки

  // Определяем видимые подсказки (используем индексы из revealed массивов)
  const visibleStaticHints = revealedStaticHints.map(index => staticHints[index]).filter(Boolean)
  const allStaticRevealed = revealedStaticHints.length >= staticHints.length
  const hasStaticHints = staticHints.length > 0
  
  // Проверяем, пройдена ли миссия
  const isPassed = checkResult && (
    checkResult.result === 'passed' || 
    (checkResult.result === 'partial' && checkResult.score >= 70)
  )

  return (
    <div className="hints-panel">
      <div className="hints-header">
        <h3>💡 Подсказки</h3>
        <div className="hints-controls">
          <label className="hint-toggle">
            <input
              type="checkbox"
              checked={hintsEnabled}
              onChange={toggleHints}
            />
            <span>Подсказки</span>
          </label>
          {hintsEnabled && (
            <label className="hint-toggle">
              <input
                type="checkbox"
                checked={mlEnabled}
                onChange={toggleML}
              />
              <span>ML подсказки</span>
            </label>
          )}
        </div>
        {onClose && (
          <button className="hints-close" onClick={onClose}>
            ×
          </button>
        )}
      </div>
      
      {/* Вкладки */}
      {hintsEnabled && (
        <div className="hints-tabs">
          <button
            className={`hints-tab ${activeTab === 'general' ? 'active' : ''}`}
            onClick={() => setActiveTab('general')}
          >
            📚 Общие
          </button>
          <button
            className={`hints-tab ${activeTab === 'ml' ? 'active' : ''}`}
            onClick={() => setActiveTab('ml')}
            disabled={!mlEnabled}
          >
            🤖 ML {sandbox?.status === 'running' && !checkResult && mlEnabled && (
              <span className="realtime-badge-small">🔄</span>
            )}
          </button>
        </div>
      )}

      {hintsEnabled && (
        <div className="hints-content">
          {/* Вкладка "Общие" */}
          {activeTab === 'general' && (
            <>
              {loading ? (
                <div className="hints-loading">Загрузка подсказок...</div>
              ) : hasStaticHints ? (
                <div className="hints-section">
                  <div className="hints-section-header">
                    <h4 className="hints-section-title">📚 Общие подсказки:</h4>
                    {!allStaticRevealed && (
                      <button 
                        className="btn-hint"
                        onClick={revealNextStaticHint}
                        disabled={allStaticRevealed}
                      >
                        Дать подсказку
                      </button>
                    )}
                  </div>
                  {visibleStaticHints.length === 0 && !allStaticRevealed && (
                    <div className="hints-placeholder">
                      <p>Нажмите кнопку "Дать подсказку" чтобы получить помощь</p>
                    </div>
                  )}
                  {visibleStaticHints.length > 0 && (
                    <ul className="hints-list">
                      {visibleStaticHints.map((hint, index) => (
                        <li key={`static-${revealedStaticHints[index]}`} className="hint-item hint-static">
                          <span className="hint-number">{index + 1}</span>
                          <span className="hint-text">{hint}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {allStaticRevealed && (
                    <div className="hints-complete">
                      <p>✓ Все общие подсказки открыты</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="hints-empty">
                  <p>Общих подсказок пока нет. Они появятся в конфигурации миссии.</p>
                </div>
              )}
            </>
          )}
          
          {/* Вкладка "ML" */}
          {activeTab === 'ml' && (
            <>
              {!mlEnabled ? (
                <div className="hints-empty">
                  <p>ML подсказки отключены. Включите их в настройках выше.</p>
                </div>
              ) : (
                <>
                  {mlLoading && (
                    <div className="hints-loading">Загрузка ML подсказок...</div>
                  )}
                  {!mlLoading && hints.length > 0 ? (
                    <div className="hints-section">
                      <div className="hints-section-header">
                        <h4 className="hints-section-title">
                          {checkResult 
                            ? '🤖 Умные подсказки на основе проверки:' 
                            : sandbox?.status === 'running'
                              ? '💡 Умные подсказки (в реальном времени):'
                              : '💡 Контекстные подсказки:'}
                        </h4>
                        {!allMLRevealed && (
                          <button 
                            className="btn-hint"
                            onClick={revealNextDynamicHint}
                            disabled={allMLRevealed}
                          >
                            Дать подсказку
                          </button>
                        )}
                        {sandbox?.status === 'running' && !checkResult && (
                          <span className="realtime-badge">🔄 Live</span>
                        )}
                      </div>
                      {visibleMLHints.length === 0 && !allMLRevealed && (
                        <div className="hints-placeholder">
                          <p>Нажмите кнопку "Дать подсказку" чтобы получить помощь</p>
                          {sandbox?.status === 'running' && (
                            <p className="realtime-info">Система анализирует ваши действия и предоставит подсказки при необходимости</p>
                          )}
                        </div>
                      )}
                      {visibleMLHints.length > 0 && (
                        <ul className="hints-list">
                          {visibleMLHints.map((hint, index) => {
                            if (!hint) return null
                            return (
                              <li key={`ml-${revealedDynamicHints[index]}-${hint.substring(0, 20)}`} className="hint-item hint-dynamic">
                                <span className="hint-icon">🤖</span>
                                <span className="hint-number">{index + 1}</span>
                                <span className="hint-text">{hint}</span>
                              </li>
                            )
                          })}
                        </ul>
                      )}
                      {allMLRevealed && (
                        <div className="hints-complete">
                          <p>✓ Все умные подсказки открыты</p>
                        </div>
                      )}
                      {sandbox?.status === 'running' && !checkResult && (
                        <div className="realtime-info">
                          <p>🔄 Подсказки обновляются автоматически каждые 20 секунд</p>
                          <p>Доступно подсказок: {hints.length} (открыто: {visibleMLHints.length})</p>
                        </div>
                      )}
                    </div>
                  ) : !mlLoading ? (
                    <div className="hints-placeholder">
                      <p>ML подсказки появятся автоматически во время работы</p>
                      {sandbox?.status === 'running' && (
                        <p className="realtime-info">Система анализирует ваши действия и предоставит подсказки при необходимости</p>
                      )}
                      {(!sandbox || sandbox.status !== 'running') && (
                        <p className="realtime-info">Запустите песочницу для получения ML подсказок</p>
                      )}
                    </div>
                  ) : null}
                </>
              )}
              {isPassed && (
                <div className="hints-success">
                  ✅ Все проверки пройдены! Отличная работа!
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default HintsPanel

