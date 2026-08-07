'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'

interface Plan {
  name: string
  price_usd: number
}

const DEFAULT_PLANS: Plan[] = [
  { name: 'FREE', price_usd: 0 },
  { name: 'STARTER', price_usd: 9.99 },
  { name: 'PRO', price_usd: 19.99 },
  { name: 'PRO YEARLY', price_usd: 159.99 },
  { name: 'MAX', price_usd: 99.99 },
  { name: 'BUSINESS', price_usd: 24.99 },
]

export default function AdminPlans() {
  const [plans, setPlans] = useState<Plan[]>(DEFAULT_PLANS)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    api
      .get('/api/admin/plans')
      .then((res) => {
        if (res.data?.plans?.length) setPlans(res.data.plans)
      })
      .catch(() => setMessage('Failed to load plans'))
      .finally(() => setLoading(false))
  }, [])

  const update = (index: number, field: 'price_usd', value: number) => {
    setPlans((prev) => prev.map((p, i) => (i === index ? { ...p, [field]: value } : p)))
  }

  const save = async () => {
    setSaving(true)
    setMessage('')
    try {
      await api.put('/api/admin/plans', { plans })
      setMessage('Plans saved successfully')
    } catch {
      setMessage('Failed to save plans')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="text-sm text-slate-400">Loading plans…</p>

  return (
    <div>
      <h2 className="mb-4 text-xl font-bold text-white">Plans</h2>
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900 text-slate-400">
            <tr>
              <th className="px-4 py-3">Plan</th>
              <th className="px-4 py-3">Price (USD)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {plans.map((plan, i) => (
              <tr key={plan.name} className="bg-slate-950">
                <td className="px-4 py-3 font-semibold text-white">{plan.name}</td>
                <td className="px-4 py-3">
                  <input
                    type="number"
                    step="0.01"
                    value={plan.price_usd}
                    onChange={(e) => update(i, 'price_usd', Number(e.target.value))}
                    className="w-28 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-white"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center gap-4">
        <button
          onClick={save}
          disabled={saving}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save Plans'}
        </button>
        {message && <p className="text-sm text-slate-400">{message}</p>}
      </div>
    </div>
  )
}