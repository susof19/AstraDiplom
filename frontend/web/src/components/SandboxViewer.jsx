import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getSandbox } from '../api/missions'
import './SandboxViewer.css'

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

function replaceLocalhostWithHostname(url) {
  if (!url) return url
  return url.replace(/localhost|127\.0\.0\.1/, window.location.hostname)
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
      if (isCreating || (query.state.data && !vncReady && (level === 'A' || level === 'B'))) {
        return 2000
      }
      return 5000
    }
  })

  useEffect(() => {
    if (isCreating && !sandbox) {
      setLoadingStage(LOADING_STAGES.CREATING)
      return
    }
    
    if (!sandbox) {
      setLoadingStage(null)
      return
    }
    
    if (sandbox.container_id) {
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
        setLoadingStage(LOADING_STAGES.READY)
      }
    } else if (sandbox.status) {
      setLoadingStage(LOADING_STAGES.STARTING)
    } else {
      setLoadingStage(LOADING_STAGES.CREATING)
    }
  }, [sandbox, isCreating, vncReady, level])

  useEffect(() => {
    if (sandbox?.novnc_port && sandbox?.vnc_url) {
      let retryCount = 0
      const maxRetries = 90
      let connectionCheckInterval = null
      
      const checkVncReady = () => {
        retryCount++
        
        if (sandbox.novnc_port && sandbox.vnc_url) {
          if (retryCount >= 15) {
            setVncReady(true)
            setVncError(null)
            setLoadingStage(LOADING_STAGES.READY)
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
      
      const checkConnectionStatus = () => {
        if (retryCount > 30 && !vncReady) {
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
      setVncReady(false)
      setVncError(null)
      setLoadingStage(null)
      setConnectionTimeout(false)
      setShowIframe(false)
    }
  }, [sandbox, vncReady])
  
  useEffect(() => {
    if (sandbox && (sandbox.status === 'stopped' || sandbox.status === 'removed')) {
      setVncReady(false)
      setVncError(null)
      setLoadingStage(null)
      setConnectionTimeout(false)
      setShowIframe(false)
    }
  }, [sandbox?.status])

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

  if ((level === 'A' || level === 'B' || sandbox.novnc_port) && sandbox.vnc_url && sandbox.status === 'running' && !isSandboxStopped) {
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
        
        {!showConnectionError && !connectionTimeout && sandbox.vnc_url && showIframe ? (
          <div className="vnc-container">
            <iframe
              ref={iframeRef}
              key={sandbox.vnc_url}
              src={replaceLocalhostWithHostname(sandbox.vnc_url)}
              title="Linux Desktop"
              className="vnc-iframe"
              allow="clipboard-read; clipboard-write"
              onLoad={() => {
                const timeoutId = setTimeout(() => {
                  if (sandbox.status === 'running' && !connectionTimeout) {
                    setVncReady(true)
                    setVncError(null)
                    setLoadingStage(LOADING_STAGES.READY)
                  }
                }, 5000)
                
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
              href={replaceLocalhostWithHostname(sandbox.vnc_url)} 
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

  return (
    <div className="sandbox-viewer">
      <div className="sandbox-header">
        <span className="status-indicator active">● Активна</span>
        <span>Контейнер: {sandbox.container_name}</span>
      </div>
      <div className="terminal-container">
        <div className="terminal-placeholder">
          <p>💻 Терминал</p>
          <p className="hint">Интеграция терминала в разработке</p>
        </div>
      </div>
    </div>
  )
}

export default SandboxViewer

