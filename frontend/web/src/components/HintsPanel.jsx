import { useState, useEffect } from 'react'
import axios from 'axios'
import './HintsPanel.css'

const HintsPanel = ({ missionId, checkResult, sandbox, mission, onClose }) => {
  const [hints, setHints] = useState([])
  const [staticHints, setStaticHints] = useState([])
  const [loading, setLoading] = useState(false)
  const [hintsEnabled, setHintsEnabled] = useState(true)
  const [mlEnabled, setMlEnabled] = useState(true)
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

  // Загружаем динамические подсказки после проверки
  useEffect(() => {
    if (checkResult && hintsEnabled) {
      loadHints()
    } else if (!checkResult && hintsEnabled && sandbox?.status === 'running') {
      // Можно загрузить общие подсказки для миссии
      loadGeneralHints()
    }
  }, [checkResult, missionId, hintsEnabled, mlEnabled, sandbox])

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

    setLoading(true)
    try {
      const response = await axios.post(
        `/api/v1/hints/check-result/${missionId}`,
        checkResult,
        {
          params: {
            use_ml: mlEnabled
          }
        }
      )
      setHints(response.data.hints || [])
    } catch (error) {
      console.error('Ошибка загрузки подсказок:', error)
      setHints([])
    } finally {
      setLoading(false)
    }
  }

  const loadGeneralHints = async () => {
    if (!missionId || !sandbox || sandbox.status !== 'running') return

    setLoading(true)
    try {
      const response = await axios.get(
        `/api/v1/hints/check/${missionId}`,
        {
          params: {
            use_ml: mlEnabled
          }
        }
      )
      setHints(response.data.hints || [])
    } catch (error) {
      console.error('Ошибка загрузки общих подсказок:', error)
      setHints([])
    } finally {
      setLoading(false)
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
    if (revealedDynamicHints.length < hints.length) {
      setRevealedDynamicHints([...revealedDynamicHints, revealedDynamicHints.length])
    }
  }

  // Определяем видимые подсказки (используем индексы из revealed массивов)
  const visibleStaticHints = revealedStaticHints.map(index => staticHints[index]).filter(Boolean)
  const visibleDynamicHints = revealedDynamicHints.map(index => hints[index]).filter(Boolean)
  const allStaticRevealed = revealedStaticHints.length >= staticHints.length
  const allDynamicRevealed = revealedDynamicHints.length >= hints.length
  const hasStaticHints = staticHints.length > 0
  const hasDynamicHints = hints.length > 0
  const hasAnyHints = hasStaticHints || hasDynamicHints || (checkResult && checkResult.result === 'passed')

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

      {hintsEnabled && (
        <div className="hints-content">
          {loading ? (
            <div className="hints-loading">Загрузка подсказок...</div>
          ) : hasAnyHints ? (
            <>
              {hasStaticHints && (
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
              )}
              {hasDynamicHints && (
                <div className="hints-section">
                  <div className="hints-section-header">
                    <h4 className="hints-section-title">
                      {checkResult ? '🤖 Умные подсказки на основе проверки:' : '💡 Контекстные подсказки:'}
                    </h4>
                    {!allDynamicRevealed && (
                      <button 
                        className="btn-hint"
                        onClick={revealNextDynamicHint}
                        disabled={allDynamicRevealed}
                      >
                        Дать подсказку
                      </button>
                    )}
                  </div>
                  {visibleDynamicHints.length === 0 && !allDynamicRevealed && (
                    <div className="hints-placeholder">
                      <p>Нажмите кнопку "Дать подсказку" чтобы получить помощь</p>
                    </div>
                  )}
                  {visibleDynamicHints.length > 0 && (
                    <ul className="hints-list">
                      {visibleDynamicHints.map((hint, index) => (
                        <li key={`dynamic-${revealedDynamicHints[index]}`} className="hint-item hint-dynamic">
                          <span className="hint-number">{index + 1}</span>
                          <span className="hint-text">{hint}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {allDynamicRevealed && (
                    <div className="hints-complete">
                      <p>✓ Все умные подсказки открыты</p>
                    </div>
                  )}
                </div>
              )}
              {checkResult && checkResult.result === 'passed' && (
                <div className="hints-success">
                  ✅ Все проверки пройдены! Отличная работа!
                </div>
              )}
            </>
          ) : checkResult ? (
            <div className="hints-empty">
              {checkResult.result === 'passed' 
                ? '✅ Все проверки пройдены! Отличная работа!'
                : 'Пока нет подсказок. Попробуйте выполнить проверку миссии.'}
            </div>
          ) : (
            <div className="hints-empty">
              {sandbox?.status === 'running' 
                ? 'Подсказки появятся после проверки миссии или при возникновении ошибок'
                : 'Запустите песочницу, чтобы получить подсказки'}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default HintsPanel

