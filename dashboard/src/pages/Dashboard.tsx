import { useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  MapPinIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  SignalIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
} from '@heroicons/react/24/outline'
import { useTrafficStore } from '../stores/trafficStore'
import { useWebSocketStore } from '../stores/websocketStore'
import StatsCard from '../components/StatsCard'
import RealtimeMap from '../components/maps/RealtimeMap'

export default function Dashboard() {
  const { 
    dashboardStats, 
    trafficData, 
    incidents, 
    isLoading, 
    error, 
    fetchDashboardStats,
    fetchTrafficData,
    fetchIncidents 
  } = useTrafficStore()
  
  const { isConnected } = useWebSocketStore()

  useEffect(() => {
    // Fetch initial data
    const loadData = async () => {
      await Promise.all([
        fetchDashboardStats(),
        fetchTrafficData(),
        fetchIncidents()
      ])
    }

    loadData()

    // Set up periodic refresh for when WebSocket is not connected
    const interval = setInterval(() => {
      if (!isConnected) {
        loadData()
      }
    }, 30000) // Refresh every 30 seconds

    return () => clearInterval(interval)
  }, [isConnected, fetchDashboardStats, fetchTrafficData, fetchIncidents])

  if (isLoading && !dashboardStats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error Loading Dashboard</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  const stats = dashboardStats || {
    total_intersections: 0,
    active_incidents: 0,
    average_speed: 0,
    congestion_percentage: 0,
    system_health: 'degraded' as const,
    last_updated: new Date().toISOString()
  }

  // Calculate recent traffic trends using the correct field name
  const recentTrafficData = trafficData.slice(0, 10)
  const avgSpeed = recentTrafficData.length > 0 
    ? recentTrafficData.reduce((sum, data) => sum + data.speed_mph, 0) / recentTrafficData.length 
    : 0

  const criticalIncidents = incidents.filter(incident => 
    incident.severity === 'critical' || incident.severity === 'severe'
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Traffic Dashboard</h1>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <ClockIcon className="h-4 w-4" />
          <span>Last updated: {new Date(stats.last_updated).toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Active Intersections"
          value={stats.total_intersections.toString()}
          icon={MapPinIcon}
          color="blue"
          trend={null}
        />
        
        <StatsCard
          title="Active Incidents"
          value={stats.active_incidents.toString()}
          icon={ExclamationTriangleIcon}
          color={stats.active_incidents > 5 ? "red" : "yellow"}
          trend={null}
          subtitle={`${criticalIncidents.length} critical`}
        />
        
        <StatsCard
          title="Average Speed"
          value={`${Math.round(avgSpeed || stats.average_speed)} mph`}
          icon={SignalIcon}
          color="green"
          trend={avgSpeed > 25 ? "up" : avgSpeed < 15 ? "down" : null}
        />
        
        <StatsCard
          title="Congestion Level"
          value={`${Math.round(stats.congestion_percentage)}%`}
          icon={stats.congestion_percentage > 60 ? ArrowTrendingUpIcon : ArrowTrendingDownIcon}
          color={stats.congestion_percentage > 60 ? "red" : stats.congestion_percentage > 30 ? "yellow" : "green"}
          trend={stats.congestion_percentage > 60 ? "up" : "down"}
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Traffic Map */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Real-time Traffic Map</h3>
              <div className="flex items-center space-x-2">
                <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                <span className="text-sm text-gray-500">
                  {isConnected ? 'Live Updates' : 'Static View'}
                </span>
              </div>
            </div>
            <div className="p-6">
              <RealtimeMap
                trafficData={trafficData}
                incidents={incidents}
                height={384}
              />
            </div>
          </div>
        </motion.div>

        {/* Incidents List */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recent Incidents</h3>
              <span className="text-sm text-gray-500">{incidents.length} active</span>
            </div>
            <div className="p-6">
              <div className="h-96 bg-gray-50 rounded-lg">
                {incidents.length > 0 ? (
                  <div className="space-y-3 p-4">
                    {incidents.slice(0, 3).map((incident) => (
                      <div key={incident.id} className="bg-white p-3 rounded border">
                        <div className="flex items-center justify-between mb-2">
                          <span className={`text-xs px-2 py-1 rounded font-medium ${
                            incident.severity === 'critical' || incident.severity === 'severe' 
                              ? 'bg-red-100 text-red-800' 
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {incident.severity}
                          </span>
                          <span className="text-xs text-gray-500 capitalize">
                            {incident.type.replace('_', ' ')}
                          </span>
                        </div>
                        <p className="text-sm text-gray-900 mb-1">{incident.description}</p>
                        <p className="text-xs text-gray-500">{incident.location.address}</p>
                        {incident.estimated_duration && (
                          <p className="text-xs text-gray-400 mt-1">
                            Duration: {incident.estimated_duration} min
                          </p>
                        )}
                      </div>
                    ))}
                    {incidents.length > 3 && (
                      <p className="text-center text-sm text-gray-500 pt-2">
                        +{incidents.length - 3} more incidents
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <div className="w-16 h-16 mx-auto mb-4 bg-gray-200 rounded-full flex items-center justify-center">
                        ✅
                      </div>
                      <h4 className="text-lg font-medium text-gray-900 mb-2">No Active Incidents</h4>
                      <p className="text-gray-500">All clear on monitored routes</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* System Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6">
              <div className="flex items-center">
                <div className={`h-3 w-3 rounded-full mr-3 ${
                  stats.system_health === 'healthy' ? 'bg-green-500' :
                  stats.system_health === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                }`} />
                <div>
                  <p className="text-sm font-medium text-gray-900">System Health</p>
                  <p className="text-sm text-gray-500 capitalize">{stats.system_health}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6">
              <div className="flex items-center">
                <SignalIcon className={`h-5 w-5 mr-3 ${isConnected ? 'text-green-500' : 'text-red-500'}`} />
                <div>
                  <p className="text-sm font-medium text-gray-900">Data Connection</p>
                  <p className="text-sm text-gray-500">{isConnected ? 'Connected' : 'Disconnected'}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6">
              <div className="flex items-center">
                <ClockIcon className="h-5 w-5 text-blue-500 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-900">Data Points</p>
                  <p className="text-sm text-gray-500">{trafficData.length} collected</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
} 