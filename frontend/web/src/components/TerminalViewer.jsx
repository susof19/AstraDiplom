import { useEffect, useRef, useState } from 'react'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import 'xterm/css/xterm.css'
import './TerminalViewer.css'

function TerminalViewer({ missionId, sandbox }) {
  const terminalRef = useRef(null)
  const terminal = useRef(null)
  const fitAddon = useRef(null)
  const socketRef = useRef(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!terminalRef.current || !sandbox || !sandbox.ssh_port) {
      return
    }

    // Инициализируем терминал
    if (!terminal.current) {
      terminal.current = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: 'Consolas, "Courier New", monospace',
        theme: {
          background: '#1e1e1e',
          foreground: '#d4d4d4',
          cursor: '#aeafad',
          black: '#000000',
          red: '#cd3131',
          green: '#0dbc79',
          yellow: '#e5e510',
          blue: '#2472c8',
          magenta: '#bc3fbc',
          cyan: '#11a8cd',
          white: '#e5e5e5',
          brightBlack: '#666666',
          brightRed: '#f14c4c',
          brightGreen: '#23d18b',
          brightYellow: '#f5f543',
          brightBlue: '#3b8eea',
          brightMagenta: '#d670d6',
          brightCyan: '#29b8db',
          brightWhite: '#e5e5e5'
        }
      })

      fitAddon.current = new FitAddon()
      terminal.current.loadAddon(fitAddon.current)
      terminal.current.loadAddon(new WebLinksAddon())
      terminal.current.open(terminalRef.current)
      fitAddon.current.fit()

      // Обработка изменения размера окна
      const handleResize = () => {
        if (fitAddon.current) {
          fitAddon.current.fit()
          if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            // Отправляем информацию о размере терминала в SSH (если нужно)
          }
        }
      }
      window.addEventListener('resize', handleResize)

      // Обработка ввода
      terminal.current.onData((data) => {
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
          socketRef.current.send(data)
        }
      })

      return () => {
        window.removeEventListener('resize', handleResize)
      }
    }
  }, [terminalRef.current, sandbox])

  useEffect(() => {
    if (!sandbox || !sandbox.ssh_port || !terminal.current) {
      return
    }

    // Подключаемся к WebSocket через прокси
    // Прокси автоматически перенаправит на правильный порт backend
    // Это решает проблему с динамическими портами
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/v1/sandbox/${missionId}/ssh`
    
    console.log(`Подключение к WebSocket: ${wsUrl}`)
    const ws = new WebSocket(wsUrl)
    socketRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket подключен успешно')
      setConnected(true)
      setError(null)
      terminal.current?.writeln('\r\n*** Подключено к SSH терминалу ***\r\n')
    }

    ws.onmessage = (event) => {
      if (event.data instanceof Blob) {
        event.data.arrayBuffer().then(buffer => {
          const data = new Uint8Array(buffer)
          terminal.current?.write(data)
        })
      } else {
        terminal.current?.write(event.data)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setError('Ошибка подключения к SSH терминалу. Проверьте, что бэкенд запущен и доступен.')
      setConnected(false)
    }

    ws.onclose = (event) => {
      console.log(`WebSocket закрыт. Код: ${event.code}, причина: ${event.reason}`)
      setConnected(false)
      if (event.code !== 1000) {
        terminal.current?.writeln(`\r\n*** Соединение закрыто (код: ${event.code}) ***\r`)
      } else {
        terminal.current?.writeln('\r\n*** Соединение закрыто ***\r')
      }
    }

    return () => {
      if (socketRef.current) {
        if (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING) {
          socketRef.current.close()
        }
        socketRef.current = null
      }
    }
  }, [missionId, sandbox?.ssh_port])

  if (!sandbox || !sandbox.ssh_port) {
    return (
      <div className="terminal-viewer">
        <div className="terminal-placeholder">
          <p>SSH порт не настроен</p>
          <p className="hint">Ожидание настройки SSH...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="terminal-viewer">
      <div className="terminal-header">
        <span className={`status-indicator ${connected ? 'active' : 'pending'}`}>
          {connected ? '● Подключено' : '○ Подключение...'}
        </span>
        <span>SSH порт: {sandbox.ssh_port}</span>
        <span>Пользователь: {sandbox.ssh_user || 'root'}</span>
      </div>
      {error && (
        <div className="terminal-error">
          <p>⚠️ {error}</p>
        </div>
      )}
      <div className="terminal-container" ref={terminalRef} />
    </div>
  )
}

export default TerminalViewer

