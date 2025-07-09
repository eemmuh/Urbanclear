import { create } from 'zustand'
import { io, Socket } from 'socket.io-client'
import { WebSocketMessage } from '../types'
import { useTrafficStore } from './trafficStore'
import toast from 'react-hot-toast'

interface WebSocketStore {
  socket: Socket | null
  isConnected: boolean
  connectionError: string | null
  retryCount: number
  maxRetries: number

  connect: () => void
  disconnect: () => void
  reconnect: () => void
  setConnectionStatus: (connected: boolean) => void
  setConnectionError: (error: string | null) => void
  resetRetryCount: () => void
}

export const useWebSocketStore = create<WebSocketStore>((set, get) => ({
  socket: null,
  isConnected: false,
  connectionError: null,
  retryCount: 0,
  maxRetries: 5,

  connect: () => {
    const socket = io('ws://localhost:8000', {
      transports: ['websocket'],
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 2000,
      timeout: 10000,
    })

    socket.on('connect', () => {
      console.log('WebSocket connected')
      set({ isConnected: true, connectionError: null })
      get().resetRetryCount()
      toast.success('Connected to real-time data feed')
    })

    socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason)
      set({ isConnected: false })
      
      if (reason === 'io server disconnect') {
        // Server initiated disconnect, try to reconnect
        setTimeout(() => {
          if (get().retryCount < get().maxRetries) {
            get().reconnect()
          }
        }, 2000)
      }
    })

    socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error)
      set({ 
        connectionError: error.message,
        isConnected: false 
      })
      
      const retryCount = get().retryCount + 1
      set({ retryCount })
      
      if (retryCount >= get().maxRetries) {
        toast.error('Unable to connect to real-time data feed')
      }
    })

    // Handle traffic data updates
    socket.on('traffic_update', (message: WebSocketMessage) => {
      if (message.type === 'traffic_update' && message.data) {
        const trafficStore = useTrafficStore.getState()
        trafficStore.addTrafficData(message.data)
      }
    })

    // Handle incident alerts
    socket.on('incident_alert', (message: WebSocketMessage) => {
      if (message.type === 'incident_alert' && message.data) {
        const trafficStore = useTrafficStore.getState()
        trafficStore.addIncident(message.data)
        
        // Show toast notification for new incidents
        toast.error(`New incident: ${message.data.type} at ${message.data.location.address || 'Unknown location'}`, {
          duration: 6000,
        })
      }
    })

    // Handle route updates
    socket.on('route_update', (message: WebSocketMessage) => {
      if (message.type === 'route_update' && message.data) {
        const trafficStore = useTrafficStore.getState()
        trafficStore.setRoutes(message.data)
      }
    })

    // Handle system status updates
    socket.on('system_status', (message: WebSocketMessage) => {
      if (message.type === 'system_status' && message.data) {
        const trafficStore = useTrafficStore.getState()
        trafficStore.setDashboardStats(message.data)
      }
    })

    set({ socket })
  },

  disconnect: () => {
    const { socket } = get()
    if (socket) {
      socket.disconnect()
      set({ socket: null, isConnected: false })
    }
  },

  reconnect: () => {
    const { socket } = get()
    if (socket) {
      socket.connect()
    } else {
      get().connect()
    }
  },

  setConnectionStatus: (connected) => {
    set({ isConnected: connected })
  },

  setConnectionError: (error) => {
    set({ connectionError: error })
  },

  resetRetryCount: () => {
    set({ retryCount: 0 })
  },
})) 