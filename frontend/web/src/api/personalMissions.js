import axios from 'axios'

const API_BASE = '/api/v1'

export const generatePersonalMission = async (request, level = 'A', conversationHistory = []) => {
  console.log('generatePersonalMission вызван:', { request, level, conversationHistory })
  try {
    const response = await axios.post(`${API_BASE}/personal-missions/generate`, {
      request,
      level,
      conversation_history: conversationHistory
    })
    console.log('generatePersonalMission получил ответ:', response.data)
    return response.data
  } catch (error) {
    console.error('Ошибка в generatePersonalMission:', error)
    console.error('Детали ошибки:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status
    })
    throw error
  }
}

export const chatForMission = async (messages) => {
  const response = await axios.post(`${API_BASE}/personal-missions/chat`, messages)
  return response.data
}

export const getPersonalMissions = async () => {
  const response = await axios.get(`${API_BASE}/personal-missions`)
  return response.data
}

export const deletePersonalMission = async (missionId) => {
  const response = await axios.delete(`${API_BASE}/personal-missions/${missionId}`)
  return response.data
}
