import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './Login.css'

function RecoverPassword() {
  const [username, setUsername] = useState('')
  const [secretCode, setSecretCode] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)
  const { recoverPassword } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess(false)

    // Валидация
    if (newPassword !== confirmPassword) {
      setError('Пароли не совпадают')
      return
    }

    if (newPassword.length < 6) {
      setError('Пароль должен быть не менее 6 символов')
      return
    }

    setLoading(true)

    const result = await recoverPassword(username, secretCode, newPassword)
    
    if (result.success) {
      setSuccess(true)
      setTimeout(() => {
        navigate('/login')
      }, 2000)
    } else {
      setError(result.error)
    }
    
    setLoading(false)
  }

  if (success) {
    return (
      <div className="auth-page">
        <div className="auth-container">
          <h1>Пароль изменён</h1>
          <p className="success-message">Пароль успешно изменён. Перенаправление на страницу входа...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <h1>Восстановление пароля</h1>
        <p className="auth-subtitle">Введите имя пользователя и секретный код</p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="username">Имя пользователя</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label htmlFor="secretCode">Секретный код</label>
            <input
              id="secretCode"
              type="text"
              value={secretCode}
              onChange={(e) => setSecretCode(e.target.value)}
              required
              minLength={4}
            />
          </div>

          <div className="form-group">
            <label htmlFor="newPassword">Новый пароль</label>
            <input
              id="newPassword"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={6}
              autoComplete="new-password"
            />
            <small>Минимум 6 символов</small>
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Подтвердите новый пароль</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={6}
              autoComplete="new-password"
            />
          </div>

          <button type="submit" disabled={loading} className="auth-button">
            {loading ? 'Изменение...' : 'Изменить пароль'}
          </button>
        </form>

        <div className="auth-links">
          <Link to="/login">Вернуться к входу</Link>
        </div>
      </div>
    </div>
  )
}

export default RecoverPassword

