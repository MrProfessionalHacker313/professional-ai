'use client'

import { Suspense, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useSearchParams } from 'next/navigation'
import { setAuthCookies, scheduleProactiveRefresh } from '@/lib/api'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const PRIMARY_OWNER_EMAIL = (process.env.NEXT_PUBLIC_OWNER_EMAIL || 'redr28126@gmail.com').toLowerCase().trim()
const OWNER_EMAILS = [
  PRIMARY_OWNER_EMAIL,
  ...(process.env.NEXT_PUBLIC_OWNER_EMAILS || '')
    .split(',')
    .map((item) => item.toLowerCase().trim())
    .filter(Boolean),
]

function GoogleCallbackContent() {
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const error = searchParams.get('error')

    if (error) {
      console.error('OAuth error:', error)
      router.push('/login?error=oauth_failed')
      return
    }

    if (!code || !state) {
      router.push('/login?error=invalid_callback')
      return
    }

    fetch(`${API_BASE_URL}/api/auth/oauth/callback/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider: 'google', code, state, redirect_uri: window.location.origin + '/auth/callback/google' }),
    })
      .then((res) => {
        if (!res.ok) {
          return res.json().then((err) => { throw new Error(err?.detail || `HTTP ${res.status}`) })
        }
        return res.json()
      })
      .then((data) => {
        if (data.tokens) {
          setAuthCookies(data)
          scheduleProactiveRefresh()
          if (OWNER_EMAILS.includes(data.user?.email?.toLowerCase().trim())) {
            router.push('/admin')
          } else {
            router.push('/dashboard?passkey_setup=1')
          }
        } else {
          router.push('/login?error=oauth_failed')
        }
      })
      .catch((err) => {
        console.error('OAuth callback error:', err)
        router.push('/login?error=oauth_failed')
      })
  }, [router, searchParams])

  return (
    <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-400">Completing sign in...</p>
      </div>
    </div>
  )
}

export default function GoogleCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-400">Completing sign in...</p>
          </div>
        </div>
      }
    >
      <GoogleCallbackContent />
    </Suspense>
  )
}