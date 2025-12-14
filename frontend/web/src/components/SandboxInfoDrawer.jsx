import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getActiveSandbox, getProcesses, getFilesystem, getNetwork } from '../api/missions'
import './SandboxInfoDrawer.css'

function SandboxInfoDrawer({ isOpen, onClose, view }) {
  const { data: activeSandbox } = useQuery({
    queryKey: ['activeSandbox'],
    queryFn: () => getActiveSandbox(),
    enabled: isOpen,
    refetchInterval: 5000,
    retry: false
  })

  const missionId = activeSandbox?.mission_id

  const { data: processesData, isLoading: processesLoading } = useQuery({
    queryKey: ['processes', missionId],
    queryFn: () => getProcesses(missionId),
    enabled: isOpen && view === 'processes' && !!missionId,
    refetchInterval: 3000
  })

  const [currentPath, setCurrentPath] = useState('/root')
  const { data: fsData, isLoading: fsLoading } = useQuery({
    queryKey: ['filesystem', missionId, currentPath],
    queryFn: () => getFilesystem(missionId, currentPath),
    enabled: isOpen && view === 'filesystem' && !!missionId,
    refetchInterval: 5000
  })

  const { data: networkData, isLoading: networkLoading } = useQuery({
    queryKey: ['network', missionId],
    queryFn: () => getNetwork(missionId),
    enabled: isOpen && view === 'network' && !!missionId,
    refetchInterval: 5000
  })

  if (!isOpen) return null

  const renderContent = () => {
    if (!activeSandbox?.has_active) {
      return (
        <div className="drawer-no-sandbox">
          <h2>⚠️ Песочница не запущена</h2>
          <p>Запустите песочницу для миссии, чтобы просмотреть информацию</p>
        </div>
      )
    }

    switch (view) {
      case 'processes':
        return (
          <div className="drawer-content">
            <div className="drawer-header">
              <h2>⚙️ Процессы</h2>
              <p className="drawer-subtitle">Миссия: {missionId} | Контейнер: {activeSandbox.container_name}</p>
            </div>
            {processesLoading ? (
              <div className="drawer-loading">Загрузка процессов...</div>
            ) : (
              <div className="drawer-body">
                <div className="drawer-stats">
                  <div className="drawer-stat-card">
                    <span className="drawer-stat-label">Всего процессов</span>
                    <span className="drawer-stat-value">{processesData?.count || 0}</span>
                  </div>
                </div>
                <div className="drawer-table-wrapper">
                  <table className="drawer-table">
                    <thead>
                      <tr>
                        <th>USER</th>
                        <th>PID</th>
                        <th>%CPU</th>
                        <th>%MEM</th>
                        <th>COMMAND</th>
                      </tr>
                    </thead>
                    <tbody>
                      {processesData?.processes?.slice(0, 20).map((proc, idx) => (
                        <tr key={`${proc.pid}-${idx}`}>
                          <td>{proc.user}</td>
                          <td>{proc.pid}</td>
                          <td>{proc.cpu}</td>
                          <td>{proc.mem}</td>
                          <td className="drawer-command-cell" title={proc.command}>
                            {proc.command.length > 40 ? `${proc.command.substring(0, 40)}...` : proc.command}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )

      case 'filesystem':
        return (
          <div className="drawer-content">
            <div className="drawer-header">
              <h2>📁 Файловая система</h2>
              <p className="drawer-subtitle">Миссия: {missionId} | Контейнер: {activeSandbox.container_name}</p>
            </div>
            {fsLoading ? (
              <div className="drawer-loading">Загрузка файловой системы...</div>
            ) : (
              <div className="drawer-body">
                <div className="drawer-path-navigation">
                  <input
                    type="text"
                    value={currentPath}
                    onChange={(e) => setCurrentPath(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && setCurrentPath(e.target.value)}
                    className="drawer-path-input"
                    placeholder="Введите путь..."
                  />
                  <button
                    onClick={() => setCurrentPath('/root')}
                    className="drawer-btn drawer-btn-secondary"
                  >
                    Домашняя
                  </button>
                </div>
                <div className="drawer-section">
                  <h3>💾 Использование диска</h3>
                  <pre className="drawer-code-block">{fsData?.disk_usage || 'Нет данных'}</pre>
                </div>
                <div className="drawer-section">
                  <h3>📂 Содержимое: {currentPath}</h3>
                  <pre className="drawer-code-block">{fsData?.directory_listing || 'Нет данных'}</pre>
                </div>
              </div>
            )}
          </div>
        )

      case 'network':
        return (
          <div className="drawer-content">
            <div className="drawer-header">
              <h2>🌐 Сеть</h2>
              <p className="drawer-subtitle">Миссия: {missionId} | Контейнер: {activeSandbox.container_name}</p>
            </div>
            {networkLoading ? (
              <div className="drawer-loading">Загрузка сетевой информации...</div>
            ) : (
              <div className="drawer-body">
                <div className="drawer-section">
                  <h3>🔌 Сетевые интерфейсы</h3>
                  <pre className="drawer-code-block">{networkData?.interfaces || 'Нет данных'}</pre>
                </div>
                <div className="drawer-section">
                  <h3>🔒 Открытые порты</h3>
                  <pre className="drawer-code-block">{networkData?.listening_ports || 'Нет данных'}</pre>
                </div>
                <div className="drawer-section">
                  <h3>📡 Активные соединения</h3>
                  <pre className="drawer-code-block">{networkData?.active_connections || 'Нет данных'}</pre>
                </div>
              </div>
            )}
          </div>
        )

      default:
        return <div className="drawer-loading">Выберите раздел</div>
    }
  }

  return (
    <>
      <div className={`drawer-overlay ${isOpen ? 'open' : ''}`} onClick={onClose}></div>
      <div className={`drawer ${isOpen ? 'open' : ''}`}>
        <div className="drawer-header-actions">
          <button className="drawer-close-btn" onClick={onClose}>×</button>
        </div>
        {renderContent()}
      </div>
    </>
  )
}

export default SandboxInfoDrawer

