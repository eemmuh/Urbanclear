import { motion } from 'framer-motion'
import { useTrafficStore } from '../stores/trafficStore'
import IncidentsList from '../components/IncidentsList'

export default function Incidents() {
  const { incidents } = useTrafficStore()

  const activeIncidents = incidents.filter(i => !i.is_resolved)
  const resolvedIncidents = incidents.filter(i => i.is_resolved)

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <h1 className="text-2xl font-bold text-gray-900">Incident Management</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">Active Incidents</h3>
            <span className="text-sm text-gray-500">{activeIncidents.length} active</span>
          </div>
          <div className="card-content p-0">
            <div className="max-h-96 overflow-y-auto">
              <IncidentsList 
                incidents={activeIncidents}
                showActions={true}
              />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">Recently Resolved</h3>
            <span className="text-sm text-gray-500">{resolvedIncidents.length} resolved</span>
          </div>
          <div className="card-content p-0">
            <div className="max-h-96 overflow-y-auto">
              <IncidentsList 
                incidents={resolvedIncidents.slice(0, 10)}
                showActions={false}
              />
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
} 