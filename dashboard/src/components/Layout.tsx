import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Bars3Icon,
  XMarkIcon,
  SignalIcon,
  SignalSlashIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  MapIcon,
  CogIcon,
  HomeIcon,
} from '@heroicons/react/24/outline'
import { useWebSocketStore } from '../stores/websocketStore'
import { useTrafficStore } from '../stores/trafficStore'

interface LayoutProps {
  children: React.ReactNode
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Traffic Map', href: '/traffic', icon: MapIcon },
  { name: 'Incidents', href: '/incidents', icon: ExclamationTriangleIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Settings', href: '/settings', icon: CogIcon },
]

export default function Layout({ children }: LayoutProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()
  const { isConnected } = useWebSocketStore()
  const { isLoading, error } = useTrafficStore()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile menu */}
      <div className={`fixed inset-0 z-50 lg:hidden ${mobileMenuOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setMobileMenuOpen(false)} />
        <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-xl">
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Urbanclear</h2>
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
          <nav className="mt-6">
            <div className="space-y-2 px-4">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                    location.pathname === item.href
                      ? 'bg-primary-50 text-primary-600'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <item.icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              ))}
            </div>
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex min-h-0 flex-1 flex-col border-r border-gray-200 bg-white">
          <div className="flex flex-1 flex-col overflow-y-auto pt-5 pb-4">
            <div className="flex items-center flex-shrink-0 px-4">
              <h1 className="text-xl font-bold text-gray-900">Urbanclear</h1>
              <div className="ml-auto flex items-center space-x-2">
                {isConnected ? (
                  <SignalIcon className="h-5 w-5 text-green-500" title="Connected" />
                ) : (
                  <SignalSlashIcon className="h-5 w-5 text-red-500" title="Disconnected" />
                )}
                {isLoading && (
                  <div className="w-4 h-4 border-2 border-gray-300 border-t-primary-600 rounded-full animate-spin" />
                )}
              </div>
            </div>
            <nav className="mt-8 flex-1 space-y-2 px-4">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                    location.pathname === item.href
                      ? 'bg-primary-50 text-primary-600'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <item.icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-10 flex h-16 flex-shrink-0 border-b border-gray-200 bg-white shadow-sm">
          <button
            type="button"
            className="border-r border-gray-200 px-4 text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 lg:hidden"
            onClick={() => setMobileMenuOpen(true)}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
          <div className="flex flex-1 justify-between px-4 sm:px-6">
            <div className="flex items-center">
              <h2 className="text-lg font-medium text-gray-900">
                {navigation.find(item => item.href === location.pathname)?.name || 'Dashboard'}
              </h2>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-500">
                  {isConnected ? 'Live' : 'Offline'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Error banner */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Page content */}
        <main className="flex-1">
          <div className="py-6">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                {children}
              </motion.div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
} 