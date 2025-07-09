import { useEffect } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import 'chartjs-adapter-date-fns'
import { TrafficData } from '../../types'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
)

interface TrafficChartProps {
  data: TrafficData[]
  height?: number
}

export default function TrafficChart({ data, height = 400 }: TrafficChartProps) {
  // Transform data for chart
  const chartData = {
    labels: data.map(d => new Date(d.timestamp)),
    datasets: [
      {
        label: 'Speed (mph)',
        data: data.map(d => ({
          x: new Date(d.timestamp),
          y: d.speed_mph
        })),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.1,
      },
      {
        label: 'Volume',
        data: data.map(d => ({
          x: new Date(d.timestamp),
          y: d.volume
        })),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.1,
        yAxisID: 'y1',
      },
      {
        label: 'Congestion Level',
        data: data.map(d => ({
          x: new Date(d.timestamp),
          y: d.congestion_level * 100 // Convert to percentage
        })),
        borderColor: 'rgb(245, 101, 101)',
        backgroundColor: 'rgba(245, 101, 101, 0.1)',
        tension: 0.1,
        yAxisID: 'y2',
      }
    ]
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Real-time Traffic Metrics',
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          displayFormats: {
            minute: 'HH:mm',
            hour: 'HH:mm'
          }
        },
        title: {
          display: true,
          text: 'Time'
        }
      },
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Speed (mph)'
        }
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        title: {
          display: true,
          text: 'Volume'
        },
        grid: {
          drawOnChartArea: false,
        },
      },
      y2: {
        type: 'linear' as const,
        display: false,
        min: 0,
        max: 100,
      }
    },
  }

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="text-gray-400 mb-2">📈</div>
          <p className="text-gray-500">No traffic data available</p>
        </div>
      </div>
    )
  }

  return (
    <div style={{ height: `${height}px` }}>
      <Line data={chartData} options={options} />
    </div>
  )
} 