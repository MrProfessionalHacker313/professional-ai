'use client'

import type { AdminTab } from './AdminShell'

const NAV_ITEMS: { key: AdminTab; label: string; icon: string }[] = [
  { key: 'overview', label: 'Overview', icon: '📊' },
  { key: 'users', label: 'Users', icon: '👥' },
  { key: 'revenue', label: 'Revenue', icon: '💰' },
  { key: 'plans', label: 'Plans', icon: '📦' },
  { key: 'vault', label: 'Vault', icon: '🔐' },
  { key: 'analytics', label: 'Analytics', icon: '📈' },
  { key: 'settings', label: 'Settings', icon: '⚙️' },
]

export default function AdminSidebar({
  active,
  onSelect,
  onUseAi,
}: {
  active: AdminTab
  onSelect: (tab: AdminTab) => void
  onUseAi: () => void
}) {
  return (
    <aside className="w-56 shrink-0 border-r border-slate-800 bg-slate-900 p-4">
      <h1 className="mb-6 text-lg font-bold text-white">Admin Panel</h1>
      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.key}
            onClick={() => onSelect(item.key)}
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-left text-sm transition ${
              active === item.key
                ? 'bg-indigo-600 text-white'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            <span>{item.icon}</span>
            {item.label}
          </button>
        ))}

        {/* Owner-only: Use AI toggle (side by side with Admin Panel) */}
        <div className="mt-6 border-t border-slate-800 pt-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">Owner Tools</p>
          <button
            onClick={onUseAi}
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-semibold text-indigo-300 transition hover:bg-indigo-500/10 hover:text-white"
          >
            <span>🤖</span>
            Use AI
          </button>
        </div>
      </nav>
    </aside>
  )
}