import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMission, createSandbox, checkMission, getSandbox, stopSandbox } from '../api/missions'
import SandboxViewer from '../components/SandboxViewer'
import GradingResult from '../components/GradingResult'
import HintsSection from '../components/HintsSection'
import './MissionDetail.css'
import { useState } from 'react'

function MissionDetail() {
  const { missionId } = useParams()
  const queryClient = useQueryClient()
  const [showStopWarning, setShowStopWarning] = useState(false)
  const [gradingResult, setGradingResult] = useState(null)

  const { data: mission, isLoading } = useQuery({
    queryKey: ['mission', missionId],
    queryFn: () => getMission(missionId)
  })

  const { data: sandbox } = useQuery({
    queryKey: ['sandbox', missionId],
    queryFn: () => getSandbox(missionId),
    refetchInterval: 5000, // Обновляем каждые 5 секунд для проверки статуса
    retry: false
  })

  const createSandboxMutation = useMutation({
    mutationFn: () => createSandbox(missionId, mission?.level),
    onSuccess: () => {
      queryClient.invalidateQueries(['sandbox', missionId])
    }
  })

  const stopSandboxMutation = useMutation({
    mutationFn: () => stopSandbox(missionId),
    onSuccess: () => {
      queryClient.invalidateQueries(['sandbox', missionId])
      setShowStopWarning(false)
    }
  })

  const checkMissionMutation = useMutation({
    mutationFn: () => checkMission(missionId, mission?.level),
    onSuccess: (result) => {
      setGradingResult(result)
      // Обновляем прогресс и список миссий после проверки
      queryClient.invalidateQueries(['progress'])
      queryClient.invalidateQueries(['missions'])
    },
    onError: (error) => {
      setGradingResult({
        result: 'failed',
        score: 0,
        message: error.response?.data?.detail || 'Ошибка при проверке миссии'
      })
    }
  })

  const handleStopSandbox = () => {
    if (window.confirm(
      '⚠️ ВНИМАНИЕ!\n\n' +
      'Остановка песочницы приведет к:\n' +
      '• Потере всего несохраненного прогресса\n' +
      '• Удалению всех файлов и изменений в контейнере\n' +
      '• Необходимости перезапуска для продолжения работы\n\n' +
      'Вы уверены, что хотите остановить песочницу?'
    )) {
      stopSandboxMutation.mutate()
    }
  }

  if (isLoading) {
    return <div className="loading">Загрузка миссии...</div>
  }

  if (!mission) {
    return <div className="error">Миссия не найдена</div>
  }

  return (
    <div className="mission-detail">
      <div className="mission-info">
        <div className="mission-header">
          <div>
            <span className={`level-badge level-${mission.level}`}>
              Уровень {mission.level}
            </span>
            <h1>{mission.name}</h1>
          </div>
          <div className="mission-meta">
            <span>⏱️ {mission.estimated_time} мин</span>
            <span>⭐ {'⭐'.repeat(mission.difficulty || 1)}</span>
          </div>
        </div>

        <div className="mission-description">
          <p>{mission.description}</p>
        </div>

        <div className="objectives">
          <h2>Цели миссии:</h2>
          <ul>
            {mission.objectives?.map((obj, idx) => (
              <li key={idx}>{obj}</li>
            ))}
          </ul>
        </div>

        {mission.hints && mission.hints.length > 0 && (
          <HintsSection hints={mission.hints} />
        )}

        <div className="actions">
          {sandbox && sandbox.status === 'running' ? (
            <button
              onClick={handleStopSandbox}
              disabled={stopSandboxMutation.isLoading}
              className="btn btn-danger"
            >
              {stopSandboxMutation.isLoading ? 'Остановка...' : '🛑 Остановить песочницу'}
            </button>
          ) : (
            <button
              onClick={() => createSandboxMutation.mutate()}
              disabled={createSandboxMutation.isLoading}
              className="btn btn-primary"
            >
              {createSandboxMutation.isLoading ? 'Запуск...' : '🚀 Запустить песочницу'}
            </button>
          )}
          <button
            onClick={() => checkMissionMutation.mutate()}
            disabled={checkMissionMutation.isLoading || !sandbox || sandbox.status !== 'running'}
            className="btn btn-secondary"
          >
            {checkMissionMutation.isLoading ? 'Проверка...' : '✓ Проверить выполнение'}
          </button>
        </div>
      </div>

      <div className="sandbox-container">
        <SandboxViewer 
          missionId={missionId} 
          level={mission.level} 
          isCreating={createSandboxMutation.isLoading}
        />
      </div>

      {gradingResult && (
        <GradingResult 
          result={gradingResult} 
          onClose={() => setGradingResult(null)}
        />
      )}
    </div>
  )
}

export default MissionDetail

