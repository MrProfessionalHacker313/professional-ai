'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'

interface AnalyticsData {
  users_by_country: { country: string; count: number }[]
  top_features: { feature: string; count: number }[]
  media_generated_count: number
  code_prompts_count: number
}

export default function AdminAnalytics() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get('/api/admin/analytics')
      .then((res) => setData(res.data))
      .catch(() => setError('Failed to load analytics'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-sm text-slate-400">Loading analytics…</p>
  if (error) return <p className="text-sm text-red-400">{error}</p>
  if (!data) return null

  const stats = [
    { label: 'Media Generated', value: (data.media_generated_count || 0).toLocaleString() },
    { label: 'Code Prompts', value: (data.code_prompts_count || 0).toLocaleString() },
  ]

  return (
    <div>
      <h2 className="mb-4 text-xl font-bold text-white">Analytics</h2>
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {stats.map((s) => (
          <div key={s.label} className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-sm text-slate-400">{s.label}</p>
            <p className="mt-2 text-2xl font-bold text-white">{s.value}</p>
          </div>
        ))}
      </div>

      <h3 className="mb-3 text-lg font-semibold text-white">Users by Country</h3>
      <ul className="mb-6 space-y-2">
        {(data.users_by_country || []).map((row) => (
          <li
            key={row.country}
            className="flex justify-between rounded-lg border border-slate-800 bg-slate-900 px-4 py-2 text-sm"
          >
            <span className="text-slate-300">{row.country}</span>
             <span className="font-semibold text-white">{(row.count || 0).toLocaleString()}</span>
          </li>
        ))}
      </ul>

      <h3 className="mb-3 text-lg font-semibold text-white">Top Features Used</h3>
      <ul className="space-y-2">
        {(data.top_features || []).map((row) => (
          <li
            key={row.feature}
            className="flex justify-between rounded-lg border border-slate-800 bg-slate-900 px-4 py-2 text-sm"
          >
            <span className="text-slate-300">{row.feature}</span>
             <span className="font-semibold text-white">{(row.count || 0).toLocaleString()}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}