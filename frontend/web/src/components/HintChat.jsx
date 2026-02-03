import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import './HintChat.css'

const HintChat = ({ missionId, mission, sandbox }) => {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const chatContainerRef = useRef(null)

  // Добавляем приветственное сообщение при загрузке
  useEffect(() => {
    if (messages.length === 0 && mission) {
      setMessages([{
        role: 'assistant',
        content: `Привет! 👋 Я бот-помощник для миссии "${mission.name}". Задайте мне вопрос, и я помогу вам выполнить задание!`
      }])
    }
  }, [mission, messages.length])

  // Прокрутка вниз при новых сообщениях
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || loading) return

    const userMessage = inputMessage.trim()
    setInputMessage('')
    
    // Добавляем сообщение пользователя
    const newUserMessage = {
      role: 'user',
      content: userMessage
    }
    setMessages(prev => [...prev, newUserMessage])
    setLoading(true)

    try {
      // Формируем историю диалога
      const conversationHistory = [...messages, newUserMessage].map(msg => ({
        role: msg.role,
        content: msg.content
      }))

      const response = await axios.post(
        `/api/v1/hints/chat/${missionId}`,
        {
          message: userMessage,
          conversation_history: conversationHistory
        }
      )

      // Добавляем ответ бота
      const botMessage = {
        role: 'assistant',
        content: response.data.message
      }
      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      console.error('Ошибка отправки сообщения:', error)
      const errorMessage = {
        role: 'assistant',
        content: 'Извините, произошла ошибка. Попробуйте еще раз или используйте обычные подсказки.'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const suggestedQuestions = [
    'С чего начать?',
    'Что нужно сделать?',
    'Как выполнить задание?',
    'Нужна подсказка'
  ]

  const handleSuggestedQuestion = (question) => {
    setInputMessage(question)
  }

  return (
    <div className="hint-chat">
      <div className="hint-chat-header">
        <h4>💬 Чат с помощником</h4>
        <span className="chat-status">
          {sandbox?.status === 'running' ? '🟢 Онлайн' : '⚪ Офлайн'}
        </span>
      </div>
      
      <div className="hint-chat-messages" ref={chatContainerRef}>
        {messages.map((message, index) => (
          <div
            key={index}
            className={`chat-message ${message.role === 'user' ? 'user-message' : 'bot-message'}`}
          >
            <div className="message-avatar">
              {message.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              <div className="message-text">{message.content}</div>
              <div className="message-time">
                {new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-message bot-message">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="message-text typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {messages.length === 1 && (
        <div className="suggested-questions">
          <p className="suggested-questions-title">Попробуйте спросить:</p>
          <div className="suggested-questions-list">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                className="suggested-question-btn"
                onClick={() => handleSuggestedQuestion(question)}
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      <form className="hint-chat-input-form" onSubmit={sendMessage}>
        <input
          type="text"
          className="hint-chat-input"
          placeholder="Задайте вопрос..."
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          className="hint-chat-send-btn"
          disabled={!inputMessage.trim() || loading}
        >
          {loading ? '⏳' : '📤'}
        </button>
      </form>
    </div>
  )
}

export default HintChat
