import { useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import { useTrafficStore } from './stores/trafficStore'
import { useWebSocketStore } from './stores/websocketStore'

// Simple placeholder pages
const Traffic = () => (
  <div className="text-center py-12">
    <h1 className="text-2xl font-bold mb-4">🗺️ Traffic Map</h1>
    <p className="text-gray-600">Interactive traffic map coming soon...</p>
  </div>
)

const Incidents = () => (
  <div className="text-center py-12">
    <h1 className="text-2xl font-bold mb-4">⚠️ Incidents</h1>
    <p className="text-gray-600">Incident management coming soon...</p>
  </div>
)

const Analytics = () => (
  <div className="text-center py-12">
    <h1 className="text-2xl font-bold mb-4">📊 Analytics</h1>
    <p className="text-gray-600">Advanced analytics coming soon...</p>
  </div>
)

const Settings = () => (
  <div className="text-center py-12">
    <h1 className="text-2xl font-bold mb-4">⚙️ Settings</h1>
    <p className="text-gray-600">System settings coming soon...</p>
  </div>
)

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