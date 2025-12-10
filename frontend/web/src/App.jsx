import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import MissionList from './pages/MissionList'
import MissionDetail from './pages/MissionDetail'
import Dashboard from './pages/Dashboard'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/missions" element={<MissionList />} />
        <Route path="/missions/:missionId" element={<MissionDetail />} />
      </Routes>
    </Layout>
  )
}

export default App

