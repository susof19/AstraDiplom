import { useState } from 'react'
import './HintsSection.css'

function HintsSection({ hints = [] }) {
  const [revealedHints, setRevealedHints] = useState([])

  if (!hints || hints.length === 0) {
    return null
  }

  const revealNextHint = () => {
    if (revealedHints.length < hints.length) {
      setRevealedHints([...revealedHints, revealedHints.length])
    }
  }

  const allHintsRevealed = revealedHints.length >= hints.length

  return (
    <div className="hints-section">
      <div className="hints-header">
        <h2>💡 Подсказки:</h2>
        {!allHintsRevealed && (
          <button 
            className="btn-hint"
            onClick={revealNextHint}
            disabled={allHintsRevealed}
          >
            Дать подсказку
          </button>
        )}
      </div>
      
      {revealedHints.length === 0 && (
        <div className="hints-placeholder">
          <p>Нажмите кнопку "Дать подсказку" чтобы получить помощь</p>
        </div>
      )}

      {revealedHints.length > 0 && (
        <ul className="hints-list">
          {revealedHints.map((hintIndex) => (
            <li key={hintIndex} className="hint-item">
              <span className="hint-number">{hintIndex + 1}</span>
              <span className="hint-text">{hints[hintIndex]}</span>
            </li>
          ))}
        </ul>
      )}

      {allHintsRevealed && (
        <div className="hints-complete">
          <p>✓ Все подсказки открыты</p>
        </div>
      )}
    </div>
  )
}

export default HintsSection

