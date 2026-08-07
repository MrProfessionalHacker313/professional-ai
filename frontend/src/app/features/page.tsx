import type { Metadata } from 'next'
import Link from 'next/link'
import { Shield, Code2, Globe, Download } from 'lucide-react'
import { SITE_URL, HREFLANG_MAP } from '@/lib/seo/locales'

export const metadata: Metadata = {
  title: 'Professional AI Features - AI Coding Tool, Security Assistant, Multilingual Chat',
  description:
    'Explore Professional AI features for coding, cybersecurity assistance, multilingual chat in 40+ languages, and app downloads.',
  keywords: [
    'professional ai features',
    'ai coding tool',
    'ai security assistant',
    'ai in urdu',
    'ai in hindi',
    'free ai chatbot',
  ],
  alternates: {
    canonical: `${SITE_URL}/features`,
    languages: {
      ...Object.fromEntries(Object.entries(HREFLANG_MAP).map(([k, v]) => [k, `${SITE_URL}/features?lang=${k}`])),
      'x-default': `${SITE_URL}/features`,
    },
  },
}

export default function FeaturesPage() {
  const cards = [
    {
      title: 'AI Coding Tool',
      desc: 'Generate production-ready code, debug issues, and ship faster with structured AI workflows.',
      icon: Code2,
    },
    {
      title: 'AI Security Assistant',
      desc: 'Get security-focused guidance and practical hardening support for modern apps and APIs.',
      icon: Shield,
    },
    {
      title: 'Multilingual AI',
      desc: 'Native responses in Urdu, Hindi, Arabic, Bengali, and 40+ languages for global teams.',
      icon: Globe,
    },
  ]

  return (
    <div className="min-h-screen bg-gray-950 text-white px-4 py-16">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-5xl font-bold mb-6">Professional AI Features</h1>
        <p className="text-gray-400 text-lg mb-12 max-w-3xl">
          Built for creators, developers, and security teams looking for reliable AI in daily production workflows.
        </p>

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {cards.map((card) => (
            <div key={card.title} className="glass-card p-6 rounded-2xl border border-gray-800">
              <card.icon className="w-7 h-7 text-cyan-400 mb-4" />
              <h2 className="text-2xl font-semibold mb-3">{card.title}</h2>
              <p className="text-gray-400">{card.desc}</p>
            </div>
          ))}
        </div>

        <Link
          href="/download"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 font-medium"
        >
          <Download className="w-4 h-4" />
          Download Apps
        </Link>
      </div>
    </div>
  )
}
