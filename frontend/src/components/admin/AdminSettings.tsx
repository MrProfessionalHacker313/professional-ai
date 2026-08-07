'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'

interface SettingsData {
  feature_toggles: Record<string, boolean>
  trial_days: number
  keys_status: { name: string; active: boolean }[]
}

const DEFAULT_TOGGLES: Record<string, boolean> = {
  chat: true,
  code: true,
  media: true,
  offline: true,
  payments: true,
}

export default function AdminSettings() {
  const [toggles, setToggles] = useState<Record<string, boolean>>(DEFAULT_TOGGLES)
  const [trialDays, setTrialDays] = useState(3)
  const [keysStatus, setKeysStatus] = useState<{ name: string; active: boolean }[]>([])
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    api
      .get('/api/admin/settings')
      .then((res) => {
        if (res.data?.feature_toggles) setToggles({ ...DEFAULT_TOGGLES, ...res.data.feature_toggles })
        if (res.data?.trial_days != null) setTrialDays(res.data.trial_days)
        if (res.data?.keys_status) setKeysStatus(res.data.keys_status)
      })
      .catch(() => setMessage('Failed to load settings'))
  }, [])

  const toggle = (key: string) => {
    setToggles((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const save = async () => {
    setSaving(true)
    setMessage('')
    try {
      await api.post('/api/admin/settings', { feature_toggles: toggles, trial_days: trialDays })
      setMessage('Settings saved successfully')
    } catch {
      setMessage('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <h2 className="mb-4 text-xl font-bold text-white">Settings</h2>

      <div className="mb-6 rounded-xl border border-slate-800 bg-slate-900 p-5">
        <h3 className="mb-3 text-lg font-semibold text-white">Feature Toggles</h3>
        <div className="space-y-3">
          {Object.entries(toggles).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between">
              <span className="text-sm capitalize text-slate-300">{key}</span>
              <button
                onClick={() => toggle(key)}
                className={`relative h-6 w-11 rounded-full transition ${
                  value ? 'bg-green-600' : 'bg-slate-700'
                }`}
              >
                <span
                  className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition ${
                    value ? 'left-5' : 'left-0.5'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="mb-6 rounded-xl border border-slate-800 bg-slate-900 p-5">
        <h3 className="mb-3 text-lg font-semibold text-white">Trial Days</h3>
        <input
          type="number"
          min={0}
          value={trialDays}
          onChange={(e) => setTrialDays(Number(e.target.value))}
          className="w-32 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-white"
        />
      </div>

      <div className="mb-6 rounded-xl border border-slate-800 bg-slate-900 p-5">
        <h3 className="mb-3 text-lg font-semibold text-white">API Keys Status</h3>
        <ul className="space-y-2">
          {keysStatus.map((k) => (
            <li key={k.name} className="flex items-center justify-between text-sm">
              <span className="text-slate-300">{k.name}</span>
              <span className={k.active ? 'text-green-400' : 'text-red-400'}>
                {k.active ? 'Active' : 'Inactive'}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={save}
          disabled={saving}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save Settings'}
        </button>
        {message && <p className="text-sm text-slate-400">{message}</p>}
      </div>
    </div>
  )
}