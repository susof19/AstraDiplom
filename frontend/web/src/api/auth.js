import axios from 'axios'

const API_BASE = '/api/v1'

// Получить информацию о текущем пользователе
export const getCurrentUser = async () => {
  const response = await axios.get(`${API_BASE}/auth/me`)
  return response.data
}

// Изменить пароль
export const changePassword = async (oldPassword, newPassword) => {
  const response = await axios.post(`${API_BASE}/auth/change-password`, {
    old_password: oldPassword,
    new_password: newPassword
  })
  return response.data
}

// Изменить имя пользователя
export const updateUsername = async (newUsername) => {
  const response = await axios.put(`${API_BASE}/auth/username`, {
    new_username: newUsername
  })
  return response.data
}

// Удалить аккаунт
export const deleteAccount = async (password) => {
  const response = await axios.delete(`${API_BASE}/auth/account`, {
    data: {
      password: password
    }
  })
  return response.data
}

// Получить информацию о секретном коде
export const getSecretCodeInfo = async () => {
  const response = await axios.get(`${API_BASE}/auth/secret-code-info`)
  return response.data
}
