import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { generatePersonalMission, chatForMission } from '../api/personalMissions'
import './MissionGeneratorChat.css'

function MissionGeneratorChat({ onMissionCreated, onClose, initialLevel = 'A' }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Привет! Я помогу тебе создать персональную миссию. Расскажи, чему ты хочешь научиться? Например: "Хочу научиться создавать файлы через графический интерфейс" или "Хочу изучить команды для работы с файлами в терминале".'
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [level, setLevel] = useState(initialLevel)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const chatMutation = useMutation({
    mutationFn: async (newMessages) => {
      return await chatForMission(newMessages)
    },
    onSuccess: (data) => {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.message
      }])
    },
    onError: (error) => {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Извините, произошла ошибка. Попробуйте еще раз.'
      }])
    }
  })

  const generateMutation = useMutation({
    mutationFn: async ({ request, conversationHistory }) => {
      console.log('generateMutation.mutationFn вызван:', { request, level, conversationHistory })
      try {
        const result = await generatePersonalMission(request, level, conversationHistory)
        console.log('generatePersonalMission вернул:', result)
        return result
      } catch (error) {
        console.error('Ошибка в generatePersonalMission:', error)
        throw error
      }
    },
    onSuccess: (data) => {
      console.log('generateMutation.onSuccess вызван, data:', data)
      
      if (data.is_existing) {
        // Найдена существующая миссия
        const similarity = data.similarity || 0
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `🔍 Найдена похожая миссия "${data.mission?.name || 'существующая миссия'}" (схожесть: ${similarity}%)! Вы можете использовать её вместо создания новой.`
        }])
      } else {
        // Создана новая миссия
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✅ Отлично! Миссия "${data.mission?.name || 'успешно создана'}" успешно создана! Теперь ты можешь перейти к ней и начать выполнение.`
      }])
      }
      
      if (onMissionCreated && data.mission) {
        console.log('Вызываем onMissionCreated с миссией:', data.mission)
        onMissionCreated(data.mission)
      }
    },
    onError: (error) => {
      console.error('generateMutation.onError вызван, error:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Неизвестная ошибка'
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Ошибка создания миссии: ${errorMessage}. Попробуйте переформулировать запрос или проверьте, что LLM сервис доступен.`
      }])
    }
  })

  const handleSend = async () => {
    if (!inputValue.trim() || isGenerating) return

    const userMessage = {
      role: 'user',
      content: inputValue
    }

    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInputValue('')
    setIsGenerating(true)

    // Определяем, нужно ли генерировать миссию или просто ответить
    const shouldGenerate = inputValue.toLowerCase().includes('создай') ||
                          inputValue.toLowerCase().includes('сделай') ||
                          inputValue.toLowerCase().includes('сгенерируй') ||
                          newMessages.length >= 4 // После нескольких сообщений предлагаем создать

    try {
      if (shouldGenerate) {
        // Генерируем миссию
        const conversationHistory = newMessages
          .filter(m => m.role !== 'system')
          .map(m => ({ role: m.role, content: m.content }))
        
        await generateMutation.mutateAsync({
          request: inputValue,
          conversationHistory
        })
      } else {
        // Просто чат для уточнения
        await chatMutation.mutateAsync(newMessages.map(m => ({
          role: m.role,
          content: m.content
        })))
      }
    } catch (error) {
      console.error('Ошибка:', error)
    } finally {
      setIsGenerating(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleGenerateNow = async () => {
    if (isGenerating) {
      console.log('Генерация уже идет, пропускаем')
      return
    }

    console.log('handleGenerateNow вызван, inputValue:', inputValue)
    console.log('messages:', messages)

    // Если есть незавершенное сообщение в поле ввода, добавляем его
    let newMessages = messages
    if (inputValue.trim()) {
      const userMessage = {
        role: 'user',
        content: inputValue.trim()
      }
      newMessages = [...messages, userMessage]
      setMessages(newMessages)
      setInputValue('')
    }

    // Формируем запрос на основе последнего сообщения пользователя или истории
    const lastUserMessage = [...newMessages].reverse().find(m => m.role === 'user')
    const requestText = lastUserMessage?.content || 'Создай миссию на основе нашего разговора'
    
    console.log('Генерируем миссию с запросом:', requestText)
    console.log('Уровень:', level)

    setIsGenerating(true)
    
    try {
      const conversationHistory = newMessages
        .filter(m => m.role !== 'system')
        .map(m => ({ role: m.role, content: m.content }))
      
      console.log('Отправляем запрос на генерацию миссии...')
      const result = await generateMutation.mutateAsync({
        request: requestText,
        conversationHistory
      })
      console.log('Результат генерации:', result)
    } catch (error) {
      console.error('Ошибка при генерации миссии:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Ошибка создания миссии: ${error.response?.data?.detail || error.message || 'Неизвестная ошибка'}. Проверьте консоль для деталей.`
      }])
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="mission-generator-chat">
      <div className="chat-header">
        <h2>Создание персональной миссии</h2>
        <div className="level-selector">
          <label>Уровень:</label>
          <select value={level} onChange={(e) => setLevel(e.target.value)}>
            <option value="A">A - GUI (Новички)</option>
            <option value="B">B - CLI (Продвинутые)</option>
          </select>
        </div>
        <button className="close-button" onClick={onClose}>×</button>
      </div>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.content}
            </div>
          </div>
        ))}
        {(isGenerating || generateMutation.isPending) && (
          <div className="message assistant">
            <div className="message-content">
              <span className="typing-indicator">🔄 Генерирую миссию на основе вашего запроса... Это может занять некоторое время.</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <textarea
          ref={inputRef}
          className="chat-input"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Опиши, чему ты хочешь научиться..."
          rows={2}
          disabled={isGenerating || generateMutation.isPending}
        />
        <div className="chat-actions">
          <button
            className="btn-primary"
            onClick={handleSend}
            disabled={!inputValue.trim() || isGenerating || generateMutation.isPending}
          >
            {isGenerating ? 'Отправка...' : 'Отправить'}
          </button>
          {messages.length > 2 && (
            <button
              className="btn-secondary"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                console.log('Кнопка "Создать миссию сейчас" нажата')
                handleGenerateNow()
              }}
              disabled={isGenerating || generateMutation.isPending}
            >
              {isGenerating || generateMutation.isPending ? '🔄 Создание миссии...' : '✨ Создать миссию сейчас'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default MissionGeneratorChat
