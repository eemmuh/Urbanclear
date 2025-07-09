import { useEffect } from 'react'
import { MapContainer, TileLayer, CircleMarker, Marker, Popup, useMap } from 'react-leaflet'
import { LatLngBounds } from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { TrafficData, Incident } from '../../types'

// Fix leaflet default marker issue
import L from 'leaflet'
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

interface RealtimeMapProps {
  trafficData: TrafficData[]
  incidents: Incident[]
  center?: [number, number]
  zoom?: number
  height?: number
}

// Component to fit map to data bounds
function MapUpdater({ trafficData, incidents }: { trafficData: TrafficData[], incidents: Incident[] }) {
  const map = useMap()

  useEffect(() => {
    if (trafficData.length > 0 || incidents.length > 0) {
      const bounds = new LatLngBounds([])
      
      // Add traffic data points to bounds
      trafficData.forEach(data => {
        bounds.extend([data.location.latitude, data.location.longitude])
      })
      
      // Add incident points to bounds
      incidents.forEach(incident => {
        bounds.extend([incident.location.latitude, incident.location.longitude])
      })
      
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [20, 20] })
      }
    }
  }, [map, trafficData, incidents])

  return null
}

export default function RealtimeMap({ 
  trafficData, 
  incidents, 
  center = [40.7831, -73.9712], // NYC default
  zoom = 13,
  height = 400 
}: RealtimeMapProps) {
  // Get circle color based on congestion level
  const getCircleColor = (congestionLevel: number) => {
    if (congestionLevel > 0.7) return '#EF4444' // Red
    if (congestionLevel > 0.4) return '#F59E0B' // Orange
    if (congestionLevel > 0.2) return '#EAB308' // Yellow
    return '#10B981' // Green
  }

  // Get circle size based on volume
  const getCircleSize = (volume: number) => {
    const minSize = 8
    const maxSize = 25
    const minVolume = 0
    const maxVolume = 1000
    
    const normalizedVolume = Math.max(0, Math.min(1, (volume - minVolume) / (maxVolume - minVolume)))
    return minSize + (maxSize - minSize) * normalizedVolume
  }

  // Get incident color based on severity
  const getIncidentColor = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'severe':
        return '#EF4444' // Red
      case 'high':
        return '#F59E0B' // Orange
      case 'medium':
        return '#EAB308' // Yellow
      case 'low':
        return '#10B981' // Green
      default:
        return '#6B7280' // Gray
    }
  }

  return (
    <div style={{ height: `${height}px` }} className="rounded-lg overflow-hidden border border-gray-200">
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
        scrollWheelZoom={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        
        <MapUpdater trafficData={trafficData} incidents={incidents} />
        
        {/* Traffic Data Points */}
        {trafficData.map((data) => (
          <CircleMarker
            key={data.id}
            center={[data.location.latitude, data.location.longitude]}
            radius={getCircleSize(data.volume)}
            color={getCircleColor(data.congestion_level)}
            fillColor={getCircleColor(data.congestion_level)}
            fillOpacity={0.6}
            weight={2}
          >
            <Popup>
              <div className="p-2">
                <h4 className="font-medium text-gray-900 mb-2">
                  {data.location.address || 'Traffic Sensor'}
                </h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Speed:</span>
                    <span className="font-medium">{data.speed_mph} mph</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Volume:</span>
                    <span className="font-medium">{data.volume} vehicles</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Congestion:</span>
                    <span className="font-medium">{(data.congestion_level * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Density:</span>
                    <span className="font-medium">{data.density}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    Updated: {new Date(data.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
        
        {/* Incident Markers */}
        {incidents.map((incident) => (
          <Marker
            key={incident.id}
            position={[incident.location.latitude, incident.location.longitude]}
          >
            <Popup>
              <div className="p-2">
                <div className="flex items-center space-x-2 mb-2">
                  <span 
                    className="inline-flex px-2 py-1 text-xs font-medium rounded text-white"
                    style={{ backgroundColor: getIncidentColor(incident.severity) }}
                  >
                    {incident.severity}
                  </span>
                  <span className="text-xs text-gray-500 capitalize">
                    {incident.type.replace('_', ' ')}
                  </span>
                </div>
                <h4 className="font-medium text-gray-900 mb-2">
                  {incident.description}
                </h4>
                <div className="space-y-1 text-sm">
                  <div className="text-gray-600">
                    📍 {incident.location.address || 'Unknown location'}
                  </div>
                  {incident.estimated_duration && (
                    <div className="text-gray-600">
                      ⏱️ Duration: {incident.estimated_duration} min
                    </div>
                  )}
                  {incident.lanes_affected && (
                    <div className="text-gray-600">
                      🛣️ Lanes: {incident.lanes_affected}
                    </div>
                  )}
                  <div className="text-xs text-gray-500 mt-2">
                    Reported: {new Date(incident.reported_time).toLocaleString()}
                  </div>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
} 