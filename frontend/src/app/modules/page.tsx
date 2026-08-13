'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  MessageSquare,
  Code2,
  Wand2,
  Image,
  Video,
  Mic,
  FileText,
  Shield,
  Terminal,
  Clapperboard,
  Sparkles,
  ArrowRight,
  Lock,
  CheckCircle2,
  Zap,
  Crown,
  ChevronRight,
  Search,
  Star,
  Users,
  TrendingUp,
  Download,
  CreditCard,
  Settings,
  User,
  LogOut,
  Menu,
  X,
} from 'lucide-react'
import { useTheme } from '@/components/ThemeProvider'
import { useLanguage } from '@/components/LanguageProvider'
import Link from 'next/link'
import { authApi, creditsApi, paymentsApi, modulesApi, deleteAllCookies } from '@/lib/api'

const MODULES = [
  {
    id: 'chat',
    name: 'Chat',
    description: 'AI chat with multilingual support in 40+ languages. Fast, accurate, and context-aware.',
    icon: MessageSquare,
    color: 'from-blue-500 to-cyan-500',
    href: '/chat?mode=chat',
    free: true,
    price: 'Free (daily credits)',
  },
  {
    id: 'code_generation',
    name: 'Code Generation',
    description: 'Generate production-ready code in 35+ languages with security best practices built in.',
    icon: Code2,
    color: 'from-green-500 to-emerald-500',
    href: '/chat?mode=code',
    free: true,
    price: 'Free (daily credits)',
  },
  {
    id: 'prompt_forge',
    name: 'Prompt Forge',
    description: 'Generate unblockable, optimized prompts for any AI model. Get better results every time.',
    icon: Wand2,
    color: 'from-amber-500 to-orange-500',
    href: '/prompt-forge',
    free: false,
    price: '$19.99/mo (PRO)',
  },
  {
    id: 'image_generation',
    name: 'Image Generation',
    description: 'Create stunning AI images with Flux, SDXL, and 8K quality. Unlimited styles and resolutions.',
    icon: Image,
    color: 'from-pink-500 to-rose-500',
    href: '/media?mode=image',
    free: false,
    price: '$19.99/mo (PRO)',
  },
  {
    id: 'video_generation',
    name: 'Video Generation',
    description: 'Generate AI videos with Kling, Runway, Luma, and Pika engines. Up to 10 minutes, 8K quality.',
    icon: Video,
    color: 'from-red-500 to-orange-500',
    href: '/media?mode=video',
    free: false,
    price: '$19.99/mo (PRO)',
  },
  {
    id: 'voice_audio',
    name: 'Voice/Audio',
    description: 'Text-to-speech, voice cloning, and natural voice conversations in 40+ languages.',
    icon: Mic,
    color: 'from-indigo-500 to-blue-500',
    href: '/media?mode=voice',
    free: false,
    price: '$19.99/mo (PRO)',
  },
  {
    id: 'document_analysis',
    name: 'Document Analysis',
    description: 'Upload PDFs, docs, and spreadsheets. Get AI-powered analysis, summaries, and insights.',
    icon: FileText,
    color: 'from-purple-500 to-violet-500',
    href: '/media?mode=documents',
    free: false,
    price: '$19.99/mo (PRO)',
  },
  {
    id: 'security_analysis',
    name: 'Security Analysis',
    description: 'Scan code for vulnerabilities, learn OWASP Top 10, and get defense strategies.',
    icon: Shield,
    color: 'from-emerald-500 to-teal-500',
    href: '/chat?mode=security',
    free: false,
    price: '$19.99/mo (PRO)',
  },
  {
    id: 'advanced_coding',
    name: 'Advanced Coding',
    description: 'Bug fixing, refactoring, and advanced code generation with multi-language support.',
    icon: Terminal,
    color: 'from-sky-500 to-blue-600',
    href: '/chat?mode=code',
    free: false,
    price: '$19.99/mo (PRO)',
  },
  {
    id: 'auto_editor',
    name: 'Auto Video Editor',
    description: 'AI-powered video editing with presets, transitions, auto-captions, and color grading.',
    icon: Clapperboard,
    color: 'from-fuchsia-500 to-pink-600',
    href: '/media?mode=editor',
    free: false,
    price: '$19.99/mo (PRO)',
  },
  {
    id: 'media_studio',
    name: 'Media Studio',
    description: 'Full AI media studio: video, image, animation, and voice-over in one place.',
    icon: Sparkles,
    color: 'from-violet-500 to-purple-600',
    href: '/media',
    free: false,
    price: '$19.99/mo (PRO)',
  },
]

export default function ModulesPage() {
  const [mounted, setMounted] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [isOwner, setIsOwner] = useState(false)
  const [userPlan, setUserPlan] = useState('free')
  const [isPro, setIsPro] = useState(false)
  const [userModules, setUserModules] = useState<string[]>([])
  const [creditInfo, setCreditInfo] = useState<any>(null)
  const [upgrading, setUpgrading] = useState(false)
  const { theme, setTheme } = useTheme()
  const { language, setLanguage } = useLanguage()

  useEffect(() => { setMounted(true) }, [])

  useEffect(() => {
    if (!mounted) return
    let cancelled = false

    authApi.checkIsOwner().then((res) => {
      if (!cancelled) setIsOwner(Boolean(res.data?.is_owner))
    }).catch(() => {
      if (!cancelled) setIsOwner(false)
    })

    creditsApi.getLimits().then((res) => {
      if (!cancelled && res.data) {
        setUserPlan(res.data.plan || 'free')
        setIsPro(['pro', 'pro_yearly', 'max', 'business', 'enterprise', 'trial'].includes(res.data.plan || 'free'))
      }
    }).catch(() => {})

    modulesApi.getMyAccess().then((res) => {
      if (!cancelled && res.data) {
        setUserModules(res.data.accessible_modules || [])
      }
    }).catch(() => {})

    creditsApi.getInfo().then((res) => {
      if (!cancelled && res.data) {
        setCreditInfo(res.data)
      }
    }).catch(() => {})

    return () => { cancelled = true }
  }, [mounted])

  const handleUpgrade = async () => {
    setUpgrading(true)
    try {
      const res = await paymentsApi.createSubscription({
        plan: 'pro',
        billing_cycle: 'monthly',
        payment_method: 'stripe',
        payment_token: 'demo_stripe_token',
        consent: true,
        currency: 'USD',
        country_code: 'US',
      })
      if (res.data) {
        window.location.href = '/pricing?success=true'
      }
    } catch (err) {
      window.location.href = '/pricing'
    } finally {
      setUpgrading(false)
    }
  }

  if (!mounted) return null

  const handleLogout = async () => {
    try {
      await authApi.logout()
    } catch {
      // ignore logout API errors
    } finally {
      deleteAllCookies()
      window.location.href = '/login'
    }
  }

  const sidebarItems = [
    { icon: MessageSquare, label: 'Chat', href: '/chat?mode=chat', active: false },
    { icon: Code2, label: 'Code Lab', href: '/chat?mode=code', active: false },
    { icon: Shield, label: 'Security', href: '/chat?mode=security', active: false },
    { icon: Wand2, label: 'Prompt Forge', href: '/prompt-forge', active: false },
    { icon: Video, label: 'Media', href: '/media', active: false },
    { icon: Lock, label: 'Vault', href: '/vault', active: false },
    { icon: Sparkles, label: 'Modules', href: '/modules', active: true },
    { icon: CreditCard, label: 'Upgrade', href: '/pricing', active: false },
    { icon: Settings, label: 'Settings', href: '/settings', active: false },
    ...(isOwner
      ? [
          { icon: Shield, label: 'Admin Panel', href: '/admin', active: false },
          { icon: Sparkles, label: 'Use AI', href: '/chat?owner=1', active: false },
          { icon: TrendingUp, label: 'AI Dashboard', href: '/ai-dashboard', active: false },
        ]
      : []),
  ]

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="flex">
        {/* Sidebar */}
        <aside className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-gray-900/50 backdrop-blur-xl border-r border-gray-800/50 transition-all duration-300 fixed h-screen z-40`}>
          <div className="p-4">
            {/* Logo */}
            <div className="flex items-center gap-2 mb-8">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                P
              </div>
              {sidebarOpen && <span className="font-bold text-lg text-gradient">Professional AI</span>}
            </div>

            {/* Navigation */}
            <nav className="space-y-2">
              {sidebarItems.map((item, i) => (
                <Link
                  key={i}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors group ${
                    item.active ? 'bg-blue-500/10 text-blue-400' : 'hover:bg-gray-800/50'
                  }`}
                >
                  <item.icon className={`w-5 h-5 flex-shrink-0 ${item.active ? 'text-blue-400' : 'text-gray-400 group-hover:text-white'} transition-colors`} />
                  {sidebarOpen && <span className="text-sm text-gray-300 group-hover:text-white transition-colors">{item.label}</span>}
                </Link>
              ))}
            </nav>

            {/* Bottom Actions */}
            <div className="absolute bottom-4 left-4 right-4 space-y-2">
              <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-gray-800/50 transition-colors cursor-pointer">
                <User className="w-5 h-5 text-gray-400 flex-shrink-0" />
                {sidebarOpen && <span className="text-sm text-gray-300">Profile</span>}
              </div>
              <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-gray-800/50 transition-colors cursor-pointer" onClick={handleLogout}>
                <LogOut className="w-5 h-5 text-gray-400 flex-shrink-0" />
                {sidebarOpen && <span className="text-sm text-gray-300">Logout</span>}
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className={`flex-1 ${sidebarOpen ? 'ml-64' : 'ml-20'} transition-all duration-300`}>
          {/* Top Bar */}
          <header className="sticky top-0 z-30 bg-gray-950/80 backdrop-blur-xl border-b border-gray-800/50">
            <div className="px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <Menu className={`w-5 h-5 transition-transform ${sidebarOpen ? 'rotate-180' : ''}`} />
                </button>
                <div>
                  <h1 className="text-xl font-bold">Modules</h1>
                  <p className="text-sm text-gray-400">Choose your AI module and start creating</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                {/* Plan Badge */}
                <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-xl">
                  <Crown className="w-4 h-4 text-purple-400" />
                  <span className="text-sm font-medium text-purple-400">{isOwner ? 'OWNER - UNLIMITED' : (isPro ? 'PRO Plan' : 'Free Plan')}</span>
                </div>

                {/* Credits Meter */}
                {creditInfo && (
                  <div className="hidden md:flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-yellow-500" />
                      <span className="text-sm text-gray-400">
                        {isOwner ? 'UNLIMITED (Owner - All features free)' : (isPro ? 'UNLIMITED' : `${creditInfo.balance?.toLocaleString() || 0} / ${(creditInfo.total_granted || 0).toLocaleString()} credits`)}
                      </span>
                    </div>
                    {!isPro && !isOwner && (
                      <div className="w-32 h-2 bg-gray-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
                          style={{ width: `${Math.min(((creditInfo.balance || 0) / Math.max(1, (creditInfo.total_granted || 1))) * 100, 100)}%` }}
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Language Selector */}
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value as any)}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm hidden md:block"
                >
                  <option value="en">EN</option>
                  <option value="ur">UR</option>
                  <option value="ar">AR</option>
                  <option value="hi">HI</option>
                  <option value="bn">BN</option>
                </select>

                {/* Theme Toggle */}
                <button
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                >
                  {theme === 'dark' ? '☀️' : '🌙'}
                </button>
              </div>
            </div>
          </header>

          {/* Modules Content */}
          <div className="p-6">
            {/* Upgrade Banner for Free Users */}
            {!isPro && !isOwner && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-8 p-6 rounded-2xl bg-gradient-to-r from-purple-500/10 via-pink-500/10 to-blue-500/10 border border-purple-500/20 relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-purple-500/5 via-pink-500/5 to-blue-500/5" />
                <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
                      <Crown className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold">Upgrade to PRO</h2>
                      <p className="text-gray-400">Unlock all modules: Image, Video, Voice, Prompt Forge, and more. Starting at $19.99/month.</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={handleUpgrade}
                      disabled={upgrading}
                      className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-6 py-3 rounded-xl font-semibold transition-all glow disabled:opacity-50"
                    >
                      {upgrading ? 'Processing...' : 'Upgrade Now'}
                      <ArrowRight className="w-5 h-5" />
                    </button>
                    <Link
                      href="/pricing"
                      className="inline-flex items-center gap-2 border border-gray-700 hover:border-gray-500 text-gray-300 px-6 py-3 rounded-xl font-semibold transition-all"
                    >
                      View Plans
                    </Link>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Modules Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {MODULES.map((module, i) => {
                const IconComponent = module.icon
                const hasAccess = isOwner || isPro || module.free || userModules.includes(module.id)

                return (
                  <motion.div
                    key={module.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className={`glass-card p-6 relative overflow-hidden group ${
                      hasAccess ? 'hover:border-blue-500/30' : 'opacity-75'
                    }`}
                  >
                    {/* Free Badge */}
                    {module.free && (
                      <div className="absolute top-4 right-4 px-2 py-1 bg-green-500/10 border border-green-500/20 rounded-lg">
                        <span className="text-xs font-medium text-green-400">FREE</span>
                      </div>
                    )}

                    {/* Pro Badge */}
                    {!module.free && !hasAccess && (
                      <div className="absolute top-4 right-4 px-2 py-1 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                        <span className="text-xs font-medium text-purple-400">PRO</span>
                      </div>
                    )}

                    {/* Check Badge */}
                    {hasAccess && !module.free && (
                      <div className="absolute top-4 right-4 px-2 py-1 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                        <CheckCircle2 className="w-4 h-4 text-blue-400" />
                      </div>
                    )}

                    <div className="flex items-start gap-4">
                      <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${module.color} flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform`}>
                        <IconComponent className="w-7 h-7 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-lg mb-1 group-hover:text-blue-400 transition-colors">
                          {module.name}
                        </h3>
                        <p className="text-sm text-gray-400 mb-3 line-clamp-2">
                          {module.description}
                        </p>
                        <div className="flex items-center justify-between">
                          <span className={`text-sm font-medium ${module.free ? 'text-green-400' : 'text-purple-400'}`}>
                            {module.price}
                          </span>
                          {hasAccess ? (
                            <Link
                              href={module.href}
                              className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors text-sm font-medium"
                            >
                              Open <ArrowRight className="w-4 h-4" />
                            </Link>
                          ) : (
                            <button
                              onClick={() => window.location.href = '/pricing'}
                              className="inline-flex items-center gap-1 bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
                            >
                              <Lock className="w-3 h-3" />
                              Upgrade
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
