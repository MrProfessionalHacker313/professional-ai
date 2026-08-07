'use client'

import { useState } from 'react'
import toast from 'react-hot-toast'
import { authApi } from '@/lib/api'

export default function PasskeySetup() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  const handleSetup = async () => {
    setLoading(true)
    setError('')
    try {
      const { startRegistration } = await import('@simplewebauthn/browser')
      const beginRes = await authApi.passkeyRegisterBegin()
      const options = beginRes.data.publicKey
      const regResult = await startRegistration(options)
      const completeRes = await authApi.passkeyRegisterComplete({
        credential_id: regResult.id,
        raw_id: regResult.rawId,
        response: regResult.response,
        type: regResult.type,
      })
      setDone(true)
      toast.success('Passkey saved! Use fingerprint/face/PIN to sign in next time.')
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Passkey setup failed'
      setError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 text-sm text-green-300">
        ✅ Passkey set up successfully. Next time just tap "Sign in with Passkey".
      </div>
    )
  }

  return (
    <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
      <p className="font-medium text-blue-300 mb-2">🔑 Speed up your login with a Passkey</p>
      <p className="text-xs text-slate-400 mb-3">
        Use your fingerprint, face ID, or device PIN to sign in with one tap — no passwords needed.
      </p>
      <button
        onClick={handleSetup}
        disabled={loading}
        className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition"
      >
        {loading ? 'Setting up...' : 'Set Up Passkey Now'}
      </button>
      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
    </div>
  )
}