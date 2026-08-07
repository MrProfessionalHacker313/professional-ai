'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  MessageSquare,
  Code2,
  Shield,
  Lock,
  FolderOpen,
  Sparkles,
  Settings,
  CreditCard,
  ChevronRight,
  Zap,
  Bug,
  Search,
  Image as ImageIcon,
  Mic,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Play,
  Copy,
  ExternalLink,
  Bell,
  User,
  LogOut,
  Moon,
  Sun,
  Globe
} from 'lucide-react'
import { useTheme } from '@/components/ThemeProvider'
import { useLanguage } from '@/components/LanguageProvider'
import Link from 'next/link'
import { authApi } from '@/lib/api'

interface QuickAction {
  id: string
  title: string
  description: string
  icon: any
  color: string
  href: string
}

interface RecentProject {
  id: string
  name: string
  type: string
  updatedAt: string
  status: 'completed' | 'in-progress' | 'failed'
}

const quickActions: QuickAction[] = [
  {
    id: 'generate-code',
    title: 'Generate Code',
    description: 'Create production-ready code in any language',
    icon: Code2,
    color: 'from-blue-500 to-cyan-500',
    href: '/chat?mode=code'
  },
  {
    id: 'fix-bug',
    title: 'Fix Bug',
    description: 'Paste broken code, get instant fixes',
    icon: Bug,
    color: 'from-red-500 to-orange-500',
    href: '/chat?mode=bugfix'
  },
  {
    id: 'analyze-security',
    title: 'Analyze Security',
    description: 'Scan code for vulnerabilities',
    icon: Shield,
    color: 'from-purple-500 to-pink-500',
    href: '/chat?mode=security'
  },
  {
    id: 'create-image',
    title: 'Create Image',
    description: 'Generate images with AI',
    icon: ImageIcon,
    color: 'from-green-500 to-emerald-500',
    href: '/chat?mode=image'
  },
  {
    id: 'voice-chat',
    title: 'Voice Chat',
    description: 'Talk to AI with natural voice',
    icon: Mic,
    color: 'from-indigo-500 to-blue-500',
    href: '/chat?mode=voice'
  },
  {
    id: 'web-search',
    title: 'Web Search',
    description: 'Search the web with AI assistance',
    icon: Search,
    color: 'from-yellow-500 to-amber-500',
    href: '/chat?mode=search'
  }
]

const recentProjects: RecentProject[] = [
  {
    id: '1',
    name: 'E-commerce API',
    type: 'Code Generation',
    updatedAt: '2 hours ago',
    status: 'completed'
  },
  {
    id: '2',
    name: 'Security Audit',
    type: 'Cybersecurity',
    updatedAt: '5 hours ago',
    status: 'in-progress'
  },
  {
    id: '3',
    name: 'Bug Fix #234',
    type: 'Bug Fixer',
    updatedAt: '1 day ago',
    status: 'completed'
  },
  {
    id: '4',
    name: 'React Dashboard',
    type: 'Code Generation',
    updatedAt: '2 days ago',
    status: 'failed'
  }
]

export default function DashboardPage() {
  const [mounted, setMounted] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [isOwner, setIsOwner] = useState(false)
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
    return () => { cancelled = true }
  }, [mounted])

  if (!mounted) return null

  const sidebarItems = [
    { icon: MessageSquare, label: 'Chat', href: '/chat', active: false },
    { icon: Code2, label: 'Code Lab', href: '/chat?mode=code', active: false },
    { icon: Shield, label: 'Security', href: '/chat?mode=security', active: false },
    { icon: Lock, label: 'Vault', href: '/vault', active: false },
    { icon: FolderOpen, label: 'Projects', href: '/projects', active: false },
    { icon: CreditCard, label: 'Upgrade', href: '/pricing', active: false },
    { icon: Settings, label: 'Settings', href: '/settings', active: false },
    // Owner-only: Admin Panel + Use AI toggle. Normal users see neither.
    ...(isOwner
      ? [
          { icon: Shield, label: 'Admin Panel', href: '/admin', active: false },
          { icon: Sparkles, label: 'Use AI', href: '/chat?owner=1', active: false },
        ]
      : []),
  ]

  const getStatusIcon = (status: RecentProject['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />
      case 'in-progress':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />
    }
  }

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
                  className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-gray-800/50 transition-colors group"
                >
                  <item.icon className="w-5 h-5 text-gray-400 group-hover:text-white transition-colors flex-shrink-0" />
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
              <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-gray-800/50 transition-colors cursor-pointer">
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
                  <ChevronRight className={`w-5 h-5 transition-transform ${sidebarOpen ? 'rotate-180' : ''}`} />
                </button>
                <div>
                  <h1 className="text-xl font-bold">Dashboard</h1>
                  <p className="text-sm text-gray-400">Welcome back! Ready to create something amazing?</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                {/* Plan Badge */}
                <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-xl">
                  <Sparkles className="w-4 h-4 text-purple-400" />
                  <span className="text-sm font-medium text-purple-400">PRO Plan</span>
                </div>

                {/* Credits Meter */}
                <div className="hidden md:flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-yellow-500" />
                    <span className="text-sm text-gray-400">847 / 1,000 credits</span>
                  </div>
                  <div className="w-32 h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full" style={{ width: '84.7%' }} />
                  </div>
                </div>

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
                  {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>

                {/* Notifications */}
                <button className="p-2 hover:bg-gray-800 rounded-lg transition-colors relative">
                  <Bell className="w-5 h-5" />
                  <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
                </button>
              </div>
            </div>
          </header>

          {/* Dashboard Content */}
          <div className="p-6">
            {/* Quick Actions */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold mb-4">Quick Actions</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {quickActions.map((action, i) => (
                  <Link
                    key={action.id}
                    href={action.href}
                    className="glass-card p-6 hover:border-blue-500/30 transition-all group"
                  >
                    <div className="flex items-start gap-4">
                      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${action.color} flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform`}>
                        <action.icon className="w-6 h-6 text-white" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold mb-1 group-hover:text-blue-400 transition-colors">{action.title}</h3>
                        <p className="text-sm text-gray-400">{action.description}</p>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-600 group-hover:text-blue-400 transition-colors" />
                    </div>
                  </Link>
                ))}
              </div>
            </section>

            {/* Stats Grid */}
            <section className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              {[
                { label: 'Total Generations', value: '1,234', icon: Zap, color: 'text-yellow-500' },
                { label: 'Projects Created', value: '56', icon: FolderOpen, color: 'text-blue-500' },
                { label: 'Bugs Fixed', value: '89', icon: Bug, color: 'text-green-500' },
                { label: 'Hours Saved', value: '342', icon: Clock, color: 'text-purple-500' }
              ].map((stat, i) => (
                <div key={i} className="glass-card p-6">
                  <div className="flex items-center justify-between mb-2">
                    <stat.icon className={`w-6 h-6 ${stat.color}`} />
                    <TrendingUp className="w-4 h-4 text-green-500" />
                  </div>
                  <div className="text-2xl font-bold mb-1">{stat.value}</div>
                  <div className="text-sm text-gray-400">{stat.label}</div>
                </div>
              ))}
            </section>

            {/* Recent Projects */}
            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold">Recent Projects</h2>
                <Link href="/projects" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
                  View All
                </Link>
              </div>
              <div className="glass-card overflow-hidden">
                <div className="divide-y divide-gray-800/50">
                  {recentProjects.map((project, i) => (
                    <div
                      key={project.id}
                      className="p-4 hover:bg-gray-800/30 transition-colors cursor-pointer group"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          {getStatusIcon(project.status)}
                          <div>
                            <h3 className="font-medium group-hover:text-blue-400 transition-colors">{project.name}</h3>
                            <p className="text-sm text-gray-400">{project.type} • {project.updatedAt}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <button className="p-2 hover:bg-gray-800 rounded-lg transition-colors opacity-0 group-hover:opacity-100">
                            <Copy className="w-4 h-4 text-gray-400" />
                          </button>
                          <button className="p-2 hover:bg-gray-800 rounded-lg transition-colors opacity-0 group-hover:opacity-100">
                            <ExternalLink className="w-4 h-4 text-gray-400" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  )
}