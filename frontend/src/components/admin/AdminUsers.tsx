'use client'

import { useEffect, useState, useCallback } from 'react'
import api from '@/lib/api'

interface AdminUser {
  id: string
  email: string
  display_name: string | null
  plan: string
  free_access_granted?: boolean
  is_approved: boolean
  is_banned: boolean
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export default function AdminUsers() {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busyId, setBusyId] = useState('')
  const [freeAccessSummary, setFreeAccessSummary] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    api
      .get('/api/admin/users')
      .then((res) => setUsers(res.data.users || []))
      .catch(() => setError('Failed to load users'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const act = async (id: string, action: 'approve' | 'disapprove' | 'ban' | 'grant-free-access' | 'revoke-free-access') => {
    setBusyId(id)
    setError('')
    setFreeAccessSummary('')
    try {
      const res = await api.post(`/api/admin/users/${id}/${action}`)
      if (action === 'grant-free-access' || action === 'revoke-free-access') {
        const used = res.data?.free_access_slots_used
        const total = res.data?.free_access_slots_total
        const remaining = res.data?.free_access_slots_remaining
        if (typeof used === 'number' && typeof total === 'number' && typeof remaining === 'number') {
          setFreeAccessSummary(`Free Access Seats: ${used}/${total} used (${remaining} remaining)`)
        }
      }
      load()
    } catch {
      setError(`Action ${action} failed`)
    } finally {
      setBusyId('')
    }
  }

  if (loading) return <p className="text-sm text-slate-400">Loading users…</p>
  if (error) return <p className="text-sm text-red-400">{error}</p>

  return (
    <div>
      <h2 className="mb-4 text-xl font-bold text-white">Users</h2>
      {freeAccessSummary ? <p className="mb-3 text-xs text-cyan-300">{freeAccessSummary}</p> : null}
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900 text-slate-400">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Plan</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Joined</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {users.map((u) => (
              <tr key={u.id} className="bg-slate-950">
                <td className="px-4 py-3">{u.display_name || '—'}</td>
                <td className="px-4 py-3">{u.email}</td>
                <td className="px-4 py-3 uppercase">{u.plan}</td>
                <td className="px-4 py-3">
                  {u.is_banned ? (
                    <span className="text-red-400">Banned</span>
                  ) : u.is_approved ? (
                    <span className="text-green-400">Approved</span>
                  ) : (
                    <span className="text-yellow-400">Pending</span>
                  )}
                </td>
                <td className="px-4 py-3">{new Date(u.created_at).toLocaleDateString()}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button
                      onClick={() => act(u.id, 'approve')}
                      disabled={busyId === u.id}
                      className="rounded bg-green-600 px-2 py-1 text-xs text-white disabled:opacity-50"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => act(u.id, 'disapprove')}
                      disabled={busyId === u.id}
                      className="rounded bg-yellow-600 px-2 py-1 text-xs text-white disabled:opacity-50"
                    >
                      Disapprove
                    </button>
                    <button
                      onClick={() => act(u.id, 'ban')}
                      disabled={busyId === u.id}
                      className="rounded bg-red-600 px-2 py-1 text-xs text-white disabled:opacity-50"
                    >
                      Ban
                    </button>
                    <button
                      onClick={() => act(u.id, u.free_access_granted ? 'revoke-free-access' : 'grant-free-access')}
                      disabled={busyId === u.id || u.is_admin}
                      className={`rounded px-2 py-1 text-xs text-white disabled:opacity-50 ${u.free_access_granted ? 'bg-slate-600' : 'bg-cyan-600'}`}
                      title={u.is_admin ? 'Admin users are already fully privileged' : 'Grant full free access'}
                    >
                      {u.free_access_granted ? 'Revoke Free Access' : 'Grant Free Access'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}