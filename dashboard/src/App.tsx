import { useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Traffic from './pages/Traffic'
import Incidents from './pages/Incidents'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'
import { useTrafficStore } from './stores/trafficStore'
import { useWebSocketStore } from './stores/websocketStore'

function App() {
  const { fetchTrafficData, fetchIncidents, fetchDashboardStats } = useTrafficStore()
  const { connect } = useWebSocketStore()

  useEffect(() => {
    // Initialize the application
    const initializeApp = async () => {
      try {
        await fetchDashboardStats()
        await fetchTrafficData()
        await fetchIncidents()
        connect()
      } catch (error) {
        console.error('Failed to initialize app:', error)
      }
    }

    initializeApp()
  }, [fetchDashboardStats, fetchTrafficData, fetchIncidents, connect])

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/traffic" element={<Traffic />} />
        <Route path="/incidents" element={<Incidents />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App 