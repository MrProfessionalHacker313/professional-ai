'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import AdminSidebar from './AdminSidebar'
import AdminOverview from './AdminOverview'
import AdminUsers from './AdminUsers'
import AdminRevenue from './AdminRevenue'
import AdminPlans from './AdminPlans'
import AdminVault from './AdminVault'
import AdminAnalytics from './AdminAnalytics'
import AdminSettings from './AdminSettings'

export type AdminTab =
  | 'overview'
  | 'users'
  | 'revenue'
  | 'plans'
  | 'vault'
  | 'analytics'
  | 'settings'

export default function AdminShell() {
  const [tab, setTab] = useState<AdminTab>('overview')
  const router = useRouter()

  const handleUseAiAsOwner = () => {
    // Set the owner AI flag so the chat interface grants full unlimited access
    document.cookie = `owner_ai_mode=1; path=/; SameSite=Strict`
    router.push('/chat?owner=1')
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-200">
      <AdminSidebar active={tab} onSelect={setTab} onUseAi={handleUseAiAsOwner} />
      <main className="flex-1 overflow-y-auto p-6">
        {/* Use AI as Owner banner - one-click access to full AI power */}
        <div className="mb-6 rounded-2xl border border-indigo-500/40 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 p-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-white">⚡ OWNER AI MODE</h2>
              <p className="text-sm text-slate-300 mt-1">
                Open the full AI interface with <span className="font-semibold text-indigo-300">unlimited power</span> — chat, code, security, images, voice, and more. No limits, no credits.
              </p>
            </div>
            <button
              onClick={handleUseAiAsOwner}
              className="shrink-0 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-900/40 transition hover:from-indigo-500 hover:to-purple-500"
            >
              🤖 USE AI AS OWNER
            </button>
          </div>
        </div>

        {tab === 'overview' && <AdminOverview />}
        {tab === 'users' && <AdminUsers />}
        {tab === 'revenue' && <AdminRevenue />}
        {tab === 'plans' && <AdminPlans />}
        {tab === 'vault' && <AdminVault />}
        {tab === 'analytics' && <AdminAnalytics />}
        {tab === 'settings' && <AdminSettings />}
      </main>
    </div>
  )
}
