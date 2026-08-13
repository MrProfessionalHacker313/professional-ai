'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'

interface OverviewData {
  total_users: number
  active_subscribers: number
  revenue_usd: number
  revenue_pkr: number
  media_jobs_today: number
}

export default function AdminOverview() {
  const [data, setData] = useState<OverviewData | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get('/api/admin/overview')
      .then((res) => setData(res.data))
      .catch(() => setError('Failed to load overview'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-sm text-slate-400">Loading overview…</p>
  if (error) return <p className="text-sm text-red-400">{error}</p>
  if (!data) return null

  const cards = [
    { label: 'Total Users', value: (data.total_users || 0).toLocaleString() },
    { label: 'Active Subscribers', value: (data.active_subscribers || 0).toLocaleString() },
    { label: 'Revenue (USD)', value: `$${(data.revenue_usd || 0).toLocaleString()}` },
    { label: 'Revenue (PKR)', value: `Rs ${(data.revenue_pkr || 0).toLocaleString()}` },
    { label: 'Media Jobs Today', value: (data.media_jobs_today || 0).toLocaleString() },
  ]

  return (
    <div>
      <h2 className="mb-4 text-xl font-bold text-white">Overview</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((card) => (
          <div key={card.label} className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-sm text-slate-400">{card.label}</p>
            <p className="mt-2 text-2xl font-bold text-white">{card.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}