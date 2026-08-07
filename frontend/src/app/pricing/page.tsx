'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  CheckCircle2, 
  Sparkles, 
  Zap, 
  Shield, 
  Lock, 
  Globe,
  CreditCard,
  ArrowRight,
  Star,
  Users,
  TrendingUp
} from 'lucide-react'
import { useTheme } from '@/components/ThemeProvider'
import { useLanguage } from '@/components/LanguageProvider'
import Link from 'next/link'

const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: '$',
  PKR: 'Rs ',
  INR: 'Rs ',
  EUR: '€',
  AED: 'AED ',
  SAR: 'SAR ',
  GBP: '£',
}

const SUPPORTED_CURRENCIES = ['USD', 'PKR', 'INR', 'EUR', 'AED', 'SAR', 'GBP']

const paymentMethods = [
  { name: 'Visa / Mastercard / Amex', color: 'text-blue-400' },
  { name: 'Apple Pay', color: 'text-gray-300' },
  { name: 'Google Pay', color: 'text-gray-300' },
  { name: 'Mastercard', color: 'text-red-400' },
  { name: 'PayPal', color: 'text-blue-300' },
  { name: 'Wise', color: 'text-teal-400' },
  { name: 'Payoneer', color: 'text-yellow-400' },
  { name: 'Skrill', color: 'text-pink-400' },
  { name: 'Binance Pay', color: 'text-amber-400' },
  { name: 'JazzCash', color: 'text-green-400' },
  { name: 'Easypaisa', color: 'text-orange-400' },
  { name: 'Sadapay', color: 'text-cyan-400' },
  { name: 'NayaPay', color: 'text-lime-400' }
]

const faqs = [
  {
    question: 'What happens after the 3-day free trial?',
    answer: 'After your 3-day PRO trial, billing starts at $19.99/month unless canceled before trial end. Starter and MAX have no trial.'
  },
  {
    question: 'Which payment methods do you accept?',
    answer: 'International: Stripe cards, Apple Pay, Google Pay, PayPal, Wise, Payoneer, Skrill, Binance Pay. Pakistan: JazzCash, Easypaisa, Sadapay, NayaPay.'
  },
  {
    question: 'How is currency conversion shown?',
    answer: 'Prices are listed in USD globally. Checkout auto-converts to your local currency with live rates and shows both values, for example: $19.99 ≈ Rs 5,499.'
  },
  {
    question: 'Where are settlements received?',
    answer: 'Payments are securely processed and settled in Pakistan (Allied Bank) through configured payout rails.'
  },
  {
    question: 'Can I switch between plans?',
    answer: 'Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately, and we\'ll prorate any differences.'
  },
  {
    question: 'Is my data secure?',
    answer: 'Absolutely. We use AES-256-GCM encryption, TLS 1.3, and per-user encryption keys. Your data is never shared with third parties.'
  },
  {
    question: 'Do you offer refunds?',
    answer: 'Yes, we offer a 30-day money-back guarantee. If you\'re not satisfied, contact our support team for a full refund.'
  },
  {
    question: 'Why do Pakistan users see PKR prices?',
    answer: 'Pakistan users see fixed PKR prices optimized for the local market. Users from all other countries see USD market-level prices.'
  }
]

function formatPrice(amount: number | undefined, currency: string): string {
  const value = amount ?? 0
  const symbol = CURRENCY_SYMBOLS[currency] || currency + ' '
  if (currency === 'PKR' || currency === 'INR') {
    return `${symbol}${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
  }
  return `${symbol}${value.toFixed(2)}`
}

export default function PricingPage() {
  const [mounted, setMounted] = useState(false)
  const [plans, setPlans] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [countryCode, setCountryCode] = useState('US')
  const [currency, setCurrency] = useState('USD')
  const [paymentMethod, setPaymentMethod] = useState('stripe')
  const [geoBlocked, setGeoBlocked] = useState(false)
  const { theme, setTheme } = useTheme()
  const { language, setLanguage } = useLanguage()

  // Load saved currency preference from localStorage
  useEffect(() => {
    setMounted(true)
    const savedCurrency = typeof window !== 'undefined' ? localStorage.getItem('preferred_currency') : null
    if (savedCurrency && SUPPORTED_CURRENCIES.includes(savedCurrency)) {
      setCurrency(savedCurrency)
    }
  }, [])

  // Persist currency preference
  useEffect(() => {
    if (typeof window !== 'undefined' && mounted) {
      localStorage.setItem('preferred_currency', currency)
    }
  }, [currency, mounted])

  // Load plans from backend (server-side geo detection decides PKR vs USD)
  useEffect(() => {
    const loadPlans = async () => {
      setLoading(true)
      try {
        const params = new URLSearchParams({ currency, country_code: countryCode, payment_method: paymentMethod })
        const response = await fetch(`/api/payments/plans?${params.toString()}`, { cache: 'no-store' })
        if (!response.ok) {
          setPlans([])
          setGeoBlocked(false)
          return
        }
        const data = await response.json()
        setPlans(data.plans || [])
        if (typeof data?.country_code === 'string') {
          setCountryCode(data.country_code.toUpperCase())
        }
        if (typeof data?.currency === 'string') {
          setCurrency(data.currency)
        }
        if (data.geo_block_notice) {
          setGeoBlocked(true)
        }
      } catch {
        setPlans([])
        setGeoBlocked(false)
      } finally {
        setLoading(false)
      }
    }

    loadPlans()
  }, [countryCode, currency, paymentMethod])

  if (!mounted) return null

  if (geoBlocked) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <div className="text-center p-8">
          <h1 className="text-4xl font-bold mb-4">Not Available</h1>
          <p className="text-xl text-gray-400">Professional AI is not available in your region.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Animated Background */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-950/20 via-purple-950/20 to-pink-950/20 animate-gradient" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-900/20 via-transparent to-transparent" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-purple-900/20 via-transparent to-transparent" />
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-gray-950/80 backdrop-blur-xl border-b border-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <Link href="/" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                  P
                </div>
                <span className="font-bold text-xl text-gradient">Professional AI</span>
              </Link>
            </div>

            <div className="hidden md:flex items-center gap-4">
              <button
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                {theme === 'dark' ? '☀️' : '🌙'}
              </button>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as any)}
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm"
              >
                <option value="en">English</option>
                <option value="ur">اردو</option>
                <option value="ar">العربية</option>
                <option value="hi">हिन्दी</option>
                <option value="bn">বাংলা</option>
              </select>
              <Link href="/login" className="text-gray-400 hover:text-white transition-colors px-4 py-2 text-sm">
                Sign In
              </Link>
              <Link href="/login?tab=register" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-6 py-2 rounded-xl font-medium transition-all glow text-sm">
                Get Started Free
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-6xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-6">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span className="text-sm text-blue-400">Simple, Transparent Pricing</span>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold mb-6">
              Choose Your <span className="text-gradient">Perfect Plan</span>
            </h1>

            <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
              Start free, upgrade when you need more power. All plans include a 3-day free trial.
            </p>

            {/* Social Proof */}
            <div className="flex flex-col items-center gap-4">
              <div className="flex items-center gap-1">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-yellow-500 text-yellow-500" />
                ))}
                <span className="ml-2 text-sm text-gray-400">5.0 from 2,000+ reviews</span>
              </div>
              <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-gray-400 mt-4">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  <span>10,000+ Users</span>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  <span>1M+ Generations</span>
                </div>
                <div className="flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-900/70 px-3 py-2">
                  <Globe className="w-4 h-4 text-blue-400" />
                  <select value={countryCode} onChange={(e) => setCountryCode(e.target.value)} className="bg-transparent text-sm outline-none">
                    <option value="US">United States</option>
                    <option value="PK">Pakistan</option>
                    <option value="IN">India</option>
                    <option value="AE">UAE</option>
                    <option value="SA">Saudi Arabia</option>
                    <option value="GB">UK</option>
                  </select>
                </div>
                <div className="flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-900/70 px-3 py-2">
                  <CreditCard className="w-4 h-4 text-green-400" />
                  <select value={currency} onChange={(e) => setCurrency(e.target.value)} className="bg-transparent text-sm outline-none">
                    {SUPPORTED_CURRENCIES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-900/70 px-3 py-2">
                  <Shield className="w-4 h-4 text-purple-400" />
                  <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} className="bg-transparent text-sm outline-none">
                    <option value="stripe">Stripe</option>
                    <option value="paypal">PayPal</option>
                    <option value="wise">Wise</option>
                    <option value="jazzcash">JazzCash</option>
                    <option value="easypaisa">Easypaisa</option>
                    <option value="sadapay">Sadapay</option>
                    <option value="nayapay">NayaPay</option>
                  </select>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-16 px-4">
        <div className="max-w-6xl mx-auto">
          {loading ? (
            <div className="text-center py-20">
              <div className="inline-block w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-gray-400 mt-4">Loading plans…</p>
            </div>
          ) : plans.length > 0 ? (
            <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-8">
              {plans.map((plan, i) => {
                const monthly = plan.monthly || {}
                const yearly = plan.yearly || {}
                const displayCurrency = monthly.local_currency || currency
                const isYearly = monthly.billing_cycle === 'yearly'
                const mainAmount = isYearly ? yearly.local_amount : monthly.local_amount
                const approxDisplay = monthly.approx_display || yearly.approx_display || ''

                return (
                  <motion.div
                    key={plan.plan_key}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    whileHover={{ y: -5 }}
                    className="relative glass-card p-8"
                  >
                    {plan.badge && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-xs font-bold px-4 py-1 rounded-full">
                        {plan.badge}
                      </div>
                    )}
                    <div className="text-center mb-6">
                      <h3 className="text-2xl font-bold mb-2">{plan.plan}</h3>
                      <div className="flex items-baseline justify-center gap-2">
                        <span className="text-4xl font-bold">{formatPrice(mainAmount, displayCurrency)}</span>
                        <span className="text-gray-400">/{isYearly ? 'year' : 'month'}</span>
                      </div>
                      {approxDisplay && (
                        <p className="text-sm text-gray-400 mt-2">{approxDisplay}</p>
                      )}
                      <p className="text-xs text-gray-500 mt-2">{plan.features.slice(0, 3).join(' • ')}</p>
                    </div>
                    <ul className="space-y-3 mb-8">
                      {plan.features.map((feature: string, j: number) => (
                        <li key={j} className="flex items-start gap-2 text-gray-300 text-sm">
                          <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                    <Link href={`/checkout?plan=${plan.plan_key}&billing_cycle=monthly`} className="block text-center px-6 py-3 rounded-xl font-medium transition-all w-full border border-gray-700 hover:border-gray-500 text-gray-300">
                      Choose {plan.plan}
                    </Link>
                  </motion.div>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-20">
              <p className="text-gray-400">Unable to load plans. Please try again later.</p>
            </div>
          )}

          {/* Payment Methods */}
          <div className="mt-16 text-center">
            <p className="text-gray-400 text-sm mb-4">Accepted payment methods</p>
            <div className="flex flex-wrap items-center justify-center gap-6 opacity-60">
              {paymentMethods.map((method, i) => (
                <div key={i} className={`font-bold ${method.color}`}>
                  {method.name}
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-4">Payments securely processed - received in Pakistan (Allied Bank).</p>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 px-4 bg-gray-900/30">
        <div className="max-w-3xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Frequently Asked <span className="text-gradient">Questions</span>
            </h2>
          </motion.div>

          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="glass-card p-6"
              >
                <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                  <span className="text-blue-400">Q:</span>
                  {faq.question}
                </h3>
                <p className="text-gray-400 text-sm leading-relaxed pl-6">
                  {faq.answer}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="glass-card p-12 text-center relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10" />
            <div className="relative z-10">
              <Sparkles className="w-12 h-12 text-blue-400 mx-auto mb-4" />
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Ready to Get Started?
              </h2>
              <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
                Join 10,000+ professionals already using Professional AI. Start your 3-day free trial today.
              </p>
              <Link
                href="/login?tab=register"
                className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all glow"
              >
                Start Free Trial
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-gray-800/50">
        <div className="max-w-6xl mx-auto text-center">
          <p className="text-gray-500 text-sm">
            © 2026 Professional AI. All rights reserved. Built with cutting-edge AI technology.
          </p>
        </div>
      </footer>
    </div>
  )
}