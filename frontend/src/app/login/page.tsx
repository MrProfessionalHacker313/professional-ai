'use client'

import React, { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import toast from 'react-hot-toast'
import { authApi, scheduleProactiveRefresh } from '@/lib/api'
import { offlineAuth } from '@/lib/offline-auth'
import { useConnectivity } from '@/lib/use-connectivity'


const PRIMARY_OWNER_EMAIL = (process.env.NEXT_PUBLIC_OWNER_EMAIL || 'redr28126@gmail.com').toLowerCase().trim()
const OWNER_EMAILS = [
  PRIMARY_OWNER_EMAIL,
  ...(process.env.NEXT_PUBLIC_OWNER_EMAILS || '')
    .split(',')
    .map((item) => item.toLowerCase().trim())
    .filter(Boolean),
]

async function saveOfflineSession(data: any) {
  try {
    await offlineAuth.saveSession({
      email: data.user?.email || '',
      displayName: data.user?.display_name || data.user?.email?.split('@')[0] || 'User',
      token: data.tokens?.access_token || '',
      isOwner: false,
    })
  } catch (e) {
    console.error('[OfflineAuth] Failed to save offline session:', e)
  }
}

function setAuthCookies(data: any) {
  if (typeof window === 'undefined') return
  // Save offline session for future offline logins
  saveOfflineSession(data)
  const secure = window.location.protocol === 'https:' ? '; Secure' : ''
  const cookieOpts = `path=/; SameSite=Strict${secure}`
  document.cookie = `access_token=${data.tokens.access_token}; ${cookieOpts}`
  document.cookie = `user_email=${encodeURIComponent(data.user.email)}; ${cookieOpts}`
  if (OWNER_EMAILS.includes(data.user.email.toLowerCase().trim())) {
    document.cookie = `owner_email=${encodeURIComponent(data.user.email)}; ${cookieOpts}`
  }
  if (data.tokens.csrf_token) {
    document.cookie = `csrf_token=${encodeURIComponent(data.tokens.csrf_token)}; ${cookieOpts}`
  }
  if (data.tokens.refresh_token) {
    document.cookie = `refresh_token=${encodeURIComponent(data.tokens.refresh_token)}; ${cookieOpts}`
  }
}

function isOwnerEmail(email: string): boolean {
  return OWNER_EMAILS.includes((email || '').toLowerCase().trim())
}

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const redirect = searchParams.get('redirect') || '/dashboard'
  const { isOnline } = useConnectivity()
  const [offlineSession, setOfflineSession] = useState<any>(null)
  const [offlineLoginLoading, setOfflineLoginLoading] = useState(false)
  const [hasOfflineProfile, setHasOfflineProfile] = useState(false)

  useEffect(() => {
    offlineAuth.hasOfflineProfile().then(setHasOfflineProfile)
    offlineAuth.getSession().then(setOfflineSession)
  }, [])

  const handleOfflineLogin = async () => {
    setOfflineLoginLoading(true)
    try {
      let session = await offlineAuth.offlineSessionLogin()
      if (!session) {
        const passkeySession = await offlineAuth.offlinePasskeyLogin()
        if (!passkeySession) {
          toast.error('No offline session found. Login online once first.')
          return
        }
        session = passkeySession
        toast.success('Logged in with passkey! 📴')
      } else {
        toast.success('Offline session restored! 📴')
      }
      if (!session) return
      document.cookie = `access_token=${session.token}; path=/; SameSite=Strict`
      document.cookie = `user_email=${encodeURIComponent(session.email)}; path=/; SameSite=Strict`
      router.push(redirect)
    } catch (err: any) {
      toast.error(err?.message || 'Offline login failed')
    } finally {
      setOfflineLoginLoading(false)
    }
  }

  // ===== FLOW A: OWNER (email only) =====
  const [ownerEmail, setOwnerEmail] = useState('')
  const [ownerLoading, setOwnerLoading] = useState(false)

  // ===== FLOW B: REGULAR USERS =====
  const [showSignup, setShowSignup] = useState(false)
  const [signupName, setSignupName] = useState('')
  const [signupEmail, setSignupEmail] = useState('')
  const [signupPassword, setSignupPassword] = useState('')
  const [signupLoading, setSignupLoading] = useState(false)

  const [socialLoading, setSocialLoading] = useState<string | null>(null)

  // ===== FLOW A: Owner email-only login =====
  const handleOwnerLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!ownerEmail) {
      toast.error('Please enter your email')
      return
    }
    setOwnerLoading(true)
    try {
      const res = await authApi.ownerEmailLogin(ownerEmail)
      setAuthCookies(res.data)
      scheduleProactiveRefresh()
      toast.success('👑 OWNER ACCESS GRANTED')
      router.push('/admin')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Owner login failed')
    } finally {
      setOwnerLoading(false)
    }
  }

  // ===== FLOW B: Social sign-in =====
  const startOAuth = async (provider: 'google') => {
    setSocialLoading(provider)
    try {
      const res = await authApi.oauthLogin(provider)
      const oauthUrl = res.data?.oauth_url
      if (!oauthUrl) throw new Error('OAuth URL not available')
      window.location.href = oauthUrl
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || `Failed to start ${provider} sign-in`)
      setSocialLoading(null)
    }
  }

  // ===== FLOW B: Signup =====
  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    if (signupPassword.length < 6) {
      toast.error('Password must be at least 6 characters')
      return
    }
    setSignupLoading(true)
    try {
      const res = await authApi.register({
        email: signupEmail,
        password: signupPassword,
        display_name: signupName || undefined,
      })
      setAuthCookies(res.data)
      scheduleProactiveRefresh()
      toast.success('Account created! 🎉')
      router.push('/dashboard?passkey_setup=1')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Signup failed')
    } finally {
      setSignupLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white">Professional AI</h1>
            <p className="text-slate-400 mt-2">Sign in to your account</p>
          </div>

          {/* ============ FLOW A: OWNER ACCESS (email only) ============ */}
          <div className="mb-8 rounded-xl border border-purple-500/40 bg-gradient-to-r from-purple-500/10 to-pink-500/10 p-4">
            <p className="text-sm font-semibold text-purple-300 mb-3">👑 OWNER ACCESS — Enter your email</p>
            <form onSubmit={handleOwnerLogin} className="space-y-3">
              <input
                type="email"
                value={ownerEmail}
                onChange={(e) => setOwnerEmail(e.target.value)}
                placeholder="Owner email"
                className="w-full px-4 py-3 bg-slate-800 border border-purple-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                required
                autoFocus
              />
              {isOwnerEmail(ownerEmail) && (
                <p className="text-xs text-amber-400 text-center">Owner email detected. One click → full admin access.</p>
              )}
              <button
                type="submit"
                disabled={ownerLoading || !ownerEmail}
                className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 text-white font-bold rounded-lg transition"
              >
                {ownerLoading ? 'Opening admin...' : '👑 OPEN ADMIN DASHBOARD'}
              </button>
            </form>
          </div>

          {/* ============ OFFLINE LOGIN ============ */}
          {!isOnline && hasOfflineProfile && (
            <div className="mb-8 rounded-xl border border-emerald-500/40 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 p-4">
              <p className="text-sm font-semibold text-emerald-300 mb-3">📴 OFFLINE MODE</p>
              {offlineSession ? (
                <div className="mb-3 text-xs text-emerald-400">
                  Logged in as <span className="font-bold">{offlineSession.email}</span> — session cached locally
                </div>
              ) : null}
              <button
                type="button"
                onClick={handleOfflineLogin}
                disabled={offlineLoginLoading}
                className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 disabled:opacity-50 text-white font-bold rounded-lg transition"
              >
                {offlineLoginLoading ? 'Restoring...' : '🔓 LOGIN OFFLINE (No Internet Needed)'}
              </button>
            </div>
          )}

          {/* ============ FLOW B: REGULAR USERS ============ */}
          <div className="border-t border-slate-800 pt-6">
            <p className="text-xs text-slate-500 text-center mb-4">or sign in with</p>

            {/* Social buttons row */}
            <div className="grid grid-cols-1 gap-2 mb-4">
              <button
                type="button"
                onClick={() => void startOAuth('google')}
                disabled={!!socialLoading}
                className="py-2.5 bg-white hover:bg-slate-100 text-slate-800 rounded-lg text-sm font-semibold transition disabled:opacity-50"
              >
                {socialLoading === 'google' ? '...' : 'Google'}
              </button>
            </div>

            {/* Signup / Login toggle */}
            <div className="border-t border-slate-800 pt-4">
              {!showSignup ? (
                <div className="text-center">
                  <p className="text-sm text-slate-400 mb-3">
                    New here?{' '}
                    <button
                      type="button"
                      onClick={() => setShowSignup(true)}
                      className="text-blue-400 hover:text-blue-300 font-semibold"
                    >
                      Sign up free
                    </button>
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSignup} className="space-y-3">
                  <p className="text-sm font-semibold text-slate-300">Create your free account</p>
                  <input
                    type="text"
                    value={signupName}
                    onChange={(e) => setSignupName(e.target.value)}
                    placeholder="Full name"
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <input
                    type="email"
                    value={signupEmail}
                    onChange={(e) => setSignupEmail(e.target.value)}
                    placeholder="Email address"
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                  <input
                    type="password"
                    value={signupPassword}
                    onChange={(e) => setSignupPassword(e.target.value)}
                    placeholder="Password (min 6 chars)"
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                    minLength={6}
                  />
                  <button
                    type="submit"
                    disabled={signupLoading || !signupEmail || signupPassword.length < 6}
                    className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold rounded-lg transition"
                  >
                    {signupLoading ? 'Creating account...' : 'Sign Up Free'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowSignup(false)}
                    className="w-full py-2 text-slate-500 hover:text-white text-sm transition"
                  >
                    ← Back to sign in
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="text-slate-400">Loading...</div>
      </div>
    }>
      <LoginForm />
    </Suspense>
  )
}
