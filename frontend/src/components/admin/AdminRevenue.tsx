'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'

interface Transaction {
  id: string
  amount: number
  currency: string
  payment_method: string
  status: string
  created_at: string
}

interface RevenueData {
  total_revenue: number
  total_revenue_pkr: number
  total_transactions: number
  average_transaction: number
  mrr_estimate_usd: number
  mrr_estimate_pkr: number
  recent_transactions: Transaction[]
}

export default function AdminRevenue() {
  const [data, setData] = useState<RevenueData | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get('/api/admin/revenue')
      .then((res) => setData(res.data))
      .catch(() => setError('Failed to load revenue'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-sm text-slate-400">Loading revenue…</p>
  if (error) return <p className="text-sm text-red-400">{error}</p>
  if (!data) return null

  const cards = [
    { label: 'Total Revenue (USD)', value: `$${(data.total_revenue || 0).toLocaleString()}` },
    { label: 'Total Revenue (PKR)', value: `Rs ${(data.total_revenue_pkr || 0).toLocaleString()}` },
    { label: 'MRR (USD)', value: `$${(data.mrr_estimate_usd || 0).toLocaleString()}` },
    { label: 'MRR (PKR)', value: `Rs ${(data.mrr_estimate_pkr || 0).toLocaleString()}` },
    { label: 'Transactions', value: (data.total_transactions || 0).toLocaleString() },
    { label: 'Avg Transaction', value: `$${(data.average_transaction || 0).toLocaleString()}` },
  ]

  return (
    <div>
      <h2 className="mb-4 text-xl font-bold text-white">Revenue</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((card) => (
          <div key={card.label} className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-sm text-slate-400">{card.label}</p>
            <p className="mt-2 text-2xl font-bold text-white">{card.value}</p>
          </div>
        ))}
      </div>

      <h3 className="mb-3 mt-8 text-lg font-semibold text-white">Recent Transactions</h3>
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900 text-slate-400">
            <tr>
              <th className="px-4 py-3">Amount</th>
              <th className="px-4 py-3">Currency</th>
              <th className="px-4 py-3">Gateway</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {data.recent_transactions.map((t) => (
              <tr key={t.id} className="bg-slate-950">
                <td className="px-4 py-3">{(t.amount || 0).toLocaleString()}</td>
                <td className="px-4 py-3">{t.currency}</td>
                <td className="px-4 py-3 uppercase">{t.payment_method}</td>
                <td className="px-4 py-3">
                  <span
                    className={
                      t.status === 'completed'
                        ? 'text-green-400'
                        : t.status === 'refunded'
                          ? 'text-red-400'
                          : 'text-yellow-400'
                    }
                  >
                    {t.status}
                  </span>
                </td>
                <td className="px-4 py-3">{t.created_at ? new Date(t.created_at).toLocaleString() : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}