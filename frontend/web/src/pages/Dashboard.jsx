import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getMissions } from '../api/missions'
import './Dashboard.css'

function Dashboard() {
  const { data: missions = [], isLoading } = useQuery({
    queryKey: ['missions'],
    queryFn: getMissions
  })

  const missionsByLevel = {
    A: missions.filter(m => m.level === 'A'),
    B: missions.filter(m => m.level === 'B'),
    C: missions.filter(m => m.level === 'C')
  }

  if (isLoading) {
    return <div className="loading">Загрузка...</div>
  }

  return (
    <div className="dashboard">
      <div className="hero">
        <h1>Добро пожаловать в тренажёр Astra Linux!</h1>
        <p>Безопасно изучайте работу с Astra Linux через практические задания</p>
      </div>

      <div className="levels">
        <div className="level-card">
          <h2>Уровень A: Новички</h2>
          <p>GUI-ориентированные задания для начинающих пользователей</p>
          <div className="mission-count">{missionsByLevel.A.length} миссий</div>
          <Link to="/missions?level=A" className="btn">Начать обучение</Link>
        </div>

        <div className="level-card">
          <h2>Уровень B: Продвинутые</h2>
          <p>Работа с терминалом, скрипты, диагностика</p>
          <div className="mission-count">{missionsByLevel.B.length} миссий</div>
          <Link to="/missions?level=B" className="btn">Начать обучение</Link>
        </div>

        <div className="level-card">
          <h2>Уровень C: Администраторы</h2>
          <p>Инфраструктурные задачи, systemd, сеть, кластеры</p>
          <div className="mission-count">{missionsByLevel.C.length} миссий</div>
          <Link to="/missions?level=C" className="btn">Начать обучение</Link>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

