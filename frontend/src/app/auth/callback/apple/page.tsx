'use client'

import { Suspense, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function AppleCallbackContent() {
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const error = searchParams.get('error')

    if (error) {
      router.push('/login?error=oauth_failed')
      return
    }

    if (!code || !state) {
      router.push('/login?error=invalid_callback')
      return
    }

    fetch(`${API_BASE_URL}/api/auth/oauth/callback/apple`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider: 'apple', code, state, redirect_uri: window.location.origin + '/auth/callback/apple' }),
    })
      .then(res => res.json())
      .then(data => {
        if (data.tokens) {
          document.cookie = `access_token=${data.tokens.access_token}; path=/; SameSite=Strict`
          document.cookie = `user_email=${encodeURIComponent(data.user.email)}; path=/; SameSite=Strict`
          if (data.tokens.csrf_token) {
            document.cookie = `csrf_token=${encodeURIComponent(data.tokens.csrf_token)}; path=/; SameSite=Strict`
          }
          router.push('/dashboard?passkey_setup=1')
        } else {
          router.push('/login?error=oauth_failed')
        }
      })
      .catch(() => {
        router.push('/login?error=oauth_failed')
      })
  }, [router, searchParams])

  return (
    <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-gray-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-400">Completing Apple sign in...</p>
      </div>
    </div>
  )
}

export default function AppleCallbackPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-950 text-white flex items-center justify-center"><div className="text-center"><div className="w-12 h-12 border-4 border-gray-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" /><p className="text-gray-400">Completing Apple sign in...</p></div></div>}>
      <AppleCallbackContent />
    </Suspense>
  )
}