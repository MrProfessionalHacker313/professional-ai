'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Languages, Globe, Copy, Check, Loader2, X, Volume2 } from 'lucide-react'
import { featuresApi } from '@/lib/api'

interface LanguageBrainPanelProps {
  onClose: () => void
}

interface LanguageResult {
  detected_language: string
  confidence: number
  original_text: string
  translated_text: string
  source_lang: string
  target_lang: string
}

export default function LanguageBrainPanel({ onClose }: LanguageBrainPanelProps) {
  const [text, setText] = useState('')
  const [sourceLang, setSourceLang] = useState('auto')
  const [targetLang, setTargetLang] = useState('en')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<LanguageResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const languages = [
    { value: 'auto', label: 'Auto Detect' },
    { value: 'en', label: 'English' },
    { value: 'ur', label: 'Urdu' },
    { value: 'ar', label: 'Arabic' },
    { value: 'hi', label: 'Hindi' },
    { value: 'bn', label: 'Bengali' },
    { value: 'es', label: 'Spanish' },
    { value: 'fr', label: 'French' },
    { value: 'de', label: 'German' },
    { value: 'zh', label: 'Chinese' },
    { value: 'ja', label: 'Japanese' },
    { value: 'ko', label: 'Korean' },
    { value: 'pt', label: 'Portuguese' },
    { value: 'ru', label: 'Russian' },
  ]

  const handleTranslate = async () => {
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    try {
      const response = await featuresApi.translate({
        text,
        source_lang: sourceLang,
        target_lang: targetLang,
        context_type: 'general',
      })
      setResult(response.data)
    } catch (err) {
      setError('Translation failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    if (result?.translated_text) {
      navigator.clipboard.writeText(result.translated_text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
            <Languages className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Language Brain</h3>
            <p className="text-xs text-gray-400">Detect & auto-translate any language</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Source Language</label>
          <select
            value={sourceLang}
            onChange={(e) => setSourceLang(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            {languages.map(lang => (
              <option key={lang.value} value={lang.value}>{lang.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Target Language</label>
          <select
            value={targetLang}
            onChange={(e) => setTargetLang(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            {languages.filter(l => l.value !== 'auto').map(lang => (
              <option key={lang.value} value={lang.value}>{lang.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="mb-4">
        <label className="text-xs text-gray-400 mb-1 block">Text to Translate</label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter text to translate..."
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm text-white resize-none focus:outline-none focus:border-blue-500"
          rows={4}
        />
      </div>

      <button
        onClick={handleTranslate}
        disabled={!text.trim() || loading}
        className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Globe className="w-4 h-4" />}
        {loading ? 'Translating...' : 'Translate'}
      </button>

      {error && (
        <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-lg p-3">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {result && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 bg-gray-800/50 border border-gray-700 rounded-xl p-4"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">Detected:</span>
              <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full">
                {result.detected_language} ({(result.confidence * 100).toFixed(0)}%)
              </span>
            </div>
            <button onClick={handleCopy} className="p-1.5 hover:bg-gray-700 rounded-lg transition-colors">
              {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4 text-gray-400" />}
            </button>
          </div>
          <div className="bg-gray-900/50 rounded-lg p-3">
            <p className="text-sm text-white whitespace-pre-wrap">{result.translated_text}</p>
          </div>
          <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
            <Volume2 className="w-3 h-3" />
            <span>{result.source_lang} → {result.target_lang}</span>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
