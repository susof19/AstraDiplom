import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getSandbox } from '../api/missions'
import './SandboxViewer.css'

// Этапы загрузки песочницы
const LOADING_STAGES = {
  CREATING: { 
    id: 'creating', 
    label: 'Создание контейнера...', 
    icon: '📦',
    description: 'Инициализация контейнера Docker/Podman'
  },
  STARTING: { 
    id: 'starting', 
    label: 'Запуск контейнера...', 
    icon: '🚀',
    description: 'Запуск системных служб'
  },
  INITIALIZING: { 
    id: 'initializing', 
    label: 'Инициализация системы...', 
    icon: '⚙️',
    description: 'Настройка окружения'
  },
  VNC_STARTING: { 
    id: 'vnc_starting', 
    label: 'Запуск VNC сервера...', 
    icon: '🖥️',
    description: 'Инициализация графического интерфейса'
  },
  VNC_READY: { 
    id: 'vnc_ready', 
    label: 'Подключение к рабочему столу...', 
    icon: '🔗',
    description: 'Установка соединения'
  },
  READY: { 
    id: 'ready', 
    label: 'Готово', 
    icon: '✅',
    description: 'Песочница готова к работе'
  }
}

function SandboxViewer({ missionId, level, isCreating = false }) {
  const iframeRef = useRef(null)
  const [vncReady, setVncReady] = useState(false)
  const [vncError, setVncError] = useState(null)
  const [loadingStage, setLoadingStage] = useState(null)
  const [connectionTimeout, setConnectionTimeout] = useState(false)
  const [showIframe, setShowIframe] = useState(false) // Задержка перед показом iframe
  
  const { data: sandbox, isLoading, isFetching } = useQuery({
    queryKey: ['sandbox', missionId],
    queryFn: () => getSandbox(missionId),
    enabled: !!missionId,
    refetchInterval: (query) => {
      // Если песочница создается или VNC не готов, опрашиваем чаще
      if (isCreating || (query.state.data && !vncReady && (level === 'A' || level === 'B'))) {
        return 2000
      }
      return 5000
    }
  })

  // Определяем текущий этап загрузки
  useEffect(() => {
    // Если идет создание и песочницы еще нет
    if (isCreating && !sandbox) {
      setLoadingStage(LOADING_STAGES.CREATING)
      return
    }
    
    // Если песочницы нет, сбрасываем этап
    if (!sandbox) {
      setLoadingStage(null)
      return
    }
    
    // Если есть container_id, значит контейнер создан и запущен
    if (sandbox.container_id) {
      // Для уровня A нужен VNC
      if (level === 'A' || level === 'B') {
        if (!sandbox.vnc_port) {
          setLoadingStage(LOADING_STAGES.INITIALIZING)
        } else if (!sandbox.novnc_port) {
          setLoadingStage(LOADING_STAGES.VNC_STARTING)
        } else if (!vncReady) {
          setLoadingStage(LOADING_STAGES.VNC_READY)
        } else {
          setLoadingStage(LOADING_STAGES.READY)
        }
      } else {
        // Для уровней B и C VNC не нужен
        setLoadingStage(LOADING_STAGES.READY)
      }
    } else if (sandbox.status) {
      // Если есть статус, но нет container_id, значит идет запуск
      setLoadingStage(LOADING_STAGES.STARTING)
    } else {
      // Иначе - создание
      setLoadingStage(LOADING_STAGES.CREATING)
    }
  }, [sandbox, isCreating, vncReady, level])

  useEffect(() => {
    if (sandbox?.novnc_port && sandbox?.vnc_url) {
      let retryCount = 0
      const maxRetries = 60 // 2 минуты максимум (60 * 2 секунды)
      let connectionCheckInterval = null
      
      // Проверяем готовность VNC сервера через проверку наличия порта и URL
      // Не используем fetch напрямую из-за CORS и проблем с localhost в браузере
      const checkVncReady = () => {
        retryCount++
        
        // Если есть novnc_port и vnc_url, считаем что VNC готов
        // Фактическую доступность проверит iframe
        if (sandbox.novnc_port && sandbox.vnc_url) {
          // Даем время на запуск (увеличено для более надежного запуска noVNC)
          if (retryCount >= 5) { // После 5 попыток (10 секунд) считаем готовым
            setVncReady(true)
            setVncError(null)
            setLoadingStage(LOADING_STAGES.READY)
            // Добавляем дополнительную задержку перед показом iframe (2 секунды)
            setTimeout(() => {
              setShowIframe(true)
            }, 2000)
            retryCount = 0
          } else {
            setVncError(`VNC сервер запускается... (попытка ${retryCount}/${maxRetries})`)
          }
        } else {
          if (retryCount < maxRetries) {
            setVncError(`Ожидание информации о VNC портах... (попытка ${retryCount}/${maxRetries})`)
          } else {
            setVncError('VNC сервер не отвечает. Проверьте логи контейнера.')
          }
        }
      }
      
      // Проверка состояния соединения - если iframe показывает экран подключения долгое время
      const checkConnectionStatus = () => {
        // Если прошло больше 30 секунд (15 попыток * 2 сек) и соединение не установлено
        if (retryCount > 15 && !vncReady) {
          setConnectionTimeout(true)
          setVncError('Не удалось установить соединение с VNC сервером. Возможно, рабочий стол не запущен.')
        }
      }
      
      checkVncReady()
      const interval = setInterval(checkVncReady, 2000)
      connectionCheckInterval = setInterval(checkConnectionStatus, 2000)
      
      return () => {
        if (interval) clearInterval(interval)
        if (connectionCheckInterval) clearInterval(connectionCheckInterval)
        retryCount = 0
      }
    } else {
      // Если нет novnc_port или песочница остановлена, сбрасываем состояние
      setVncReady(false)
      setVncError(null)
      setLoadingStage(null)
      setConnectionTimeout(false)
      setShowIframe(false)
    }
  }, [sandbox, vncReady])
  
  // Отслеживаем изменения статуса песочницы - если она остановлена, возвращаемся к исходному состоянию
  useEffect(() => {
    if (sandbox && (sandbox.status === 'stopped' || sandbox.status === 'removed')) {
      setVncReady(false)
      setVncError(null)
      setLoadingStage(null)
      setConnectionTimeout(false)
      setShowIframe(false)
    }
  }, [sandbox?.status])

  // Компонент индикатора загрузки с этапами
  const LoadingIndicator = ({ stage }) => {
    if (!stage) return null
    
    const stages = Object.values(LOADING_STAGES)
    const currentIndex = stages.findIndex(s => s.id === stage.id)
    
    return (
      <div className="sandbox-loading">
        <div className="loading-stages">
          {stages.slice(0, currentIndex + 1).map((s, idx) => (
            <div 
              key={s.id} 
              className={`loading-stage ${s.id === stage.id ? 'active' : 'completed'}`}
            >
              <div className="stage-icon">{s.icon}</div>
              <div className="stage-content">
                <div className="stage-label">{s.label}</div>
                {s.id === stage.id && (
                  <div className="stage-description">{s.description}</div>
                )}
              </div>
              {s.id !== stage.id && <div className="stage-check">✓</div>}
            </div>
          ))}
        </div>
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      </div>
    )
  }

  // Показываем индикатор загрузки если:
  // 1. Идет начальная загрузка
  // 2. Идет создание песочницы
  // 3. Песочница есть, но еще не готова (не достигнут этап READY)
  // 4. Песочница остановлена или удалена - возвращаемся к исходному состоянию
  const isSandboxStopped = sandbox && (sandbox.status === 'stopped' || sandbox.status === 'removed')
  const showLoading = isLoading || isCreating || (sandbox && !isSandboxStopped && loadingStage && loadingStage.id !== 'ready') || (!sandbox && isCreating)
  
  if (showLoading) {
    return (
      <div className="sandbox-viewer">
        <div className="sandbox-placeholder">
          <LoadingIndicator stage={loadingStage || LOADING_STAGES.CREATING} />
        </div>
      </div>
    )
  }

  // Если песочница остановлена, удалена или не существует - показываем исходное состояние
  if (!sandbox || isSandboxStopped) {
    return (
      <div className="sandbox-viewer">
        <div className="sandbox-placeholder">
          <p>{isSandboxStopped ? 'Песочница остановлена' : 'Песочница не запущена'}</p>
          <p className="hint">Нажмите "Запустить песочницу" для начала работы</p>
        </div>
      </div>
    )
  }

  // Для уровня A - GUI через noVNC
  // Показываем VNC только если песочница запущена
  if ((level === 'A' || level === 'B' || sandbox.novnc_port) && sandbox.vnc_url && sandbox.status === 'running' && !isSandboxStopped) {
    // Если соединение не установлено долгое время, показываем сообщение о проблеме
    const showConnectionError = vncError && vncError.includes('Не удалось установить соединение')
    
    return (
      <div className="sandbox-viewer">
        <div className="sandbox-header">
          <span className={`status-indicator ${vncReady && !showConnectionError ? 'active' : 'pending'}`}>
            {vncReady && !showConnectionError ? '● Подключено' : '○ Подключение...'}
          </span>
          <span>noVNC порт: {sandbox.novnc_port}</span>
          {sandbox.vnc_port && <span>VNC порт: {sandbox.vnc_port}</span>}
        </div>
        
        {showConnectionError && (
          <div className="vnc-loading">
            <p>⚠️ {vncError}</p>
            <p className="hint">Проверьте логи контейнера или перезапустите песочницу</p>
            <div className="vnc-troubleshooting">
              <p className="hint" style={{ marginTop: '1rem', color: '#ff9800' }}>
                💡 Возможные решения:
              </p>
              <ul className="hint" style={{ textAlign: 'left', marginTop: '0.5rem' }}>
                <li>Проверьте, что контейнер запущен: <code>docker ps</code> или <code>podman ps</code></li>
                <li>Проверьте логи контейнера на наличие ошибок</li>
                <li>Попробуйте перезапустить песочницу</li>
              </ul>
            </div>
          </div>
        )}
        
        {/* Показываем iframe только после задержки для загрузки noVNC */}
        {!showConnectionError && !connectionTimeout && sandbox.vnc_url && showIframe ? (
          <div className="vnc-container">
            <iframe
              ref={iframeRef}
              key={sandbox.vnc_url} // Ключ для пересоздания iframe при изменении URL
              src={sandbox.vnc_url}
              title="Linux Desktop"
              className="vnc-iframe"
              allow="clipboard-read; clipboard-write"
              onLoad={() => {
                // Если iframe загрузился, считаем что страница загружена
                // Но соединение может еще не быть установлено
                // Даем еще немного времени на установку соединения
                const timeoutId = setTimeout(() => {
                  if (sandbox.status === 'running' && !connectionTimeout) {
                    setVncReady(true)
                    setVncError(null)
                    setLoadingStage(LOADING_STAGES.READY)
                  }
                }, 5000) // Даем 5 секунд на установку соединения
                
                // Очищаем таймаут при размонтировании
                return () => clearTimeout(timeoutId)
              }}
              onError={() => {
                setVncError('Ошибка загрузки VNC интерфейса. Проверьте, что VNC сервер запущен.')
                setVncReady(false)
                setConnectionTimeout(true)
              }}
            />
          </div>
        ) : (
          !showConnectionError && (
            <div className="vnc-container">
              <div className="vnc-placeholder">
                {connectionTimeout ? (
                  <>
                    <p>⚠️ Соединение не установлено</p>
                    <p className="hint">Попробуйте перезапустить песочницу</p>
                  </>
                ) : (
                  <>
                    <p>🖥️ Запуск рабочего стола...</p>
                    <p className="hint">Пожалуйста, подождите</p>
                  </>
                )}
              </div>
            </div>
          )
        )}
        
        {!showConnectionError && (
          <div className="sandbox-footer">
            <p className="hint">
              💡 Совет: Используйте полноэкранный режим для лучшего опыта
            </p>
            <a 
              href={sandbox.vnc_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="external-link"
            >
              Открыть в новом окне ↗
            </a>
          </div>
        )}
      </div>
    )
  }

  // Для уровня B и C - терминал
  return (
    <div className="sandbox-viewer">
      <div className="sandbox-header">
        <span className="status-indicator active">● Активна</span>
        <span>Контейнер: {sandbox.container_name}</span>
      </div>
      <div className="terminal-container">
        <div className="terminal-placeholder">
          <p>💻 Терминал</p>
          <p className="hint">TODO: Интеграция xterm.js</p>
        </div>
      </div>
    </div>
  )
}

export default SandboxViewer

