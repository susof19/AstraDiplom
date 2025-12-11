import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getSandbox } from '../api/missions'
import './SandboxViewer.css'

function SandboxViewer({ missionId, level }) {
  const iframeRef = useRef(null)
  const [vncReady, setVncReady] = useState(false)
  const [vncError, setVncError] = useState(null)
  
  const { data: sandbox, isLoading } = useQuery({
    queryKey: ['sandbox', missionId],
    queryFn: () => getSandbox(missionId),
    enabled: !!missionId,
    refetchInterval: 5000
  })

  useEffect(() => {
    if (sandbox?.novnc_port && sandbox?.vnc_url) {
      // Проверяем готовность VNC сервера
      const checkVncReady = async () => {
        try {
          const response = await fetch(`http://localhost:${sandbox.novnc_port}/`)
          if (response.ok) {
            setVncReady(true)
            setVncError(null)
          }
        } catch (error) {
          console.error('VNC не готов:', error)
          setVncError('VNC сервер запускается...')
        }
      }
      
      checkVncReady()
      const interval = setInterval(checkVncReady, 3000)
      
      return () => clearInterval(interval)
    }
  }, [sandbox])

  if (isLoading) {
    return (
      <div className="sandbox-viewer">
        <div className="sandbox-placeholder">
          <p>⏳ Загрузка...</p>
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

