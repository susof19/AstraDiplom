import { useState } from 'react'
import './Hints.css'

function Hints({ hints = [] }) {
  const [revealedHints, setRevealedHints] = useState([])

  if (!hints || hints.length === 0) {
    return null
  }

  const revealNextHint = () => {
    if (revealedHints.length < hints.length) {
      setRevealedHints([...revealedHints, revealedHints.length])
    }
  }

  const hasMoreHints = revealedHints.length < hints.length

  return (
    <div className="hints-section">
      <div className="hints-header">
        <h2>💡 Подсказки</h2>
        {hasMoreHints && (
          <button 
            className="btn-hint" 
            onClick={revealNextHint}
            disabled={!hasMoreHints}
          >
            Дать подсказку ({revealedHints.length + 1}/{hints.length})
          </button>
        )}
      </div>
      
      {revealedHints.length === 0 && (
        <div className="hints-placeholder">
          <p>Нажмите кнопку "Дать подсказку" чтобы получить первую подсказку</p>
        </div>
      )}

      {revealedHints.length > 0 && (
        <div className="hints-list">
          {revealedHints.map((hintIndex) => (
            <div key={hintIndex} className="hint-item">
              <span className="hint-number">{hintIndex + 1}</span>
              <div className="hint-content">
                {hints[hintIndex].split('\n').map((line, idx) => (
                  <div key={idx} className="hint-line">
                    {line}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {revealedHints.length === hints.length && (
        <div className="hints-complete">
          <p>✓ Все подсказки показаны</p>
        </div>
      )}
    </div>
  )
}

export default Hints

