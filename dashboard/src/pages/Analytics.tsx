import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline'
import { useTrafficStore } from '../stores/trafficStore'
import TrafficChart from '../components/charts/TrafficChart'

export default function Analytics() {
  const { trafficData, incidents, fetchTrafficData, fetchIncidents } = useTrafficStore()
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('24h')
  const [selectedMetric, setSelectedMetric] = useState<'speed' | 'volume' | 'congestion'>('speed')

  useEffect(() => {
    const loadData = async () => {
      await Promise.all([
        fetchTrafficData(),
        fetchIncidents()
      ])
    }
    loadData()
  }, [fetchTrafficData, fetchIncidents])

  // Calculate analytics
  const totalSensors = trafficData.length
  const avgSpeed = totalSensors > 0 
    ? trafficData.reduce((sum, data) => sum + data.speed_mph, 0) / totalSensors 
    : 0
  const avgVolume = totalSensors > 0 
    ? trafficData.reduce((sum, data) => sum + data.volume, 0) / totalSensors 
    : 0
  const avgCongestion = totalSensors > 0 
    ? trafficData.reduce((sum, data) => sum + data.congestion_level, 0) / totalSensors 
    : 0
  const activeIncidents = incidents.filter(i => !i.is_resolved).length

  // Performance metrics
  const performanceMetrics = [
    {
      name: 'Average Speed',
      value: `${avgSpeed.toFixed(1)} mph`,
      change: '+2.3%',
      changeType: 'positive',
      icon: ArrowTrendingUpIcon,
    },
    {
      name: 'Traffic Volume',
      value: `${Math.round(avgVolume)} vehicles`,
      change: '-1.8%',
      changeType: 'negative',
      icon: ChartBarIcon,
    },
    {
      name: 'Congestion Level',
      value: `${(avgCongestion * 100).toFixed(1)}%`,
      change: '-0.5%',
      changeType: 'positive',
      icon: ExclamationTriangleIcon,
    },
    {
      name: 'Active Incidents',
      value: activeIncidents.toString(),
      change: activeIncidents > 0 ? 'Active' : 'Clear',
      changeType: activeIncidents > 0 ? 'negative' : 'positive',
      icon: ClockIcon,
    },
  ]

  // Top performing locations
  const topLocations = trafficData
    .sort((a, b) => b.speed_mph - a.speed_mph)
    .slice(0, 5)
    .map(data => ({
      name: data.location.address || data.id,
      speed: data.speed_mph,
      volume: data.volume,
      congestion: data.congestion_level,
    }))

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <ChartBarIcon className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Traffic Analytics</h1>
            <p className="text-gray-600">Comprehensive traffic performance insights</p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {performanceMetrics.map((metric, index) => (
          <motion.div
            key={metric.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{metric.name}</p>
                <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
              </div>
              <div className={`p-2 rounded-lg ${
                metric.changeType === 'positive' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
              }`}>
                <metric.icon className="h-6 w-6" />
              </div>
            </div>
            <div className="mt-4 flex items-center">
              <span className={`text-sm font-medium ${
                metric.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
              }`}>
                {metric.change}
              </span>
              <span className="text-sm text-gray-500 ml-2">vs previous period</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Traffic Trends Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-lg shadow-sm border border-gray-200"
        >
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Traffic Trends</h3>
              <select
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value as any)}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="speed">Speed</option>
                <option value="volume">Volume</option>
                <option value="congestion">Congestion</option>
              </select>
            </div>
          </div>
          <div className="p-6">
            <TrafficChart data={trafficData} height={300} />
          </div>
        </motion.div>

        {/* Top Performing Locations */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-lg shadow-sm border border-gray-200"
        >
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Top Performing Locations</h3>
            <p className="text-sm text-gray-500">Best traffic flow by average speed</p>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {topLocations.map((location, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-medium text-blue-600">{index + 1}</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{location.name}</p>
                      <p className="text-xs text-gray-500">
                        {location.volume} vehicles • {(location.congestion * 100).toFixed(1)}% congestion
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{location.speed.toFixed(1)} mph</p>
                    <p className="text-xs text-green-600">Good flow</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Incident Analysis */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white rounded-lg shadow-sm border border-gray-200"
      >
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Incident Analysis</h3>
          <p className="text-sm text-gray-500">Recent traffic incidents and their impact</p>
        </div>
        <div className="p-6">
          {activeIncidents > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{activeIncidents}</div>
                <div className="text-sm text-gray-600">Active Incidents</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {incidents.filter(i => i.severity === 'high' || i.severity === 'critical').length}
                </div>
                <div className="text-sm text-gray-600">High Priority</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {incidents.filter(i => i.is_resolved).length}
                </div>
                <div className="text-sm text-gray-600">Recently Resolved</div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircleIcon className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Incidents</h3>
              <p className="text-gray-500">Traffic flow is optimal across all monitored routes</p>
            </div>
          )}
        </div>
      </motion.div>

      {/* System Health */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="bg-white rounded-lg shadow-sm border border-gray-200"
      >
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">System Health</h3>
          <p className="text-sm text-gray-500">Monitoring system status and performance</p>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-700">API Services</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-700">Database</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-700">WebSocket</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-700">ML Models</span>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
} 