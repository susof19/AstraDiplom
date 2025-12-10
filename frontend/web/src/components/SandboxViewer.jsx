import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getSandbox } from '../api/missions'
import './SandboxViewer.css'

function SandboxViewer({ missionId, level }) {
  const canvasRef = useRef(null)
  const [connected, setConnected] = useState(false)
  
  const { data: sandbox } = useQuery({
    queryKey: ['sandbox', missionId],
    queryFn: () => getSandbox(missionId),
    enabled: !!missionId,
    refetchInterval: 5000
  })

  useEffect(() => {
    if (sandbox?.vnc_port && level === 'A') {
      // TODO: Подключение к noVNC
      // Пока показываем заглушку
      setConnected(true)
    }
  }, [sandbox, level])

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

  if (level === 'A' && sandbox.vnc_port) {
    return (
      <div className="sandbox-viewer">
        <div className="sandbox-header">
          <span className="status-indicator active">● Подключено</span>
          <span>VNC порт: {sandbox.vnc_port}</span>
        </div>
        <div className="vnc-container">
          <div className="vnc-placeholder">
            <p>🖥️ VNC подключение</p>
            <p>Порт: {sandbox.vnc_port}</p>
            <p className="hint">TODO: Интеграция noVNC</p>
          </div>
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

