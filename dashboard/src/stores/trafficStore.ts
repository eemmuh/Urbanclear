import { create } from 'zustand'
import { trafficApi } from '../utils/api'
import { TrafficData, Incident, Route, DashboardStats } from '../types'

interface TrafficState {
  trafficData: TrafficData[]
  incidents: Incident[]
  routes: Route[]
  dashboardStats: DashboardStats | null
  isLoading: boolean
  error: string | null
  
  // Actions
  fetchTrafficData: () => Promise<void>
  fetchIncidents: () => Promise<void>
  fetchRoutes: () => Promise<void>
  fetchDashboardStats: () => Promise<void>
  updateTrafficData: (data: TrafficData[]) => void
  updateIncidents: (incidents: Incident[]) => void
  addIncident: (incident: Incident) => void
  addTrafficData: (data: TrafficData[]) => void
  setRoutes: (routes: Route[]) => void
  setDashboardStats: (stats: DashboardStats) => void
  resolveIncident: (id: string) => Promise<void>
  clearError: () => void
}

export const useTrafficStore = create<TrafficState>((set) => ({
  trafficData: [],
  incidents: [],
  routes: [],
  dashboardStats: null,
  isLoading: false,
  error: null,

  fetchTrafficData: async () => {
    try {
      set({ isLoading: true, error: null })
      const response = await trafficApi.getTrafficData()
      
      if (response.success && response.data) {
        set({ trafficData: response.data, isLoading: false })
      } else {
        set({ 
          error: response.message || 'Failed to fetch traffic data', 
          isLoading: false 
        })
      }
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch traffic data',
        isLoading: false 
      })
    }
  },

  fetchIncidents: async () => {
    try {
      set({ isLoading: true, error: null })
      const response = await trafficApi.getIncidents()
      
      if (response.success && response.data) {
        set({ incidents: response.data, isLoading: false })
      } else {
        set({ 
          error: response.message || 'Failed to fetch incidents', 
          isLoading: false 
        })
      }
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch incidents',
        isLoading: false 
      })
    }
  },

  fetchRoutes: async () => {
    try {
      set({ isLoading: true, error: null })
      // For now, we don't have a direct route endpoint, so we'll just clear loading
      set({ routes: [], isLoading: false })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch routes',
        isLoading: false 
      })
    }
  },

  fetchDashboardStats: async () => {
    try {
      set({ isLoading: true, error: null })
      const response = await trafficApi.getDashboardStats()
      
      if (response.success && response.data) {
        set({ dashboardStats: response.data, isLoading: false })
      } else {
        set({ 
          error: response.message || 'Failed to fetch dashboard stats', 
          isLoading: false 
        })
      }
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch dashboard stats',
        isLoading: false 
      })
    }
  },

  updateTrafficData: (data: TrafficData[]) => {
    set({ trafficData: data })
  },

  updateIncidents: (incidents: Incident[]) => {
    set({ incidents })
  },

  addIncident: (incident: Incident) => {
    set(state => ({ 
      incidents: [incident, ...state.incidents]
    }))
  },

  addTrafficData: (data: TrafficData[]) => {
    set({ trafficData: data })
  },

  setRoutes: (routes: Route[]) => {
    set({ routes })
  },

  setDashboardStats: (stats: DashboardStats) => {
    set({ dashboardStats: stats })
  },

  resolveIncident: async (id: string) => {
    try {
      const response = await trafficApi.updateIncident(id, { 
        is_resolved: true, 
        resolved_time: new Date().toISOString() 
      })
      
      if (response.success) {
        set(state => ({
          incidents: state.incidents.map(incident =>
            incident.id === id 
              ? { ...incident, is_resolved: true, resolved_time: new Date().toISOString() }
              : incident
          )
        }))
      } else {
        set({ error: response.message || 'Failed to resolve incident' })
      }
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to resolve incident'
      })
    }
  },

  clearError: () => {
    set({ error: null })
  }
})) 