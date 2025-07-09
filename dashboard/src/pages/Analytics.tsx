import { motion } from 'framer-motion'

export default function Analytics() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
      
      <div className="card">
        <div className="card-content">
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              📊
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Coming Soon</h3>
            <p className="text-gray-500">Advanced analytics and reporting features will be available here.</p>
          </div>
        </div>
      </div>
    </motion.div>
  )
} 