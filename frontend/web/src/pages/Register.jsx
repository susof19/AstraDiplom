import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './Login.css'

function Register() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [secretCode, setSecretCode] = useState('')
  const [error, setError] = useState('')
  const [usernameError, setUsernameError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [secretCodeError, setSecretCodeError] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  // Валидация username в реальном времени
  const handleUsernameChange = (e) => {
    const value = e.target.value
    
    // Блокируем ввод нелатинских символов
    const latinOnlyRegex = /^[a-zA-Z0-9_-]*$/
    if (!latinOnlyRegex.test(value)) {
      setUsernameError('Имя пользователя может содержать только латинские буквы (a-z, A-Z), цифры (0-9), подчеркивание (_) и дефис (-)')
      return
    }
    
    // Проверка на начало/конец с дефисом или подчеркиванием
    if (value && (value.startsWith('-') || value.startsWith('_') || value.endsWith('-') || value.endsWith('_'))) {
      setUsernameError('Имя пользователя не может начинаться или заканчиваться дефисом или подчеркиванием')
    } else if (value && value.length < 3) {
      setUsernameError('Имя пользователя должно содержать минимум 3 символа')
    } else if (value && !/[a-zA-Z]/.test(value)) {
      setUsernameError('Имя пользователя должно содержать хотя бы одну латинскую букву')
    } else if (value && /^\d+$/.test(value)) {
      setUsernameError('Имя пользователя не может состоять только из цифр')
    } else {
      setUsernameError('')
    }
    
    setUsername(value)
  }

  // Валидация пароля в реальном времени
  const handlePasswordChange = (e) => {
    const value = e.target.value
    
    // Блокируем ввод нелатинских символов
    const latinOnlyRegex = /^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]*$/
    if (value && !latinOnlyRegex.test(value)) {
      setPasswordError('Пароль может содержать только латинские буквы, цифры и специальные символы')
      setPassword(value)
      return
    }
    
    if (value && value.length < 6) {
      setPasswordError('Пароль должен содержать минимум 6 символов')
    } else if (value && !/[a-zA-Z]/.test(value)) {
      setPasswordError('Пароль должен содержать хотя бы одну латинскую букву')
    } else if (value && !/[0-9]/.test(value)) {
      setPasswordError('Пароль должен содержать хотя бы одну цифру')
    } else {
      setPasswordError('')
    }
    
    setPassword(value)
  }

  // Валидация секретного кода в реальном времени
  const handleSecretCodeChange = (e) => {
    const value = e.target.value
    
    // Блокируем ввод нелатинских символов
    const latinOnlyRegex = /^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]*$/
    if (value && !latinOnlyRegex.test(value)) {
      setSecretCodeError('Секретный код может содержать только латинские буквы, цифры и специальные символы')
      setSecretCode(value)
      return
    }
    
    if (value && value.length < 4) {
      setSecretCodeError('Секретный код должен содержать минимум 4 символа')
    } else {
      setSecretCodeError('')
    }
    
    setSecretCode(value)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    // Валидация username
    const trimmedUsername = username.trim()
    if (!trimmedUsername) {
      setError('Имя пользователя не может быть пустым')
      return
    }

    if (trimmedUsername.length < 3) {
      setError('Имя пользователя должно содержать минимум 3 символа')
      return
    }

    if (trimmedUsername.length > 50) {
      setError('Имя пользователя не может быть длиннее 50 символов')
      return
    }

    // Проверка на латиницу для username
    const usernameLatinRegex = /^[a-zA-Z0-9_-]+$/
    if (!usernameLatinRegex.test(trimmedUsername)) {
      setError('Имя пользователя может содержать только латинские буквы (a-z, A-Z), цифры (0-9), подчеркивание (_) и дефис (-)')
      return
    }

    if (!/[a-zA-Z]/.test(trimmedUsername)) {
      setError('Имя пользователя должно содержать хотя бы одну латинскую букву')
      return
    }

    if (/^\d+$/.test(trimmedUsername)) {
      setError('Имя пользователя не может состоять только из цифр')
      return
    }

    if (trimmedUsername.startsWith('-') || trimmedUsername.startsWith('_') || 
        trimmedUsername.endsWith('-') || trimmedUsername.endsWith('_')) {
      setError('Имя пользователя не может начинаться или заканчиваться дефисом или подчеркиванием')
      return
    }

    // Валидация пароля
    const trimmedPassword = password.trim()
    if (!trimmedPassword) {
      setError('Пароль не может быть пустым')
      return
    }

    if (trimmedPassword.length < 6) {
      setError('Пароль должен быть не менее 6 символов')
      return
    }

    // Проверка на латиницу и допустимые символы для пароля
    const passwordLatinRegex = /^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+$/
    if (!passwordLatinRegex.test(trimmedPassword)) {
      setError('Пароль может содержать только латинские буквы, цифры и специальные символы')
      return
    }

    if (!/[a-zA-Z]/.test(trimmedPassword)) {
      setError('Пароль должен содержать хотя бы одну латинскую букву')
      return
    }

    if (!/[0-9]/.test(trimmedPassword)) {
      setError('Пароль должен содержать хотя бы одну цифру')
      return
    }

    if (password !== confirmPassword) {
      setError('Пароли не совпадают')
      return
    }

    // Валидация секретного кода
    const trimmedSecretCode = secretCode.trim()
    if (!trimmedSecretCode) {
      setError('Секретный код не может быть пустым')
      return
    }

    if (trimmedSecretCode.length < 4) {
      setError('Секретный код должен быть не менее 4 символов')
      return
    }

    // Проверка на латиницу и допустимые символы для секретного кода
    const secretCodeLatinRegex = /^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+$/
    if (!secretCodeLatinRegex.test(trimmedSecretCode)) {
      setError('Секретный код может содержать только латинские буквы, цифры и специальные символы')
      return
    }

    setLoading(true)

    const result = await register(username, password, secretCode)
    
    if (result.success) {
      navigate('/')
    } else {
      setError(result.error)
    }
    
    setLoading(false)
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <h1>Регистрация</h1>
        <p className="auth-subtitle">Создайте аккаунт для доступа к тренажёру</p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="username">Имя пользователя</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={handleUsernameChange}
              onKeyPress={(e) => {
                // Блокируем ввод нелатинских символов
                const char = e.key
                const latinOnlyRegex = /^[a-zA-Z0-9_-]$/
                if (!latinOnlyRegex.test(char) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.key)) {
                  e.preventDefault()
                }
              }}
              required
              minLength={3}
              maxLength={50}
              autoComplete="username"
              className={usernameError ? 'error' : ''}
            />
            {usernameError && <small className="error-text">{usernameError}</small>}
            {!usernameError && <small>От 3 до 50 символов. Только латинские буквы (a-z, A-Z), цифры (0-9), подчеркивание (_) и дефис (-)</small>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Пароль</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={handlePasswordChange}
              onKeyPress={(e) => {
                // Блокируем ввод нелатинских символов
                const char = e.key
                const latinOnlyRegex = /^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]$/
                if (!latinOnlyRegex.test(char) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.key)) {
                  e.preventDefault()
                }
              }}
              required
              minLength={6}
              autoComplete="new-password"
              className={passwordError ? 'error' : ''}
            />
            {passwordError && <small className="error-text">{passwordError}</small>}
            {!passwordError && <small>Минимум 6 символов. Только латинские буквы, цифры и специальные символы. Должен содержать хотя бы одну букву и одну цифру.</small>}
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Подтвердите пароль</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              onKeyPress={(e) => {
                // Блокируем ввод нелатинских символов
                const char = e.key
                const latinOnlyRegex = /^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]$/
                if (!latinOnlyRegex.test(char) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.key)) {
                  e.preventDefault()
                }
              }}
              required
              minLength={6}
              autoComplete="new-password"
            />
          </div>

          <div className="form-group">
            <label htmlFor="secretCode">Секретный код для восстановления</label>
            <input
              id="secretCode"
              type="text"
              value={secretCode}
              onChange={handleSecretCodeChange}
              onKeyPress={(e) => {
                // Блокируем ввод нелатинских символов
                const char = e.key
                const latinOnlyRegex = /^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]$/
                if (!latinOnlyRegex.test(char) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.key)) {
                  e.preventDefault()
                }
              }}
              required
              minLength={4}
              maxLength={72}
              className={secretCodeError ? 'error' : ''}
            />
            {secretCodeError && <small className="error-text">{secretCodeError}</small>}
            {!secretCodeError && <small>Используется для восстановления пароля. Запомните его! Только латинские буквы, цифры и специальные символы.</small>}
          </div>

          <button type="submit" disabled={loading} className="auth-button">
            {loading ? 'Регистрация...' : 'Зарегистрироваться'}
          </button>
        </form>

        <div className="auth-links">
          <Link to="/login">Уже есть аккаунт? Войти</Link>
        </div>
      </div>
    </div>
  )
}

export default Register

