'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { authApi } from '@/lib/api'

const OWNER_EMAIL = (process.env.NEXT_PUBLIC_OWNER_EMAIL || 'redr28126@gmail.com').toLowerCase().trim()

export default function OwnerPage() {
  const router = useRouter()
  const [checking, setChecking] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true
    authApi
      .me()
      .then((res) => {
        const email = (res.data?.email || '').toLowerCase().trim()
        if (!mounted) return
        if (email !== OWNER_EMAIL) {
          setError('403 — Forbidden: Owner access required')
          setChecking(false)
          return
        }
        setChecking(false)
      })
      .catch(() => {
        if (mounted) router.replace('/login?redirect=/owner')
      })
    return () => {
      mounted = false
    }
  }, [router])

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-300">
        <p className="text-sm">Verifying owner access…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-slate-950 text-slate-300 p-6">
        <p className="text-7xl font-bold text-red-500/40 mb-4">403</p>
        <h1 className="text-2xl font-bold text-white mb-2">Forbidden</h1>
        <p className="text-slate-400">{error}</p>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-950 text-slate-200 p-6">
      <div className="w-full max-w-lg rounded-2xl border border-purple-500/40 bg-gradient-to-br from-purple-500/10 via-slate-900 to-pink-500/10 p-8">
        <div className="text-center mb-6">
          <p className="text-5xl mb-3">👑</p>
          <h1 className="text-2xl font-bold text-white">OWNER ACCESS</h1>
          <p className="text-sm text-slate-400 mt-2">Full platform owner privileges confirmed for {OWNER_EMAIL}</p>
        </div>
        <div className="space-y-3">
          <button
            onClick={() => router.push('/admin')}
            className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-700 px-4 py-3 text-sm font-bold text-white transition"
          >
            📊 Open Admin Dashboard
          </button>
          <button
            onClick={() => {
              document.cookie = `owner_ai_mode=1; path=/; SameSite=Strict`
              router.push('/chat?owner=1')
            }}
            className="w-full rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 px-4 py-3 text-sm font-bold text-white transition"
          >
            🤖 Use AI as Owner (Unlimited)
          </button>
          <button
            onClick={() => router.push('/dashboard')}
            className="w-full rounded-xl bg-slate-800 hover:bg-slate-700 px-4 py-3 text-sm font-semibold text-slate-300 transition"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  )
}