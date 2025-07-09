import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  MapIcon,
  AdjustmentsHorizontalIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline'
import { useTrafficStore } from '../stores/trafficStore'
import { useWebSocketStore } from '../stores/websocketStore'
import RealtimeMap from '../components/maps/RealtimeMap'
import TrafficChart from '../components/charts/TrafficChart'

export default function Traffic() {
  const { 
    trafficData, 
    incidents, 
    isLoading, 
    error, 
    fetchTrafficData,
    fetchIncidents 
  } = useTrafficStore()
  
  const { isConnected } = useWebSocketStore()
  
  // Map display settings
  const [showTrafficData, setShowTrafficData] = useState(true)
  const [showIncidents, setShowIncidents] = useState(true)
  const [selectedMetric, setSelectedMetric] = useState<'speed' | 'volume' | 'congestion'>('speed')
  const [searchLocation, setSearchLocation] = useState('')

  useEffect(() => {
    // Fetch initial data
    const loadData = async () => {
      await Promise.all([
        fetchTrafficData(),
        fetchIncidents()
      ])
    }

    loadData()

    // Set up periodic refresh
    const interval = setInterval(() => {
      if (!isConnected) {
        loadData()
      }
    }, 30000)

    return () => clearInterval(interval)
  }, [isConnected, fetchTrafficData, fetchIncidents])

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error Loading Traffic Data</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  // Filter traffic data based on search
  const filteredTrafficData = trafficData.filter(data =>
    !searchLocation || 
    data.location.address?.toLowerCase().includes(searchLocation.toLowerCase()) ||
    data.id.toLowerCase().includes(searchLocation.toLowerCase())
  )

  // Get stats for current view
  const avgSpeed = filteredTrafficData.length > 0 
    ? filteredTrafficData.reduce((sum, data) => sum + data.speed_mph, 0) / filteredTrafficData.length 
    : 0
  
  const avgVolume = filteredTrafficData.length > 0 
    ? filteredTrafficData.reduce((sum, data) => sum + data.volume, 0) / filteredTrafficData.length 
    : 0

  const avgCongestion = filteredTrafficData.length > 0 
    ? filteredTrafficData.reduce((sum, data) => sum + data.congestion_level, 0) / filteredTrafficData.length 
    : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <MapIcon className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Interactive Traffic Map</h1>
            <p className="text-gray-600">Real-time traffic monitoring and visualization</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
          <span className="text-sm text-gray-500">
            {isConnected ? 'Live Updates' : 'Static View'} • {filteredTrafficData.length} sensors
          </span>
        </div>
      </div>

      {/* Controls and Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Map Controls */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <AdjustmentsHorizontalIcon className="h-5 w-5 mr-2" />
              Map Controls
            </h3>
            
            {/* Search */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Location
              </label>
              <div className="relative">
                <MagnifyingGlassIcon className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search sensors..."
                  value={searchLocation}
                  onChange={(e) => setSearchLocation(e.target.value)}
                  className="pl-9 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Display Options */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Display Options
              </label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={showTrafficData}
                    onChange={(e) => setShowTrafficData(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Traffic Sensors</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={showIncidents}
                    onChange={(e) => setShowIncidents(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Incidents</span>
                </label>
              </div>
            </div>

            {/* Metric Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Primary Metric
              </label>
              <select
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="speed">Speed (mph)</option>
                <option value="volume">Volume (vehicles)</option>
                <option value="congestion">Congestion Level</option>
              </select>
            </div>

            {/* Current Stats */}
            <div className="border-t pt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Current Averages</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Speed:</span>
                  <span className="font-medium">{avgSpeed.toFixed(1)} mph</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Volume:</span>
                  <span className="font-medium">{Math.round(avgVolume)} vehicles</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Congestion:</span>
                  <span className="font-medium">{(avgCongestion * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Incidents:</span>
                  <span className="font-medium">{incidents.length} active</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Map */}
        <div className="lg:col-span-3">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-lg shadow-sm border border-gray-200"
          >
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Live Traffic Map</h3>
                <div className="flex items-center space-x-2">
                  {isLoading && (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  )}
                  <span className="text-sm text-gray-500">
                    {new Date().toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
            <div className="p-6">
              <RealtimeMap
                trafficData={showTrafficData ? filteredTrafficData : []}
                incidents={showIncidents ? incidents : []}
                height={600}
              />
            </div>
          </motion.div>
        </div>
      </div>

      {/* Traffic Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-lg shadow-sm border border-gray-200"
      >
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Traffic Trends</h3>
          <p className="text-sm text-gray-500">Real-time metrics across all sensors</p>
        </div>
        <div className="p-6">
          <TrafficChart data={filteredTrafficData} height={300} />
        </div>
      </motion.div>

      {/* Legend */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Map Legend</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span className="text-sm text-gray-700">Low Congestion (0-20%)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
            <span className="text-sm text-gray-700">Medium Congestion (20-40%)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-orange-500"></div>
            <span className="text-sm text-gray-700">High Congestion (40-70%)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-red-500"></div>
            <span className="text-sm text-gray-700">Severe Congestion (70%+)</span>
          </div>
        </div>
        <div className="mt-4 pt-4 border-t">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-blue-600 rounded-full flex items-center justify-center">
                <MapIcon className="w-2 h-2 text-white" />
              </div>
              <span className="text-sm text-gray-700">Traffic Sensor (size = volume)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-red-600 rounded-sm"></div>
              <span className="text-sm text-gray-700">Active Incident</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 