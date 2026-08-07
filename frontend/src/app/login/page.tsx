'use client'

import React, { useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import toast from 'react-hot-toast'
import { authApi } from '@/lib/api'
import { COUNTRIES } from '@/lib/countries'

const PRIMARY_OWNER_EMAIL = (process.env.NEXT_PUBLIC_OWNER_EMAIL || 'redr28126@gmail.com').toLowerCase().trim()
const OWNER_EMAILS = [
  PRIMARY_OWNER_EMAIL,
  ...(process.env.NEXT_PUBLIC_OWNER_EMAILS || '')
    .split(',')
    .map((item) => item.toLowerCase().trim())
    .filter(Boolean),
]

function setAuthCookies(data: any) {
  if (typeof window === 'undefined') return
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

  // ===== FLOW A: OWNER (email only) =====
  const [ownerEmail, setOwnerEmail] = useState('')
  const [ownerLoading, setOwnerLoading] = useState(false)

  // ===== FLOW B: REGULAR USERS =====
  const [showSignup, setShowSignup] = useState(false)
  const [signupName, setSignupName] = useState('')
  const [signupEmail, setSignupEmail] = useState('')
  const [signupPassword, setSignupPassword] = useState('')
  const [signupLoading, setSignupLoading] = useState(false)

  const [countryIndex, setCountryIndex] = useState(0)
  const [phoneNumber, setPhoneNumber] = useState('')
  const [otpCode, setOtpCode] = useState('')
  const [otpSent, setOtpSent] = useState(false)
  const [otpDevMode, setOtpDevMode] = useState(false)
  const [otpLoading, setOtpLoading] = useState(false)

  const [socialLoading, setSocialLoading] = useState<string | null>(null)

  const selectedCountry = COUNTRIES[countryIndex] || COUNTRIES[0]

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
      toast.success('👑 OWNER ACCESS GRANTED')
      router.push('/admin')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Owner login failed')
    } finally {
      setOwnerLoading(false)
    }
  }

  // ===== FLOW B: Social sign-in =====
  const startOAuth = async (provider: 'google' | 'microsoft' | 'github' | 'apple') => {
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
      toast.success('Account created! 🎉')
      router.push('/dashboard?passkey_setup=1')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Signup failed')
    } finally {
      setSignupLoading(false)
    }
  }

  // ===== FLOW B: Phone OTP =====
  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    setOtpLoading(true)
    try {
      const res = await authApi.sendOTP({ phone: phoneNumber, country_code: selectedCountry.dial })
      setOtpSent(true)
      setOtpDevMode(!!res.data.dev_mode)
      toast.success(res.data.dev_mode ? 'Dev mode: OTP in server terminal' : 'OTP sent via SMS!')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to send OTP')
    } finally {
      setOtpLoading(false)
    }
  }

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    setOtpLoading(true)
    try {
      const res = await authApi.verifyOTP({ phone: phoneNumber, country_code: selectedCountry.dial, code: otpCode })
      const data = res.data
      if (data.requires_2fa) {
        toast('2FA code required', { icon: '🔐' })
        return
      }
      setAuthCookies(data)
      toast.success(data.is_new_user ? 'Account created! 🎉' : 'Logged in with phone!')
      router.push(data.is_new_user ? '/dashboard?passkey_setup=1' : redirect)
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'OTP verification failed')
    } finally {
      setOtpLoading(false)
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

          {/* ============ FLOW B: REGULAR USERS ============ */}
          <div className="border-t border-slate-800 pt-6">
            <p className="text-xs text-slate-500 text-center mb-4">or sign in with</p>

            {/* Social buttons row */}
            <div className="grid grid-cols-2 gap-2 mb-4">
              <button
                type="button"
                onClick={() => void startOAuth('google')}
                disabled={!!socialLoading}
                className="py-2.5 bg-white hover:bg-slate-100 text-slate-800 rounded-lg text-sm font-semibold transition disabled:opacity-50"
              >
                {socialLoading === 'google' ? '...' : 'Google'}
              </button>
              <button
                type="button"
                onClick={() => void startOAuth('microsoft')}
                disabled={!!socialLoading}
                className="py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition disabled:opacity-50"
              >
                {socialLoading === 'microsoft' ? '...' : 'Microsoft'}
              </button>
              <button
                type="button"
                onClick={() => void startOAuth('github')}
                disabled={!!socialLoading}
                className="py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition disabled:opacity-50"
              >
                {socialLoading === 'github' ? '...' : 'GitHub'}
              </button>
              <button
                type="button"
                onClick={() => void startOAuth('apple')}
                disabled={!!socialLoading}
                className="py-2.5 bg-black hover:bg-neutral-800 text-white rounded-lg text-sm font-medium transition disabled:opacity-50"
              >
                {socialLoading === 'apple' ? '...' : 'Apple'}
              </button>
            </div>

            {/* Phone OTP */}
            {!otpSent ? (
              <form onSubmit={handleSendOtp} className="space-y-3 mb-4">
                <div className="flex gap-2">
                  <select
                    value={countryIndex}
                    onChange={(e) => setCountryIndex(Number(e.target.value))}
                    className="w-1/3 px-2 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                  >
                    {COUNTRIES.map((c, i) => (
                      <option key={c.code + c.dial} value={i}>{c.flag} {c.dial}</option>
                    ))}
                  </select>
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value.replace(/[^\d]/g, ''))}
                    placeholder="Phone number"
                    className="flex-1 px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-green-500"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={otpLoading || phoneNumber.length < 7}
                  className="w-full py-2.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-semibold rounded-lg transition"
                >
                  {otpLoading ? 'Sending...' : '📱 Phone OTP'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleVerifyOtp} className="space-y-3 mb-4">
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 text-sm text-green-300">
                  <p className="font-medium mb-1">📱 OTP Sent</p>
                  <p>Enter the 6-digit code sent to {selectedCountry.dial} {phoneNumber}.</p>
                  {otpDevMode && (
                    <p className="mt-1 text-amber-400">Dev mode: Check the backend terminal for the OTP code.</p>
                  )}
                </div>
                <input
                  type="text"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="6-digit code"
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 text-center text-2xl tracking-widest focus:outline-none focus:ring-2 focus:ring-green-500"
                  maxLength={6}
                />
                <button
                  type="submit"
                  disabled={otpLoading || otpCode.length !== 6}
                  className="w-full py-2.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-semibold rounded-lg transition"
                >
                  {otpLoading ? 'Verifying...' : 'Verify & Sign In'}
                </button>
                <button
                  type="button"
                  onClick={() => setOtpSent(false)}
                  className="w-full py-2 text-slate-500 hover:text-white text-sm transition"
                >
                  ← Change number
                </button>
              </form>
            )}

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