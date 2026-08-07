import type { Metadata } from 'next'
import Link from 'next/link'
import { Download, Monitor, ShieldCheck, Sparkles, Laptop, Smartphone } from 'lucide-react'
import { SITE_URL, HREFLANG_MAP } from '@/lib/seo/locales'

const DOWNLOAD_URL = `${SITE_URL}/download`

export const metadata: Metadata = {
  title: 'Download Professional AI Apps - Android, iOS, Windows, Mac, Linux',
  description:
    'Download Professional AI apps with one click: Android APK, iOS TestFlight/App Store, Windows EXE, macOS DMG, and Linux AppImage.',
  keywords: [
    'professional ai download',
    'ai app download',
    'professional ai apk',
    'professional ai ios',
    'professional ai windows',
    'professional ai mac',
    'professional ai linux',
  ],
  alternates: {
    canonical: DOWNLOAD_URL,
    languages: {
      ...Object.fromEntries(Object.keys(HREFLANG_MAP).map((k) => [k, `${DOWNLOAD_URL}?lang=${k}`])),
      'x-default': DOWNLOAD_URL,
    },
  },
}

const mobileDownloads = [
  {
    os: 'Android',
    file: 'app-release.apk',
    arch: 'ARM64 / x64',
    url: '/downloads/android/app-release.apk',
    playStoreUrl: 'https://play.google.com/store/apps/details?id=com.professionalai.mobile',
  },
  {
    os: 'iOS',
    file: 'TestFlight / App Store',
    arch: 'iPhone / iPad',
    url: 'https://apps.apple.com/app/professional-ai/id000000000',
    testFlightUrl: 'https://testflight.apple.com/join/ABC123',
  },
]

const desktopDownloads = [
  {
    os: 'Windows',
    file: '.exe',
    arch: 'x64 / ARM64',
    url: '/downloads/desktop/Professional-AI-Setup.exe',
  },
  {
    os: 'macOS',
    file: '.dmg',
    arch: 'Apple Silicon / Intel',
    url: '/downloads/desktop/Professional-AI.dmg',
  },
  {
    os: 'Linux',
    file: '.AppImage',
    arch: 'x64',
    url: '/downloads/desktop/Professional-AI.AppImage',
  },
]

export default function DownloadPage() {
  const softwareAppSchema = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'Professional AI',
    operatingSystem: 'Android, iOS, Windows, macOS, Linux',
    applicationCategory: 'BusinessApplication',
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: '5',
      bestRating: '5',
      ratingCount: '2500',
    },
    downloadUrl: [
      ...mobileDownloads.map((item) => item.url),
      ...desktopDownloads.map((item) => item.url),
    ],
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
      availability: 'https://schema.org/InStock',
      url: DOWNLOAD_URL,
    },
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white px-4 py-16">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareAppSchema) }} />
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-300 text-sm mb-6">
            <Laptop className="w-4 h-4" />
            Direct App Downloads
          </div>
          <h1 className="text-5xl font-bold mb-4">Download Professional AI</h1>
          <p className="text-gray-400 max-w-3xl mx-auto text-lg">
            One-click app access for Android, iOS, Windows, macOS, and Linux with full Professional AI experience, offline support, and auto-updates.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-12">
          {mobileDownloads.map((item) => (
            <div id={item.os.toLowerCase()} key={item.os} className="glass-card p-6 border border-gray-800 rounded-2xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-semibold">{item.os}</h2>
                <Smartphone className="w-6 h-6 text-cyan-400" />
              </div>
              <p className="text-gray-400 mb-1">Package: {item.file}</p>
              <p className="text-gray-500 text-sm mb-4">Platform: {item.arch}</p>
              <div className="flex flex-col gap-2">
                <a
                  href={item.url}
                  className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 transition-all font-medium"
                >
                  <Download className="w-4 h-4" />
                  Download {item.os} APK
                </a>
                {item.playStoreUrl && (
                  <a
                    href={item.playStoreUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl border border-gray-700 hover:border-gray-500 transition-all font-medium text-gray-300"
                  >
                    <Download className="w-4 h-4" />
                    Google Play
                  </a>
                )}
                {item.testFlightUrl && (
                  <a
                    href={item.testFlightUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl border border-gray-700 hover:border-gray-500 transition-all font-medium text-gray-300"
                  >
                    <Download className="w-4 h-4" />
                    TestFlight
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {desktopDownloads.map((item) => (
            <div id={item.os.toLowerCase() === 'macos' ? 'mac' : item.os.toLowerCase()} key={item.os} className="glass-card p-6 border border-gray-800 rounded-2xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-semibold">{item.os}</h2>
                <Monitor className="w-6 h-6 text-cyan-400" />
              </div>
              <p className="text-gray-400 mb-1">Installer: {item.file}</p>
              <p className="text-gray-500 text-sm mb-6">Architecture: {item.arch}</p>
              <a
                href={item.url}
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 transition-all font-medium"
              >
                <Download className="w-4 h-4" />
                Download {item.file}
              </a>
            </div>
          ))}
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-10">
          <div className="glass-card p-6 border border-gray-800 rounded-2xl">
            <h3 className="text-xl font-semibold mb-3 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-green-400" />
              Security & Sign-In
            </h3>
            <ul className="text-gray-300 space-y-2 text-sm">
              <li>Google, Microsoft, SSO, GitHub, Apple, and phone OTP login</li>
              <li>Same secure 2FA and passkey flow as web</li>
              <li>Owner mode includes full admin panel access</li>
              <li>Payments and security alerts appear as native notifications</li>
            </ul>
          </div>

          <div className="glass-card p-6 border border-gray-800 rounded-2xl">
            <h3 className="text-xl font-semibold mb-3 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-cyan-400" />
              Offline + Auto-Update
            </h3>
            <ul className="text-gray-300 space-y-2 text-sm">
              <li>Works with on-device Ollama models when internet is down</li>
              <li>Global shortcut quick ask: Ctrl+Shift+P</li>
              <li>System tray icon for instant access</li>
              <li>Silent desktop auto-update checks every 30 minutes</li>
            </ul>
          </div>
        </div>

        <div className="glass-card p-6 border border-gray-800 rounded-2xl text-sm text-gray-400">
          <p className="mb-2">
            <strong className="text-white">Web (PWA):</strong> Open <a href="/" className="text-cyan-400 hover:underline">professionalai.com</a> in your browser and tap "Add to Home Screen" for app-like experience without installation.
          </p>
          <p className="mb-2">
            <strong className="text-white">Mobile vs Desktop vs Web:</strong> Mobile app = native phone experience with offline AI. Desktop app = computer app with tray icon, global shortcut (Ctrl+Shift+P), and auto-updates. Web = browser-only, no install needed, same features and account.
          </p>
          <p>
            Need checksums or enterprise deployment packages? Contact support for signed release metadata and managed rollout channels.
          </p>
          <p className="mt-2">
            Back to pricing: <Link href="/pricing" className="text-cyan-400 hover:text-cyan-300">View Plans</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
