'use client'

import { useState } from 'react'
import api from '@/lib/api'

interface VaultEntry {
  id: string
  project_name: string
  encrypted: boolean
  version: string
  created_at: string
  updated_at: string
  note: string
}

export default function AdminVault() {
  const [email, setEmail] = useState('')
  const [entries, setEntries] = useState<VaultEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const search = async () => {
    if (!email.trim()) return
    setLoading(true)
    setMessage('')
    setEntries([])
    try {
      const res = await api.get(`/api/admin/vault/${encodeURIComponent(email.trim())}`)
      setEntries(res.data.vault_entries || [])
      if (!res.data.vault_entries?.length) setMessage('No vault entries found for this user')
    } catch {
      setMessage('Failed to load vault (action is logged)')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2 className="mb-4 text-xl font-bold text-white">Vault</h2>
      <p className="mb-4 text-sm text-slate-400">
        Search a user's saved projects. Data is decrypted server-side for the owner only. This
        action is audited.
      </p>
      <div className="mb-4 flex gap-2">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="user@email.com"
          className="w-72 rounded border border-slate-700 bg-slate-900 px-3 py-2 text-white"
        />
        <button
          onClick={search}
          disabled={loading}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
        >
          {loading ? 'Searching…' : 'Search'}
        </button>
      </div>
      {message && <p className="mb-4 text-sm text-slate-400">{message}</p>}
      {entries.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900 text-slate-400">
              <tr>
                <th className="px-4 py-3">Project</th>
                <th className="px-4 py-3">Encrypted</th>
                <th className="px-4 py-3">Version</th>
                <th className="px-4 py-3">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {entries.map((e) => (
                <tr key={e.id} className="bg-slate-950">
                  <td className="px-4 py-3 font-semibold text-white">{e.project_name}</td>
                  <td className="px-4 py-3">{e.encrypted ? 'Yes' : 'No'}</td>
                  <td className="px-4 py-3">{e.version}</td>
                  <td className="px-4 py-3">{e.updated_at ? new Date(e.updated_at).toLocaleString() : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}