import axios from 'axios'

const API_BASE = '/api/v1'

// Получить информацию о текущем пользователе
export const getUserInfo = async () => {
  const response = await axios.get(`${API_BASE}/admin/user-info`)
  return response.data
}

// Создать миссию
export const createMission = async (missionData) => {
  const formData = new FormData()
  
  formData.append('mission_id', missionData.mission_id)
  formData.append('level', missionData.level)
  formData.append('name', missionData.name)
  formData.append('description', missionData.description)
  formData.append('difficulty', missionData.difficulty || 1)
  formData.append('estimated_time', missionData.estimated_time || 5)
  formData.append('objectives', JSON.stringify(missionData.objectives || []))
  formData.append('checks', JSON.stringify(missionData.checks || []))
  
  if (missionData.hints) {
    formData.append('hints', JSON.stringify(missionData.hints))
  }
  
  if (missionData.setup) {
    formData.append('setup', typeof missionData.setup === 'string' 
      ? missionData.setup 
      : JSON.stringify(missionData.setup))
  }
  
  const response = await axios.post(`${API_BASE}/admin/missions`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return response.data
}

// Обновить миссию
export const updateMission = async (missionId, missionData) => {
  const formData = new FormData()
  
  formData.append('level', missionData.level)
  formData.append('name', missionData.name)
  formData.append('description', missionData.description)
  formData.append('difficulty', missionData.difficulty || 1)
  formData.append('estimated_time', missionData.estimated_time || 5)
  formData.append('objectives', JSON.stringify(missionData.objectives || []))
  formData.append('checks', JSON.stringify(missionData.checks || []))
  
  if (missionData.hints) {
    formData.append('hints', JSON.stringify(missionData.hints))
  }
  
  if (missionData.setup) {
    formData.append('setup', typeof missionData.setup === 'string' 
      ? missionData.setup 
      : JSON.stringify(missionData.setup))
  }
  
  const response = await axios.put(`${API_BASE}/admin/missions/${missionId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return response.data
}

// Удалить миссию
export const deleteMission = async (missionId, level) => {
  const response = await axios.delete(`${API_BASE}/admin/missions/${missionId}`, {
    params: { level }
  })
  return response.data
}

// Загрузить файл для миссии
export const uploadMissionFile = async (missionId, level, file) => {
  const formData = new FormData()
  formData.append('level', level)
  formData.append('file', file)
  
  const response = await axios.post(`${API_BASE}/admin/missions/${missionId}/files`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return response.data
}

// Удалить файл миссии
export const deleteMissionFile = async (missionId, level, filename) => {
  const response = await axios.delete(`${API_BASE}/admin/missions/${missionId}/files/${filename}`, {
    params: { level }
  })
  return response.data
}

// Получить список всех пользователей
export const getUsers = async () => {
  const response = await axios.get(`${API_BASE}/admin/users-list`)
  return response.data
}

// Получить прогресс пользователя
export const getUserProgressAdmin = async (username) => {
  const response = await axios.get(`${API_BASE}/admin/users/${username}/progress`)
  return response.data
}
