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
  
  const { data: sandbox, isLoading, isFetching } = useQuery({
    queryKey: ['sandbox', missionId],
    queryFn: () => getSandbox(missionId),
    enabled: !!missionId,
    refetchInterval: (query) => {
      // Если песочница создается или VNC не готов, опрашиваем чаще
      if (isCreating || (query.state.data && !vncReady && level === 'A')) {
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
      if (level === 'A') {
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
      // Проверяем готовность VNC сервера
      const checkVncReady = async () => {
        try {
          const response = await fetch(`http://localhost:${sandbox.novnc_port}/`)
          if (response.ok) {
            setVncReady(true)
            setVncError(null)
            setLoadingStage(LOADING_STAGES.READY)
          } else {
            setVncError('VNC сервер запускается...')
          }
        } catch (error) {
          console.error('VNC не готов:', error)
          setVncError('VNC сервер запускается...')
        }
      }
      
      checkVncReady()
      const interval = setInterval(checkVncReady, 2000)
      
      return () => clearInterval(interval)
    }
  }, [sandbox])

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
  const showLoading = isLoading || isCreating || (sandbox && loadingStage && loadingStage.id !== 'ready') || (!sandbox && isCreating)
  
  if (showLoading) {
    return (
      <div className="sandbox-viewer">
        <div className="sandbox-placeholder">
          <LoadingIndicator stage={loadingStage || LOADING_STAGES.CREATING} />
        </div>
      </div>
    )
  }

  if (!sandbox) {
    return (
      <div className="sandbox-viewer">
        <div className="sandbox-placeholder">
          <p>Песочница не запущена</p>
          <p className="hint">Нажмите "Запустить песочницу" для начала работы</p>
        </div>
      </div>
    )
  }

  // Для уровня A - GUI через noVNC
  if ((level === 'A' || sandbox.novnc_port) && sandbox.vnc_url) {
    return (
      <div className="sandbox-viewer">
        <div className="sandbox-header">
          <span className={`status-indicator ${vncReady ? 'active' : 'pending'}`}>
            {vncReady ? '● Подключено' : '○ Подключение...'}
          </span>
          <span>noVNC порт: {sandbox.novnc_port}</span>
          {sandbox.vnc_port && <span>VNC порт: {sandbox.vnc_port}</span>}
        </div>
        
        {vncError && !vncReady && (
          <div className="vnc-loading">
            <p>⏳ {vncError}</p>
            <p className="hint">Ожидание запуска VNC сервера в контейнере...</p>
          </div>
        )}
        
        {vncReady ? (
          <div className="vnc-container">
            <iframe
              ref={iframeRef}
              src={sandbox.vnc_url}
              title="Astra Linux Desktop"
              className="vnc-iframe"
              allow="clipboard-read; clipboard-write"
            />
          </div>
        ) : (
          <div className="vnc-container">
            <div className="vnc-placeholder">
              <p>🖥️ Запуск рабочего стола Astra Linux...</p>
              <p className="hint">Пожалуйста, подождите</p>
            </div>
          </div>
        )}
        
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

