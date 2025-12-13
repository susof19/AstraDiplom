import axios from 'axios'

const API_BASE = '/api/v1'

export const getMissions = async (level = null) => {
  const params = level ? { level } : {}
  const response = await axios.get(`${API_BASE}/missions`, { params })
  return response.data
}

export const getMission = async (missionId) => {
  const response = await axios.get(`${API_BASE}/missions/${missionId}`)
  return response.data
}

export const createSandbox = async (missionId, level) => {
  const response = await axios.post(`${API_BASE}/sandbox/create`, {
    mission_id: missionId,
    level,
    image: 'astra-linux:latest'
  })
  return response.data
}

export const getSandbox = async (missionId) => {
  try {
    const response = await axios.get(`${API_BASE}/sandbox/${missionId}`)
    return response.data
  } catch (error) {
    if (error.response?.status === 404) {
      return null
    }
    throw error
  }
}

export const checkMission = async (missionId, level) => {
  const response = await axios.post(`${API_BASE}/grader/check/${missionId}`, null, {
    params: { level }
  })
  return response.data
}

export const getProgress = async () => {
  try {
    const response = await axios.get(`${API_BASE}/progress`)
    return response.data
  } catch (error) {
    // 403 или 401 означает проблему с аутентификацией
    if (error.response?.status === 403 || error.response?.status === 401) {
      console.warn('Ошибка аутентификации при получении прогресса:', error.response?.data)
      // Возвращаем null, чтобы не ломать UI
      return null
    }
    if (error.response?.status === 404) {
      return null
    }
    throw error
  }
}

