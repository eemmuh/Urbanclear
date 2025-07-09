export interface TrafficData {
  id: string
  location: {
    latitude: number
    longitude: number
    address?: string
  }
  timestamp: string
  speed_mph: number
  volume: number
  density: number
  severity: string
  congestion_level: number
  travel_time_index: number
}

export interface Incident {
  id: string
  type: 'road_closure' | 'accident' | 'construction' | 'weather' | 'congestion'
  location: {
    latitude: number
    longitude: number
    address?: string
  }
  severity: 'low' | 'medium' | 'high' | 'severe' | 'critical'
  description: string
  reported_time: string
  estimated_duration?: number
  lanes_affected?: number
  is_resolved: boolean
  resolved_time?: string | null
  impact_radius?: number
}

export interface Route {
  id: string
  start: {
    latitude: number
    longitude: number
  }
  end: {
    latitude: number
    longitude: number
  }
  distance_meters: number
  duration_seconds: number
  duration_with_traffic_seconds?: number
  traffic_level: 'light' | 'moderate' | 'heavy' | 'severe'
  alternative_routes?: Route[]
  waypoints?: Array<{
    latitude: number
    longitude: number
  }>
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  timestamp: string
}

export interface WebSocketMessage {
  type: 'traffic_update' | 'incident_alert' | 'route_update' | 'system_status'
  data: any
  timestamp: string
}

export interface DashboardStats {
  total_intersections: number
  active_incidents: number
  average_speed: number
  congestion_percentage: number
  system_health: 'healthy' | 'degraded' | 'critical'
  last_updated: string
}

export interface ChartDataPoint {
  x: string | number
  y: number
  label?: string
}

export interface MapMarker {
  id: string
  position: [number, number]
  type: 'traffic' | 'incident' | 'camera' | 'sensor'
  data: any
  popup?: string
} 