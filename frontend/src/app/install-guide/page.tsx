import type { Metadata } from 'next'
import Link from 'next/link'
import { Download, Smartphone, Monitor, Globe, ChevronRight } from 'lucide-react'

export const metadata: Metadata = {
  title: 'How to Install Professional AI - Android, iOS, Windows, Mac, Linux',
  description: 'Step-by-step installation guide for Professional AI on all platforms. Mobile app, desktop app, and web browser.',
  keywords: [
    'how to install professional ai',
    'professional ai setup guide',
    'install professional ai android',
    'install professional ai ios',
    'install professional ai windows',
    'install professional ai mac',
    'install professional ai linux',
  ],
}

export default function InstallGuidePage() {
  return (
    <div className="min-h-screen bg-gray-950 text-white px-4 py-16">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-300 text-sm mb-6">
            <Monitor className="w-4 h-4" />
            Installation Guide
          </div>
          <h1 className="text-5xl font-bold mb-4">How to Install Professional AI</h1>
          <p className="text-gray-400 max-w-3xl mx-auto text-lg">
            Choose your platform below for step-by-step installation instructions. All platforms share the same account and features.
          </p>
        </div>

        <div className="grid gap-8 mb-12">
          <InstallCard
            icon={<Smartphone className="w-8 h-8 text-green-400" />}
            title="Android Mobile App"
            description="Native Android app with offline AI, 2FA, and all Professional AI features."
            steps={[
              'Download the APK from this page or Google Play Store.',
              'Open the APK file on your Android device.',
              'If prompted, enable "Install from unknown sources" in Settings > Security.',
              'Tap "Install" and wait for the installation to complete.',
              'Open the app and sign in with Google, GitHub, Apple, or Phone.',
              'Complete 2FA and passkey setup (optional but recommended).',
              'Start using Professional AI!',
            ]}
            note="Minimum Android 7.0 (API 24). ARM64 and x64 supported."
          />

          <InstallCard
            icon={<Smartphone className="w-8 h-8 text-gray-300" />}
            title="iOS Mobile App"
            description="Native iOS app for iPhone and iPad with offline AI and passkey support."
            steps={[
              'Open the App Store on your iPhone or iPad.',
              'Search for "Professional AI" or use the TestFlight link.',
              'Tap "Get" or "Install" to download the app.',
              'Open the app and sign in with Apple, Google, or Phone.',
              'Complete 2FA and Face ID / passkey setup (optional).',
              'Start using Professional AI!',
            ]}
            note="Minimum iOS 15.0. iPhone and iPad supported. TestFlight available for beta testing."
          />

          <InstallCard
            icon={<Monitor className="w-8 h-8 text-blue-400" />}
            title="Windows Desktop App"
            description="Windows desktop app with tray icon, global shortcut (Ctrl+Shift+P), and auto-updates."
            steps={[
              'Download ProfessionalAI-Setup.exe from this page.',
              'Double-click the installer file.',
              'Follow the installation wizard: click "Next", accept terms, choose install location.',
              'Click "Install" and wait for completion.',
              'Click "Finish" to launch the app.',
              'Sign in with your Professional AI account.',
              'Access quick-ask anytime with Ctrl+Shift+P.',
            ]}
            note="Windows 10/11 (x64 and ARM64). Requires ~200MB disk space."
          />

          <InstallCard
            icon={<Monitor className="w-8 h-8 text-gray-300" />}
            title="macOS Desktop App"
            description="macOS desktop app with tray icon, global shortcut, and auto-updates."
            steps={[
              'Download ProfessionalAI.dmg from this page.',
              'Double-click the DMG file to open it.',
              'Drag the Professional AI icon to the Applications folder.',
              'Open Applications and double-click Professional AI.',
              'If prompted, allow the app in System Settings > Privacy & Security.',
              'Sign in with your Professional AI account.',
              'Access quick-ask anytime with Cmd+Shift+P.',
            ]}
            note="macOS 12.0+ (Monterey). Apple Silicon and Intel supported."
          />

          <InstallCard
            icon={<Monitor className="w-8 h-8 text-orange-400" />}
            title="Linux Desktop App"
            description="Linux desktop AppImage with offline support and global shortcuts."
            steps={[
              'Download ProfessionalAI.AppImage from this page.',
              'Open terminal and navigate to the download folder.',
              'Make the AppImage executable: chmod +x ProfessionalAI.AppImage',
              'Double-click the AppImage or run: ./ProfessionalAI.AppImage',
              'Sign in with your Professional AI account.',
              'Create a desktop shortcut for easy access.',
            ]}
            note="Ubuntu 20.04+, Fedora 35+, or any modern Linux distribution. x64 only."
          />

          <InstallCard
            icon={<Globe className="w-8 h-8 text-cyan-400" />}
            title="Web Browser (PWA)"
            description="No installation needed. Use Professional AI directly in your browser."
            steps={[
              'Go to https://professionalai.com in your browser.',
              'Sign in with your account.',
              'For app-like experience: click the install icon in the address bar.',
              'Or: Menu > "Add to Home Screen" (mobile) / "Install App" (desktop).',
              'The PWA works offline and syncs when you reconnect.',
            ]}
            note="Chrome, Edge, Safari, Firefox supported. PWA available on all devices."
          />
        </div>

        <div className="glass-card p-8 border border-gray-800 rounded-2xl">
          <h2 className="text-2xl font-bold mb-4">One Account, All Platforms</h2>
          <p className="text-gray-400 mb-4">
            Your Professional AI account works across mobile, desktop, and web. Sign in once and access your chats, code projects, vault, and settings from any device. All data is synced securely in real-time.
          </p>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-900 rounded-xl">
              <h3 className="font-semibold text-green-400 mb-2">Mobile App</h3>
              <p className="text-sm text-gray-400">Native app for Android and iOS. Offline AI, 2FA, passkey, notifications.</p>
            </div>
            <div className="p-4 bg-gray-900 rounded-xl">
              <h3 className="font-semibold text-blue-400 mb-2">Desktop App</h3>
              <p className="text-sm text-gray-400">Electron app for Windows, Mac, Linux. Tray icon, global shortcut, auto-updates.</p>
            </div>
            <div className="p-4 bg-gray-900 rounded-xl">
              <h3 className="font-semibold text-cyan-400 mb-2">Web (PWA)</h3>
              <p className="text-sm text-gray-400">Browser-based. No install needed. Add to home screen for app-like experience.</p>
            </div>
          </div>
          <div className="mt-6">
            <Link href="/download" className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 transition-all font-medium">
              <Download className="w-4 h-4" />
              Download Now
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

function InstallCard({ icon, title, description, steps, note }: {
  icon: React.ReactNode
  title: string
  description: string
  steps: string[]
  note: string
}) {
  return (
    <div className="glass-card p-8 border border-gray-800 rounded-2xl">
      <div className="flex items-start gap-4 mb-4">
        <div className="p-3 bg-gray-900 rounded-xl">{icon}</div>
        <div>
          <h2 className="text-2xl font-bold">{title}</h2>
          <p className="text-gray-400 mt-1">{description}</p>
        </div>
      </div>
      <ol className="space-y-3 mb-4">
        {steps.map((step, index) => (
          <li key={index} className="flex items-start gap-3">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-sm font-bold">
              {index + 1}
            </span>
            <span className="text-gray-300 pt-0.5">{step}</span>
          </li>
        ))}
      </ol>
      <div className="p-3 bg-gray-900 rounded-lg">
        <p className="text-sm text-gray-400">
          <strong className="text-gray-300">Note:</strong> {note}
        </p>
      </div>
    </div>
  )
}
