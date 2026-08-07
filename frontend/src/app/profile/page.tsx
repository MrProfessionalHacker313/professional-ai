'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { User, CreditCard, Shield, Bell, Moon, Sun, Globe, Save } from 'lucide-react'
import { useTheme } from '@/components/ThemeProvider'
import { useLanguage } from '@/components/LanguageProvider'
import Link from 'next/link'

export default function ProfilePage() {
  const [mounted, setMounted] = useState(false)
  const { theme, setTheme } = useTheme()
  const { language, setLanguage } = useLanguage()
  const [name, setName] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => { setMounted(true) }, [])

  if (!mounted) return null

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold">Profile Settings</h1>
          <Link href="/dashboard" className="text-sm text-gray-400 hover:text-white">Back to Dashboard</Link>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 mb-6"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold">
              {name ? name[0].toUpperCase() : 'U'}
            </div>
            <div>
              <h2 className="text-xl font-semibold">{name || 'User'}</h2>
              <p className="text-sm text-gray-400">Free Plan</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Display Name</label>
              <div className="relative">
                <User className="absolute left-3 top-3 w-5 h-5 text-gray-500" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-10 py-2.5 text-sm focus:outline-none focus:border-blue-500"
                  placeholder="Your name"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Language</label>
              <div className="relative">
                <Globe className="absolute left-3 top-3 w-5 h-5 text-gray-500" />
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value as any)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-10 py-2.5 text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="en">English</option>
                  <option value="ur">Urdu</option>
                  <option value="ar">Arabic</option>
                  <option value="hi">Hindi</option>
                  <option value="bn">Bengali</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Theme</label>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setTheme('light')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl border ${theme === 'light' ? 'border-blue-500 bg-blue-500/10' : 'border-gray-700'}`}
                >
                  <Sun className="w-4 h-4" /> Light
                </button>
                <button
                  onClick={() => setTheme('dark')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl border ${theme === 'dark' ? 'border-blue-500 bg-blue-500/10' : 'border-gray-700'}`}
                >
                  <Moon className="w-4 h-4" /> Dark
                </button>
              </div>
            </div>
          </div>

          <div className="mt-6 flex items-center gap-3">
            <button
              onClick={handleSave}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-6 py-2.5 rounded-xl font-medium transition-all flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              {saved ? 'Saved!' : 'Save Changes'}
            </button>
            <Link href="/pricing" className="flex items-center gap-2 px-6 py-2.5 rounded-xl border border-gray-700 hover:border-gray-500 text-sm">
              <CreditCard className="w-4 h-4" />
              Upgrade Plan
            </Link>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6"
        >
          <h3 className="font-semibold mb-2 flex items-center gap-2">
            <Shield className="w-5 h-5 text-green-400" />
            Security
          </h3>
          <p className="text-sm text-gray-400">Your data is encrypted with AES-256-GCM. Enable 2FA for extra protection.</p>
        </motion.div>
      </div>
    </div>
  )
}
