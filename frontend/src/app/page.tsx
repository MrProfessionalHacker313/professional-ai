'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  Sparkles,
  Code2,
  Shield,
  Zap,
  Globe,
  Image,
  Mic,
  Search,
  Download,
  ArrowRight,
  Star,
  Users,
  TrendingUp,
  ChevronRight,
  Lock,
  MessageSquare,
  Bug,
  Video,
} from 'lucide-react'
import { useTheme } from '@/components/ThemeProvider'
import { useLanguage } from '@/components/LanguageProvider'

const features = [
  {
    id: 'coding',
    title: 'AI Coding Engine',
    description: 'Generate complete production-ready code in 35+ languages with security best practices built in.',
    icon: Code2,
    color: 'from-blue-500 to-cyan-500',
    href: '/chat?mode=code',
  },
  {
    id: 'security',
    title: 'Cybersecurity Assistant',
    description: 'Scan code for vulnerabilities, learn OWASP Top 10, and get defense strategies.',
    icon: Shield,
    color: 'from-purple-500 to-pink-500',
    href: '/chat?mode=security',
  },
  {
    id: 'chat',
    title: 'Multilingual Chat',
    description: 'Chat in Urdu, Hindi, Arabic, Bengali, and 40+ languages with native-quality responses.',
    icon: Globe,
    color: 'from-green-500 to-emerald-500',
    href: '/chat?mode=chat',
  },
  {
    id: 'media',
    title: 'AI Media Studio',
    description: 'Generate videos, images, and animations with 8K quality, voice-over, and auto-editing.',
    icon: Video,
    color: 'from-orange-500 to-rose-500',
    href: '/media',
  },
  {
    id: 'voice',
    title: 'Voice AI',
    description: 'Speak to AI naturally and get voice responses in multiple languages and styles.',
    icon: Mic,
    color: 'from-indigo-500 to-blue-500',
    href: '/chat?mode=voice',
  },
  {
    id: 'search',
    title: 'AI Web Search',
    description: 'Search the web with AI-powered summarization and privacy-focused results.',
    icon: Search,
    color: 'from-yellow-500 to-amber-500',
    href: '/chat?mode=search',
  },
]

const stats = [
  { label: 'Active Users', value: '10,000+', icon: Users },
  { label: 'AI Generations', value: '1M+', icon: Zap },
  { label: 'Rating', value: '5.0', icon: Star },
  { label: 'Languages', value: '40+', icon: Globe },
]

export default function HomePage() {
  const router = useRouter()
  const [mounted, setMounted] = useState(false)
  const { theme, setTheme } = useTheme()
  const { language, setLanguage } = useLanguage()

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-gray-400">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-gray-950/80 backdrop-blur-xl border-b border-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                P
              </div>
              <span className="font-bold text-xl text-gradient">Professional AI</span>
            </Link>

            <div className="hidden md:flex items-center gap-4">
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as any)}
                className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm"
              >
                <option value="en">EN</option>
                <option value="ur">UR</option>
                <option value="ar">AR</option>
                <option value="hi">HI</option>
                <option value="bn">BN</option>
              </select>
              <Link href="/landing" className="text-gray-400 hover:text-white transition-colors px-4 py-2 text-sm">
                Landing
              </Link>
              <Link href="/blog" className="text-gray-400 hover:text-white transition-colors px-4 py-2 text-sm">
                Blog
              </Link>
              <button
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                {theme === 'dark' ? '☀️' : '🌙'}
              </button>
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
              <span className="text-sm text-blue-400">World's Most Powerful AI Assistant</span>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold mb-6">
              Code. Create. Secure.{' '}
              <span className="text-gradient">All in One AI.</span>
            </h1>

            <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
              Professional AI is the ultimate all-in-one AI platform. Generate code, create media,
              secure your apps, and chat in 40+ languages — all from one place.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/login?tab=register"
                className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all glow"
              >
                Start Free Trial
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                href="/pricing"
                className="inline-flex items-center gap-2 border border-gray-700 hover:border-gray-500 text-gray-300 px-8 py-4 rounded-xl font-semibold text-lg transition-all"
              >
                View Pricing
                <ChevronRight className="w-5 h-5" />
              </Link>
            </div>

            {/* Social Proof */}
            <div className="flex flex-col items-center gap-4 mt-12">
              <div className="flex items-center gap-1">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-yellow-500 text-yellow-500" />
                ))}
                <span className="ml-2 text-sm text-gray-400">5.0 from 2,000+ reviews</span>
              </div>
              <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-gray-400">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  <span>10,000+ Users</span>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  <span>1M+ Generations</span>
                </div>
                <div className="flex items-center gap-2">
                  <Download className="w-4 h-4" />
                  <span>Direct App Downloads</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Everything You Need in <span className="text-gradient">One Platform</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              From coding to cybersecurity, media generation to multilingual chat —
              Professional AI has you covered.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, i) => (
              <motion.div
                key={feature.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -5 }}
                className="relative glass-card p-8 group"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold mb-3 group-hover:text-blue-400 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-gray-400 mb-6">{feature.description}</p>
                <Link
                  href={feature.href}
                  className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors text-sm font-medium"
                >
                  Try it now <ArrowRight className="w-4 h-4" />
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 px-4 bg-gray-900/30">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, i) => (
              <div key={i} className="text-center">
                <stat.icon className="w-8 h-8 text-blue-400 mx-auto mb-4" />
                <div className="text-3xl font-bold mb-2">{stat.value}</div>
                <div className="text-sm text-gray-400">{stat.label}</div>
              </div>
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
                Join thousands of professionals already using Professional AI.
                Start your free trial today.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link
                  href="/login?tab=register"
                  className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all glow"
                >
                  Start Free Trial <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  href="/pricing"
                  className="inline-flex items-center gap-2 border border-gray-700 hover:border-gray-500 text-gray-300 px-8 py-4 rounded-xl font-semibold text-lg transition-all"
                >
                  View Plans <ChevronRight className="w-5 h-5" />
                </Link>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-gray-800/50">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                P
              </div>
              <span className="font-bold text-lg text-gradient">Professional AI</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-gray-400">
              <Link href="/pricing" className="hover:text-white transition-colors">Pricing</Link>
              <Link href="/features" className="hover:text-white transition-colors">Features</Link>
              <Link href="/blog" className="hover:text-white transition-colors">Blog</Link>
              <Link href="/download" className="hover:text-white transition-colors">Download</Link>
              <Link href="/login" className="hover:text-white transition-colors">Sign In</Link>
            </div>
            <p className="text-sm text-gray-500">
              &copy; 2026 Professional AI. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
