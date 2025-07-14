import axios from 'axios'
import { TrafficData, Incident, Route, DashboardStats, ApiResponse } from '../types'

const API_BASE_URL = 'http://localhost:8000' // Use direct API URL

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Response Error:', error)
    
    if (error.code === 'ECONNABORTED') {
      throw new Error('Request timeout - API is not responding')
    }
    
    if (error.response?.status === 500) {
      throw new Error('Internal server error')
    }
    
    if (error.response?.status === 404) {
      throw new Error('API endpoint not found')
    }
    
    throw error
  }
)

// Transform API traffic data to our expected format
const transformTrafficData = (apiData: any[]): TrafficData[] => {
  return apiData.map(item => ({
    id: item.id,
    timestamp: item.timestamp,
    location: {
      latitude: item.location.latitude,
      longitude: item.location.longitude,
      address: item.location.address
    },
    speed_mph: item.speed_mph,
    volume: item.volume,
    density: item.density,
    severity: item.severity,
    congestion_level: item.congestion_level,
    travel_time_index: item.travel_time_index
  }))
}

// Transform API incident data to our expected format
const transformIncidentData = (apiData: any[]): Incident[] => {
  return apiData.map(item => ({
    id: item.id,
    type: item.type,
    location: {
      latitude: item.location.latitude,
      longitude: item.location.longitude,
      address: item.location.address
    },
    severity: item.severity,
    description: item.description,
    reported_time: item.reported_time,
    estimated_duration: item.estimated_duration,
    lanes_affected: item.lanes_affected,
    is_resolved: item.is_resolved,
    resolved_time: item.resolved_time,
    impact_radius: item.impact_radius
  }))
}

export const trafficApi = {
  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    try {
      const response = await apiClient.get('/health')
      return {
        success: true,
        data: response.data,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      return {
        success: false,
        message: 'Health check failed',
        timestamp: new Date().toISOString()
      }
    }
  },

  // Traffic data endpoints
  async getTrafficData(): Promise<ApiResponse<TrafficData[]>> {
    try {
      const response = await apiClient.get('/api/v1/traffic/current')
      const transformedData = transformTrafficData(response.data)
      
      return {
        success: true,
        data: transformedData,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to fetch traffic data',
        timestamp: new Date().toISOString()
      }
    }
  },

  async getTrafficDataByLocation(lat: number, lon: number, radius: number = 5): Promise<ApiResponse<TrafficData[]>> {
    try {
      const response = await apiClient.get(`/api/v1/traffic/location`, {
        params: { latitude: lat, longitude: lon, radius_km: radius }
      })
      const transformedData = transformTrafficData(response.data)
      
      return {
        success: true,
        data: transformedData,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to fetch traffic data by location',
        timestamp: new Date().toISOString()
      }
    }
  },

  // Incident endpoints
  async getIncidents(): Promise<ApiResponse<Incident[]>> {
    try {
      const response = await apiClient.get('/api/v1/incidents/active')
      const transformedData = transformIncidentData(response.data)
      
      return {
        success: true,
        data: transformedData,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to fetch incidents',
        timestamp: new Date().toISOString()
      }
    }
  },

  async createIncident(incident: Omit<Incident, 'id' | 'reported_time'>): Promise<ApiResponse<Incident>> {
    try {
      const response = await apiClient.post('/api/v1/incidents/', incident)
      return {
        success: true,
        data: response.data,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to create incident',
        timestamp: new Date().toISOString()
      }
    }
  },

  async updateIncident(id: string, updates: Partial<Incident>): Promise<ApiResponse<Incident>> {
    try {
      const response = await apiClient.patch(`/api/v1/incidents/${id}`, updates)
      return {
        success: true,
        data: response.data,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to update incident',
        timestamp: new Date().toISOString()
      }
    }
  },

  // Route optimization endpoints
  async optimizeRoute(start: { lat: number; lon: number }, end: { lat: number; lon: number }): Promise<ApiResponse<Route>> {
    try {
      const response = await apiClient.post('/api/v1/routes/optimize', {
        start_latitude: start.lat,
        start_longitude: start.lon,
        end_latitude: end.lat,
        end_longitude: end.lon
      })
      return {
        success: true,
        data: response.data,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to optimize route',
        timestamp: new Date().toISOString()
      }
    }
  },

  // Dashboard stats
  async getDashboardStats(): Promise<ApiResponse<DashboardStats>> {
    try {
      const response = await apiClient.get('/api/v1/dashboard/stats')
      return {
        success: true,
        data: response.data,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      // Create mock stats if endpoint doesn't exist
      const mockStats: DashboardStats = {
        total_intersections: 8,
        active_incidents: 1,
        average_speed: 25.5,
        congestion_percentage: 15,
        system_health: 'healthy',
        last_updated: new Date().toISOString()
      }
      
      return {
        success: true,
        data: mockStats,
        message: 'Using mock data - dashboard stats endpoint not available',
        timestamp: new Date().toISOString()
      }
    }
  },

  // ML Predictions
  async getTrafficPrediction(location: { lat: number; lon: number }, hours: number = 1): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.post('/api/v1/predictions/traffic', {
        latitude: location.lat,
        longitude: location.lon,
        prediction_hours: hours
      })
      return {
        success: true,
        data: response.data,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to get traffic prediction',
        timestamp: new Date().toISOString()
      }
    }
  },

  // Real data services
  async geocodeAddress(address: string): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.post('/api/v1/real-data/geocode', null, {
        params: { address }
      })
      return {
        success: true,
        data: response.data,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to geocode address',
        timestamp: new Date().toISOString()
      }
    }
  },

  async findPlaces(query: string, lat: number, lon: number, radius: number = 5): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.get('/api/v1/real-data/places/search', {
        params: {
          query,
          latitude: lat,
          longitude: lon,
          radius_km: radius,
          limit: 20
        }
      })
      return {
        success: true,
        data: response.data,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to search places',
        timestamp: new Date().toISOString()
      }
    }
  }
}

export default apiClient 