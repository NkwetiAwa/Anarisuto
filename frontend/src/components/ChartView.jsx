import React from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

function buildChartJsData(payload) {
  const datasets = (payload.datasets || []).map((ds, idx) => ({
    label: ds.label,
    data: ds.data,
    borderColor: idx === 0 ? '#2563eb' : '#16a34a',
    backgroundColor: idx === 0 ? 'rgba(37, 99, 235, 0.25)' : 'rgba(22, 163, 74, 0.25)'
  }))

  return {
    labels: payload.labels || [],
    datasets
  }
}

export default function ChartView({ payload }) {
  if (!payload) return null
  if (!payload.labels?.length || !payload.datasets?.length) {
    return (
      <div>
        {payload.title ? <div className="chartTitle">{payload.title}</div> : null}
        <div className="empty">No data available.</div>
      </div>
    )
  }

  const data = buildChartJsData(payload)
  const options = {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
      title: { display: false }
    }
  }

  if (payload.chartType === 'bar') {
    return (
      <div>
        {payload.title ? <div className="chartTitle">{payload.title}</div> : null}
        <Bar data={data} options={options} />
      </div>
    )
  }
  return (
    <div>
      {payload.title ? <div className="chartTitle">{payload.title}</div> : null}
      <Line data={data} options={options} />
    </div>
  )
}
