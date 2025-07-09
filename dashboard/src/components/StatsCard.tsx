import React from 'react'
import { motion } from 'framer-motion'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid'

interface StatsCardProps {
  title: string
  value: string
  icon: React.ComponentType<{ className?: string }>
  color: 'blue' | 'green' | 'yellow' | 'red' | 'gray'
  trend?: 'up' | 'down' | null
  subtitle?: string
  onClick?: () => void
}

const colorClasses = {
  blue: {
    icon: 'text-blue-600 bg-blue-100',
    border: 'border-blue-200',
    accent: 'text-blue-600'
  },
  green: {
    icon: 'text-green-600 bg-green-100',
    border: 'border-green-200',
    accent: 'text-green-600'
  },
  yellow: {
    icon: 'text-yellow-600 bg-yellow-100',
    border: 'border-yellow-200',
    accent: 'text-yellow-600'
  },
  red: {
    icon: 'text-red-600 bg-red-100',
    border: 'border-red-200',
    accent: 'text-red-600'
  },
  gray: {
    icon: 'text-gray-600 bg-gray-100',
    border: 'border-gray-200',
    accent: 'text-gray-600'
  }
}

export default function StatsCard({
  title,
  value,
  icon: Icon,
  color,
  trend,
  subtitle,
  onClick
}: StatsCardProps) {
  const colors = colorClasses[color]

  return (
    <motion.div
      whileHover={onClick ? { scale: 1.02 } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
      className={`card ${onClick ? 'cursor-pointer' : ''} ${colors.border}`}
      onClick={onClick}
    >
      <div className="card-content">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 truncate">{title}</p>
            <div className="flex items-center space-x-2 mt-1">
              <p className="text-2xl font-semibold text-gray-900">{value}</p>
              {trend && (
                <div className={`flex items-center ${
                  trend === 'up' 
                    ? 'text-green-600' 
                    : 'text-red-600'
                }`}>
                  {trend === 'up' ? (
                    <ArrowUpIcon className="h-4 w-4" />
                  ) : (
                    <ArrowDownIcon className="h-4 w-4" />
                  )}
                </div>
              )}
            </div>
            {subtitle && (
              <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
            )}
          </div>
          <div className={`rounded-lg p-3 ${colors.icon}`}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
      </div>
    </motion.div>
  )
} 