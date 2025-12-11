import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(localStorage.getItem('token'))

  // Настройка axios interceptor для добавления токена
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      localStorage.setItem('token', token)
    } else {
      delete axios.defaults.headers.common['Authorization']
      localStorage.removeItem('token')
    }
  }, [token])

  // Проверка токена при загрузке
  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        try {
          const response = await axios.get('/api/v1/auth/me')
          setUser(response.data)
        } catch (error) {
          // Токен недействителен
          setToken(null)
          setUser(null)
        }
      }
      setLoading(false)
    }
    checkAuth()
  }, [token])

  const login = async (username, password) => {
    try {
      const response = await axios.post('/api/v1/auth/login', {
        username,
        password
      })
      const { access_token, username: user } = response.data
      setToken(access_token)
      setUser({ username: user })
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Ошибка входа'
      }
    }
  }

  const register = async (username, password, secretCode) => {
    try {
      const response = await axios.post('/api/v1/auth/register', {
        username,
        password,
        secret_code: secretCode
      })
      const { access_token, username: user } = response.data
      setToken(access_token)
      setUser({ username: user })
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Ошибка регистрации'
      }
    }
  }

  const recoverPassword = async (username, secretCode, newPassword) => {
    try {
      await axios.post('/api/v1/auth/recover-password', {
        username,
        secret_code: secretCode,
        new_password: newPassword
      })
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Ошибка восстановления пароля'
      }
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
  }

  const value = {
    user,
    token,
    loading,
    login,
    register,
    recoverPassword,
    logout,
    isAuthenticated: !!user
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

