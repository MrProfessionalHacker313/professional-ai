'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import AdminShell from '@/components/admin/AdminShell'
import { authApi } from '@/lib/api'

const PRIMARY_OWNER_EMAIL = (process.env.NEXT_PUBLIC_OWNER_EMAIL || 'redr28126@gmail.com').toLowerCase().trim()
const OWNER_EMAILS = [
  PRIMARY_OWNER_EMAIL,
  ...(process.env.NEXT_PUBLIC_OWNER_EMAILS || '')
    .split(',')
    .map((item) => item.toLowerCase().trim())
    .filter(Boolean),
]

export default function AdminPage() {
  const router = useRouter()
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    let mounted = true
    authApi
      .me()
      .then((res) => {
        const email = (res.data?.email || '').toLowerCase().trim()
        if (!mounted) return
        if (!OWNER_EMAILS.includes(email)) {
          router.replace('/?error=403')
          return
        }
        setChecking(false)
      })
      .catch(() => {
        if (mounted) router.replace('/login?redirect=/admin')
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

  return <AdminShell />
}