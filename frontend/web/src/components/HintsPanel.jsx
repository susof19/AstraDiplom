import { useState, useEffect } from 'react'
import axios from 'axios'
import HintChat from './HintChat'
import './HintsPanel.css'

const HintsPanel = ({ missionId, checkResult, sandbox, mission, onClose }) => {
  const [staticHints, setStaticHints] = useState([]) // Общие подсказки
  const [loading, setLoading] = useState(false)
  const [hintsEnabled, setHintsEnabled] = useState(true)
  const [mlEnabled, setMlEnabled] = useState(true) // включён ли Чат-бот
  const [activeTab, setActiveTab] = useState('general') // 'general' или 'chat'
  const [revealedStaticHints, setRevealedStaticHints] = useState([])

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

  const loadHintSettings = async () => {
    try {
      const response = await axios.get('/api/v1/hints/settings')
      setHintsEnabled(response.data.hints_enabled)
      setMlEnabled(response.data.ml_enabled)
    } catch (error) {
      console.error('Ошибка загрузки настроек подсказок:', error)
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
    } catch (error) {
      console.error('Ошибка обновления настроек:', error)
    }
  }

  const revealNextStaticHint = () => {
    if (revealedStaticHints.length < staticHints.length) {
      setRevealedStaticHints([...revealedStaticHints, revealedStaticHints.length])
    }
  }

  // Определяем видимые подсказки (используем индексы из revealed массивов)
  const visibleStaticHints = revealedStaticHints.map(index => staticHints[index]).filter(Boolean)
  const allStaticRevealed = revealedStaticHints.length >= staticHints.length
  const hasStaticHints = staticHints.length > 0

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
              <span>Чат-бот</span>
            </label>
          )}
        </div>
        {onClose && (
          <button className="hints-close" onClick={onClose}>
            ×
          </button>
        )}
      </div>
      
      {/* Вкладки: Общие подсказки и Чат-бот */}
      {hintsEnabled && (
        <div className="hints-tabs">
          <button
            className={`hints-tab ${activeTab === 'general' ? 'active' : ''}`}
            onClick={() => setActiveTab('general')}
          >
            📚 Общие
          </button>
          <button
            className={`hints-tab ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
            disabled={!mlEnabled}
          >
            💬 Чат-бот
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
          
          {/* Вкладка "Чат-бот" */}
          {activeTab === 'chat' && (
            <>
              {!mlEnabled ? (
                <div className="hints-empty">
                  <p>Чат-бот отключен. Включите его в настройках выше.</p>
                </div>
              ) : (
                <HintChat 
                  missionId={missionId}
                  mission={mission}
                  sandbox={sandbox}
                />
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default HintsPanel

