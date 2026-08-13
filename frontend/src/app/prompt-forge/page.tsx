'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Wand2, Copy, Check, Lightbulb, ChevronRight, Sparkles, Loader2 } from 'lucide-react'
import { featuresApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface GeneratedResult {
  prompt: string
  category: string
  target_ai: string
  tone: string
  complexity: string
  tips: string[]
  follow_up_prompts: string[]
}

const CATEGORIES = [
  { id: 'coding', name: 'Coding / Software', icon: 'Code2' },
  { id: 'hacking', name: 'Security Testing', icon: 'Shield' },
  { id: 'security', name: 'Cybersecurity', icon: 'Shield' },
  { id: 'malware_analysis', name: 'Malware Analysis', icon: 'Bug' },
  { id: 'automation', name: 'Automation Scripts', icon: 'Zap' },
  { id: 'general', name: 'General / Cross-Domain', icon: 'Sparkles' },
]

const TARGETS = [
  { id: 'chatgpt', name: 'ChatGPT / GPT-4' },
  { id: 'claude', name: 'Claude / Anthropic' },
  { id: 'gemini', name: 'Gemini / Google' },
  { id: 'llama', name: 'Llama / Open Source' },
  { id: 'any', name: 'Any AI / Universal' },
]

const TONES = [
  { id: 'academic', name: 'Academic' },
  { id: 'technical', name: 'Technical' },
  { id: 'educational', name: 'Educational' },
  { id: 'professional', name: 'Professional' },
  { id: 'beginner-friendly', name: 'Beginner Friendly' },
  { id: 'certification-prep', name: 'Certification Prep' },
]

const COMPLEXITIES = [
  { id: 'beginner', name: 'Beginner' },
  { id: 'intermediate', name: 'Intermediate' },
  { id: 'advanced', name: 'Advanced' },
  { id: 'expert', name: 'Expert' },
  { id: 'comprehensive', name: 'Comprehensive (All Levels)' },
]

const EXAMPLES = [
  { name: 'Python Web Scraper', category: 'coding', target_ai: 'any', tone: 'technical', complexity: 'intermediate', topic: 'Build a production-grade web scraper in Python' },
  { name: 'Network Pen Test', category: 'hacking', target_ai: 'any', tone: 'professional', complexity: 'advanced', topic: 'Conduct an authorized network penetration test' },
  { name: 'Malware Analysis', category: 'malware_analysis', target_ai: 'any', tone: 'academic', complexity: 'advanced', topic: 'Analyze malware behavior in a sandboxed environment' },
  { name: 'CI/CD Automation', category: 'automation', target_ai: 'any', tone: 'professional', complexity: 'intermediate', topic: 'Automate a complete CI/CD deployment pipeline' },
  { name: 'Security Audit Report', category: 'security', target_ai: 'any', tone: 'academic', complexity: 'advanced', topic: 'Generate a comprehensive security audit report' },
]

export default function PromptForgePage() {
  const [category, setCategory] = useState('coding')
  const [targetAi, setTargetAi] = useState('any')
  const [tone, setTone] = useState('technical')
  const [complexity, setComplexity] = useState('intermediate')
  const [topic, setTopic] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<GeneratedResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copiedPrompt, setCopiedPrompt] = useState(false)
  const [copiedTip, setCopiedTip] = useState<string | null>(null)
  const [showExamples, setShowExamples] = useState(false)

  const handleGenerate = async () => {
    if (!topic.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const response = await featuresApi.generatePrompt({
        topic: topic.trim(),
        category,
        target_ai: targetAi,
        tone,
        complexity,
      })
      setResult(response.data)
    } catch {
      setError('Failed to generate prompt. Please try again.')
      toast.error('Prompt generation failed')
    } finally {
      setLoading(false)
    }
  }

  const loadExample = (example: typeof EXAMPLES[0]) => {
    setCategory(example.category)
    setTargetAi(example.target_ai)
    setTone(example.tone)
    setComplexity(example.complexity)
    setTopic(example.topic)
    setShowExamples(false)
  }

  const copyToClipboard = async (text: string, type: 'prompt' | 'tip', id?: string) => {
    try {
      await navigator.clipboard.writeText(text)
      if (type === 'prompt') {
        setCopiedPrompt(true)
        setTimeout(() => setCopiedPrompt(false), 2000)
        toast.success('Prompt copied to clipboard')
      } else if (id) {
        setCopiedTip(id)
        setTimeout(() => setCopiedTip(null), 2000)
      }
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
      toast.error('Failed to copy to clipboard')
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl flex items-center justify-center">
            <Wand2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Prompt Forge</h1>
            <p className="text-sm text-gray-400">Generate advanced prompts engineered to work with any AI</p>
          </div>
        </div>

        <div className="glass-card p-6 mb-6">
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500"
              >
                {CATEGORIES.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Target AI</label>
              <select
                value={targetAi}
                onChange={(e) => setTargetAi(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500"
              >
                {TARGETS.map(t => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Tone</label>
              <select
                value={tone}
                onChange={(e) => setTone(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500"
              >
                {TONES.map(t => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Complexity</label>
              <select
                value={complexity}
                onChange={(e) => setComplexity(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500"
              >
                {COMPLEXITIES.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="mb-4">
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs text-gray-400 block">Topic / Task Description</label>
              <button
                onClick={() => setShowExamples(!showExamples)}
                className="text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1"
              >
                <Lightbulb className="w-3 h-3" />
                {showExamples ? 'Hide Examples' : 'Show Examples'}
              </button>
            </div>
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Describe what you want the AI to do... Be specific for best results."
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm text-white resize-none focus:outline-none focus:border-amber-500"
              rows={3}
            />
          </div>

          {showExamples && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mb-4 bg-gray-800/50 border border-gray-700 rounded-lg p-3"
            >
              <p className="text-xs text-gray-400 mb-2">Quick examples:</p>
              <div className="flex flex-wrap gap-2">
                {EXAMPLES.map((ex, i) => (
                  <button
                    key={i}
                    onClick={() => loadExample(ex)}
                    className="text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    {ex.name}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          <button
            onClick={handleGenerate}
            disabled={!topic.trim() || loading}
            className="w-full bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
            {loading ? 'Forging Prompt...' : 'Generate Prompt'}
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
              className="mt-4 space-y-4"
            >
              <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Wand2 className="w-4 h-4 text-amber-400" />
                    <span className="text-sm font-medium text-white">Generated Prompt</span>
                  </div>
                  <button
                    onClick={() => copyToClipboard(result.prompt, 'prompt')}
                    className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors"
                  >
                    {copiedPrompt ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    {copiedPrompt ? 'Copied!' : 'Copy Prompt'}
                  </button>
                </div>
                <div className="bg-gray-900/50 rounded-lg p-3 max-h-80 overflow-y-auto">
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono">{result.prompt}</pre>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Lightbulb className="w-4 h-4 text-yellow-400" />
                    <span className="text-xs font-medium text-gray-400">PRO TIPS</span>
                  </div>
                  <div className="space-y-2">
                    {result.tips.map((tip, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <ChevronRight className="w-3 h-3 text-yellow-500 mt-0.5 flex-shrink-0" />
                        <p className="text-xs text-gray-300">{tip}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="w-4 h-4 text-purple-400" />
                    <span className="text-xs font-medium text-gray-400">FOLLOW-UP PROMPTS</span>
                  </div>
                  <div className="space-y-2">
                    {result.follow_up_prompts.map((fp, i) => (
                      <button
                        key={i}
                        onClick={() => copyToClipboard(fp, 'tip', `followup-${i}`)}
                        className="w-full text-left flex items-start gap-2 p-2 bg-gray-900/50 rounded-lg hover:bg-gray-900 transition-colors"
                      >
                        <ChevronRight className="w-3 h-3 text-purple-500 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <p className="text-xs text-gray-300 line-clamp-2">{fp}</p>
                        </div>
                        {copiedTip === `followup-${i}` && <Check className="w-3 h-3 text-green-400 flex-shrink-0" />}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}
