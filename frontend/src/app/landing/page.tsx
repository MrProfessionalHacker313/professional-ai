import Link from 'next/link'
import {
  MessageSquare,
  Code2,
  Image,
  Video,
  Mic,
  Wand2,
  WifiOff,
  ArrowRight,
  Sparkles,
  Star,
  Users,
  TrendingUp,
  Download,
  ChevronRight,
  CheckCircle2,
} from 'lucide-react'
import { LANDING_SHARE_DOMAIN, LANDING_OG_IMAGE } from '@/lib/landing-config'

export const metadata = {
  title: 'Professional AI Landing — AI Chat, Code, Images, Video, Voice & Offline Mode',
  description: 'Experience Professional AI: multilingual chat, code generation, image & video creation, voice AI, Prompt Forge, and full offline mode. Try now for free.',
  keywords: [
    'professional ai landing',
    'ai chat',
    'ai code generation',
    'ai image generator',
    'ai video generator',
    'voice ai',
    'prompt forge',
    'offline ai',
    'free ai assistant',
  ],
  alternates: {
    canonical: `${LANDING_SHARE_DOMAIN}/landing`,
  },
  openGraph: {
    title: 'Professional AI — AI Chat, Code, Images, Video, Voice & Offline Mode',
    description: 'All-in-one AI platform with chat, code generation, image & video creation, voice AI, Prompt Forge, and offline mode. Try free.',
    type: 'website',
    url: `${LANDING_SHARE_DOMAIN}/landing`,
    siteName: 'Professional AI',
    images: [
      {
        url: LANDING_OG_IMAGE,
        width: 1200,
        height: 630,
        alt: 'Professional AI Landing — AI Chat, Code, Images, Video, Voice & Offline Mode',
      },
    ],
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Professional AI — AI Chat, Code, Images, Video, Voice & Offline Mode',
    description: 'All-in-one AI platform with chat, code generation, image & video creation, voice AI, Prompt Forge, and offline mode. Try free.',
    images: [LANDING_OG_IMAGE],
  },
  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
}

const features = [
  {
    id: 'chat',
    title: 'AI Chat',
    description: 'Multilingual conversational AI that understands context, remembers history, and responds in 40+ languages with native fluency.',
    icon: MessageSquare,
    color: 'from-blue-500 to-cyan-500',
    details: ['Context-aware responses', '40+ languages', 'History memory'],
  },
  {
    id: 'code',
    title: 'Code Generation',
    description: 'Generate production-ready code in 35+ languages with built-in security best practices, debugging, and optimization.',
    icon: Code2,
    color: 'from-purple-500 to-indigo-500',
    details: ['35+ languages', 'Security built-in', 'Instant debugging'],
  },
  {
    id: 'image',
    title: 'Image Generation',
    description: 'Create stunning visuals, artwork, and designs with AI. From concept to high-resolution output in seconds.',
    icon: Image,
    color: 'from-pink-500 to-rose-500',
    details: ['8K quality output', 'Style transfer', 'Batch generation'],
  },
  {
    id: 'video',
    title: 'Video Generation',
    description: 'Generate videos, animations, and clips with AI-powered editing, voice-over synthesis, and auto-captions.',
    icon: Video,
    color: 'from-orange-500 to-red-500',
    details: ['AI editing', 'Voice-over sync', 'Auto captions'],
  },
  {
    id: 'voice',
    title: 'Voice AI',
    description: 'Speak naturally to AI and get lifelike voice responses. Multiple languages, tones, and real-time streaming.',
    icon: Mic,
    color: 'from-teal-500 to-emerald-500',
    details: ['Natural speech', 'Multi-language', 'Real-time streaming'],
  },
  {
    id: 'prompt-forge',
    title: 'Prompt Forge',
    description: 'Craft, refine, and optimize prompts with AI assistance. Get better results from any AI model with structured prompt engineering.',
    icon: Wand2,
    color: 'from-amber-500 to-yellow-500',
    details: ['AI-assisted crafting', 'Template library', 'Optimization scores'],
  },
  {
    id: 'offline',
    title: 'Offline Mode',
    description: 'Full AI power without internet. Local coding, search, login, and knowledge base work entirely on-device.',
    icon: WifiOff,
    color: 'from-gray-500 to-slate-500',
    details: ['No internet needed', 'Local AI engine', 'Auto-sync when online'],
  },
]

const stats = [
  { label: 'Active Users', value: '10,000+' },
  { label: 'AI Generations', value: '1M+' },
  { label: 'Rating', value: '5.0' },
  { label: 'Languages', value: '40+' },
]

export default function LandingPage() {
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
              <Link
                href="/"
                className="text-gray-400 hover:text-white transition-colors px-4 py-2 text-sm"
              >
                Home
              </Link>
              <Link
                href="/features"
                className="text-gray-400 hover:text-white transition-colors px-4 py-2 text-sm"
              >
                Features
              </Link>
              <Link
                href="/pricing"
                className="text-gray-400 hover:text-white transition-colors px-4 py-2 text-sm"
              >
                Pricing
              </Link>
              <Link
                href="/login?tab=register"
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-6 py-2 rounded-xl font-medium transition-all glow text-sm"
              >
                Try Now
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-6xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-6">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-blue-400">World&apos;s Most Powerful AI Assistant</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            Code. Create. Secure.{' '}
            <span className="text-gradient">All in One AI.</span>
          </h1>

          <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
            Professional AI is the ultimate all-in-one AI platform. Chat, generate code,
            create images and videos, speak with voice AI, forge perfect prompts, and work fully offline —
            all from one place.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/login?tab=register"
              className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all glow"
            >
              Try Now
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/features"
              className="inline-flex items-center gap-2 border border-gray-700 hover:border-gray-500 text-gray-300 px-8 py-4 rounded-xl font-semibold text-lg transition-all"
            >
              Explore Features
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
              From chat to code, images to video, voice to offline mode —
              Professional AI has every tool you need.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, i) => (
              <div
                key={feature.id}
                className="relative glass-card p-8 group"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold mb-3 group-hover:text-blue-400 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-gray-400 mb-6">{feature.description}</p>
                <ul className="space-y-2 mb-6">
                  {feature.details.map((detail) => (
                    <li key={detail} className="flex items-center gap-2 text-sm text-gray-300">
                      <CheckCircle2 className="w-4 h-4 text-green-400" />
                      {detail}
                    </li>
                  ))}
                </ul>
              </div>
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
                <div className="text-4xl font-bold mb-2 text-gradient">{stat.value}</div>
                <div className="text-sm text-gray-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="glass-card p-12 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10" />
            <div className="relative z-10">
              <Sparkles className="w-12 h-12 text-blue-400 mx-auto mb-4" />
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Ready to Get Started?
              </h2>
              <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
                Join thousands of professionals already using Professional AI.
                Start your free trial today — no credit card required.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link
                  href="/login?tab=register"
                  className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all glow"
                >
                  Try Now <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  href="/pricing"
                  className="inline-flex items-center gap-2 border border-gray-700 hover:border-gray-500 text-gray-300 px-8 py-4 rounded-xl font-semibold text-lg transition-all"
                >
                  View Pricing <ChevronRight className="w-5 h-5" />
                </Link>
              </div>
            </div>
          </div>
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
