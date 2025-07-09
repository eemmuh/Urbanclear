import { motion } from 'framer-motion'
import {
  CheckCircleIcon,
  XMarkIcon,
  ClockIcon,
  MapPinIcon,
} from '@heroicons/react/24/outline'
import { Incident } from '../types'
import { useTrafficStore } from '../stores/trafficStore'

interface IncidentsListProps {
  incidents: Incident[]
  showActions?: boolean
}

export default function IncidentsList({ incidents, showActions = true }: IncidentsListProps) {
  const { resolveIncident } = useTrafficStore()

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'severe':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'accident':
        return '🚗'
      case 'construction':
        return '🚧'
      case 'weather':
        return '🌧️'
      case 'road_closure':
        return '🚫'
      case 'congestion':
        return '🚦'
      default:
        return '⚠️'
    }
  }

  const handleResolveIncident = async (id: string) => {
    try {
      await resolveIncident(id)
    } catch (error) {
      console.error('Failed to resolve incident:', error)
    }
  }

  if (incidents.length === 0) {
    return (
      <div className="text-center py-12">
        <CheckCircleIcon className="w-12 h-12 text-green-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Incidents</h3>
        <p className="text-gray-500">All clear on monitored routes</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {incidents.map((incident, index) => (
        <motion.div
          key={incident.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm"
        >
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center space-x-3">
              <div className="text-2xl">{getTypeIcon(incident.type)}</div>
              <div>
                <div className="flex items-center space-x-2 mb-1">
                  <span className={`inline-flex px-2 py-1 text-xs font-medium rounded border ${getSeverityColor(incident.severity)}`}>
                    {incident.severity}
                  </span>
                  <span className="text-sm text-gray-500 capitalize">
                    {incident.type.replace('_', ' ')}
                  </span>
                </div>
                <h4 className="text-sm font-medium text-gray-900">
                  {incident.description}
                </h4>
              </div>
            </div>
            
            {showActions && !incident.is_resolved && (
              <div className="flex space-x-2">
                <button
                  onClick={() => handleResolveIncident(incident.id)}
                  className="text-green-600 hover:text-green-800 transition-colors"
                  title="Mark as resolved"
                >
                  <CheckCircleIcon className="w-5 h-5" />
                </button>
                <button
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                  title="Dismiss"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
            <div className="flex items-center space-x-2">
              <MapPinIcon className="w-4 h-4" />
              <span>{incident.location.address || 'Unknown location'}</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <ClockIcon className="w-4 h-4" />
              <span>
                {new Date(incident.reported_time).toLocaleString()}
              </span>
            </div>

            {incident.estimated_duration && (
              <div className="flex items-center space-x-2">
                <span className="text-gray-500">Duration:</span>
                <span>{incident.estimated_duration} minutes</span>
              </div>
            )}

            {incident.lanes_affected && (
              <div className="flex items-center space-x-2">
                <span className="text-gray-500">Lanes affected:</span>
                <span>{incident.lanes_affected}</span>
              </div>
            )}
          </div>

          {incident.is_resolved && (
            <div className="mt-3 p-2 bg-green-50 rounded border border-green-200">
              <div className="flex items-center space-x-2 text-green-800">
                <CheckCircleIcon className="w-4 h-4" />
                <span className="text-sm font-medium">Resolved</span>
                {incident.resolved_time && (
                  <span className="text-sm">
                    on {new Date(incident.resolved_time).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          )}
        </motion.div>
      ))}
    </div>
  )
} 