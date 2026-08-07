'use client'

import { Suspense, useState, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  CheckCircle2,
  CreditCard,
  Lock,
  ArrowRight,
  Shield,
  Loader2,
  AlertCircle,
  Wallet,
  Globe,
  Smartphone,
  Building2,
} from 'lucide-react'
import { useTheme } from '@/components/ThemeProvider'
import { useLanguage } from '@/components/LanguageProvider'
import { paymentsApi, authApi } from '@/lib/api'
import toast from 'react-hot-toast'

const PAYMENT_METHODS = [
  { id: 'stripe', label: 'Credit / Debit Card', icon: CreditCard, desc: 'Visa, Mastercard, Amex, Apple Pay, Google Pay', color: 'text-blue-400' },
  { id: 'paypal', label: 'PayPal', icon: Wallet, desc: 'Pay with your PayPal account', color: 'text-blue-300' },
  { id: 'wise', label: 'Wise', icon: Globe, desc: 'International bank transfer', color: 'text-teal-400' },
  { id: 'payoneer', label: 'Payoneer', icon: Building2, desc: 'Payoneer account payment', color: 'text-yellow-400' },
  { id: 'jazzcash', label: 'JazzCash', icon: Smartphone, desc: 'Pakistan mobile wallet', color: 'text-green-400' },
  { id: 'easypaisa', label: 'Easypaisa', icon: Smartphone, desc: 'Pakistan mobile wallet', color: 'text-orange-400' },
  { id: 'sadapay', label: 'SadaPay', icon: Smartphone, desc: 'Pakistan digital wallet', color: 'text-cyan-400' },
  { id: 'nayapay', label: 'NayaPay', icon: Smartphone, desc: 'Pakistan digital wallet', color: 'text-lime-400' },
]

function CheckoutPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [mounted, setMounted] = useState(false)
  const { theme, setTheme } = useTheme()
  const { language, setLanguage } = useLanguage()

  const planParam = searchParams.get('plan') || 'pro'
  const billingCycle = searchParams.get('billing_cycle') || 'monthly'
  const [plans, setPlans] = useState<any[]>([])
  const [selectedPlan, setSelectedPlan] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [step, setStep] = useState<'review' | 'payment' | 'success'>('review')
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  const [paymentMethod, setPaymentMethod] = useState('stripe')
  const [paymentToken, setPaymentToken] = useState('')
  const [consent, setConsent] = useState(false)
  const [teamSize, setTeamSize] = useState(1)
  const [cardLast4, setCardLast4] = useState('')
  const [cardBrand, setCardBrand] = useState('')
  const [cardExpiryMonth, setCardExpiryMonth] = useState('')
  const [cardExpiryYear, setCardExpiryYear] = useState('')
  const [cardholderName, setCardholderName] = useState('')

  useEffect(() => {
    setMounted(true)
    checkAuth()
    loadPlans()
  }, [])

  const checkAuth = async () => {
    try {
      await authApi.me()
      setIsAuthenticated(true)
    } catch {
      setIsAuthenticated(false)
    }
  }

  useEffect(() => {
    if (plans.length > 0 && !isAuthenticated && !loading) {
      const params = new URLSearchParams({ plan: planParam, billing_cycle: billingCycle })
      router.push(`/login?tab=register&${params.toString()}`)
    }
  }, [plans, isAuthenticated, loading, planParam, billingCycle, router])

  useEffect(() => {
    if (plans.length > 0 && isAuthenticated) {
      const found = plans.find((p) => p.plan_key === planParam)
      if (found) {
        setSelectedPlan(found)
      }
    }
  }, [plans, planParam, isAuthenticated])

  const loadPlans = async () => {
    try {
      const res = await paymentsApi.getPlans()
      setPlans(res.data.plans || [])
    } catch {
      toast.error('Failed to load plans')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!consent) {
      toast.error('You must accept the terms to continue')
      return
    }
    if (!paymentToken.trim()) {
      toast.error('Payment token is required')
      return
    }

    setSubmitting(true)
    try {
      const res = await paymentsApi.createSubscription({
        plan: planParam as any,
        billing_cycle: billingCycle as any,
        payment_method: paymentMethod as any,
        payment_token: paymentToken.trim(),
        consent,
        team_size: teamSize,
        card_last4: cardLast4 || undefined,
        card_brand: cardBrand || undefined,
        card_expiry_month: cardExpiryMonth || undefined,
        card_expiry_year: cardExpiryYear || undefined,
        cardholder_name: cardholderName || undefined,
      })
      toast.success('Subscription activated successfully!')
      setStep('success')
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Payment failed'
      toast.error(msg)
    } finally {
      setSubmitting(false)
    }
  }

  if (!mounted) return null

  if (loading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-400">{loading ? 'Loading checkout…' : 'Redirecting to login…'}</p>
        </div>
      </div>
    )
  }

  if (!selectedPlan) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold mb-2">Plan Not Found</h1>
          <p className="text-gray-400 mb-6">The selected plan could not be loaded.</p>
          <button
            onClick={() => router.push('/pricing')}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium"
          >
            View Plans
          </button>
        </div>
      </div>
    )
  }

  if (step === 'success') {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-lg mx-auto px-4"
        >
          <CheckCircle2 className="w-16 h-16 text-green-400 mx-auto mb-6" />
          <h1 className="text-3xl font-bold mb-4">Subscription Activated!</h1>
          <p className="text-gray-400 mb-8">
            You are now on the <span className="text-white font-semibold">{selectedPlan.plan}</span> plan.
            Welcome aboard!
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => router.push('/dashboard')}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium"
            >
              Go to Dashboard
            </button>
            <button
              onClick={() => router.push('/media')}
              className="px-6 py-3 rounded-xl border border-gray-700 text-gray-300 font-medium hover:border-gray-500"
            >
              Try Media Studio
            </button>
          </div>
        </motion.div>
      </div>
    )
  }

  const monthly = selectedPlan.monthly || {}
  const yearly = selectedPlan.yearly || {}
  const quote = billingCycle === 'yearly' ? yearly : monthly
  const displayCurrency = quote.local_currency || 'USD'
  const amount = quote.local_amount || 0

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <nav className="fixed top-0 w-full z-50 bg-gray-950/80 backdrop-blur-xl border-b border-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <button onClick={() => router.back()} className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
              <ArrowRight className="w-4 h-4 rotate-180" />
              <span className="text-sm">Back</span>
            </button>
            <div className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-green-400" />
              <span className="text-sm text-gray-400">Secure Checkout</span>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 py-24">
        <div className="grid lg:grid-cols-5 gap-8">
          {/* Left: Checkout Form */}
          <div className="lg:col-span-3 space-y-6">
            {step === 'review' && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-8 rounded-2xl">
                <h2 className="text-2xl font-bold mb-6">Order Summary</h2>
                <div className="flex items-center justify-between p-4 bg-gray-900/50 rounded-xl mb-6">
                  <div>
                    <h3 className="font-semibold text-lg">{selectedPlan.plan}</h3>
                    <p className="text-sm text-gray-400">{billingCycle === 'yearly' ? 'Billed yearly' : 'Billed monthly'}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">${amount.toFixed(2)}</p>
                    <p className="text-xs text-gray-500">{displayCurrency}</p>
                  </div>
                </div>

                {selectedPlan.plan_key === 'business' && (
                  <div className="mb-6">
                    <label className="block text-sm text-gray-400 mb-2">Team Size (min 5 for Business)</label>
                    <input
                      type="number"
                      min={5}
                      value={teamSize}
                      onChange={(e) => setTeamSize(Math.max(5, parseInt(e.target.value) || 5))}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}

                <button
                  onClick={() => setStep('payment')}
                  className="w-full py-4 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 font-semibold text-lg transition-all flex items-center justify-center gap-2"
                >
                  Continue to Payment <ArrowRight className="w-5 h-5" />
                </button>
              </motion.div>
            )}

            {step === 'payment' && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-8 rounded-2xl">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold">Payment Method</h2>
                  <button onClick={() => setStep('review')} className="text-sm text-gray-400 hover:text-white">
                    Back
                  </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label className="block text-sm text-gray-400 mb-3">Select Payment Method</label>
                    <div className="grid grid-cols-2 gap-3">
                      {PAYMENT_METHODS.map((method) => (
                        <button
                          key={method.id}
                          type="button"
                          onClick={() => setPaymentMethod(method.id)}
                          className={`p-4 rounded-xl border text-left transition-all ${
                            paymentMethod === method.id
                              ? 'border-blue-500 bg-blue-500/10'
                              : 'border-gray-800 bg-gray-900/50 hover:border-gray-700'
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <method.icon className={`w-5 h-5 ${method.color}`} />
                            <div>
                              <p className="font-medium text-sm">{method.label}</p>
                              <p className="text-xs text-gray-500">{method.desc}</p>
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Payment Token / Reference</label>
                    <input
                      type="text"
                      value={paymentToken}
                      onChange={(e) => setPaymentToken(e.target.value)}
                      placeholder={
                        paymentMethod === 'stripe'
                          ? 'tok_xxx or pm_xxx'
                          : paymentMethod === 'paypal'
                          ? 'PAYID-xxx'
                          : 'Payment reference or token'
                      }
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-600"
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {paymentMethod === 'stripe'
                        ? 'Use a Stripe test token (tok_visa, tok_mastercard) for testing.'
                        : 'Enter the payment token or reference from your payment provider.'}
                    </p>
                  </div>

                  {(paymentMethod === 'stripe' || paymentMethod === 'paypal') && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">Card Last 4 (optional)</label>
                        <input
                          type="text"
                          maxLength={4}
                          value={cardLast4}
                          onChange={(e) => setCardLast4(e.target.value.replace(/\D/g, ''))}
                          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">Card Brand (optional)</label>
                        <input
                          type="text"
                          value={cardBrand}
                          onChange={(e) => setCardBrand(e.target.value)}
                          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  )}

                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Cardholder Name (optional)</label>
                    <input
                      type="text"
                      value={cardholderName}
                      onChange={(e) => setCardholderName(e.target.value)}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="flex items-start gap-3 p-4 bg-gray-900/50 rounded-xl border border-gray-800">
                    <input
                      type="checkbox"
                      id="consent"
                      checked={consent}
                      onChange={(e) => setConsent(e.target.checked)}
                      className="mt-1 w-4 h-4 accent-blue-500"
                    />
                    <label htmlFor="consent" className="text-sm text-gray-300 cursor-pointer">
                      I agree to the Terms of Service and Privacy Policy. I understand that my subscription will auto-renew
                      {billingCycle === 'yearly' ? ' annually' : ' monthly'} until canceled.
                    </label>
                  </div>

                  <button
                    type="submit"
                    disabled={submitting}
                    className="w-full py-4 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:opacity-50 font-semibold text-lg transition-all flex items-center justify-center gap-2"
                  >
                    {submitting ? (
                      <><Loader2 className="w-5 h-5 animate-spin" /> Processing…</>
                    ) : (
                      <><Shield className="w-5 h-5" /> Pay ${amount.toFixed(2)}</>
                    )}
                  </button>
                </form>
              </motion.div>
            )}
          </div>

          {/* Right: Trust Sidebar */}
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-card p-6 rounded-2xl">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5 text-green-400" />
                Secure Payment
              </h3>
              <ul className="space-y-3 text-sm text-gray-400">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5" />
                  <span>256-bit SSL encryption on all transactions</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5" />
                  <span>Payments securely processed — received in Pakistan (Allied Bank)</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5" />
                  <span>Cancel anytime — no questions asked</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5" />
                  <span>30-day money-back guarantee</span>
                </li>
              </ul>
            </div>

            <div className="glass-card p-6 rounded-2xl">
              <h3 className="font-semibold mb-4">What You Get</h3>
              <ul className="space-y-2 text-sm text-gray-300">
                {selectedPlan.features?.slice(0, 6).map((feature: string, i: number) => (
                  <li key={i} className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function CheckoutPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
            <p className="text-gray-400">Loading checkout…</p>
          </div>
        </div>
      }
    >
      <CheckoutPageContent />
    </Suspense>
  )
}
