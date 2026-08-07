'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Search, FileText, Link2, Mail, Shield, AlertTriangle, CheckCircle2, XCircle, Loader2, X, ExternalLink } from 'lucide-react'
import { featuresApi } from '@/lib/api'

interface AIDetectivePanelProps {
  onClose: () => void
}

interface AnalysisResult {
  target_type: 'file' | 'link' | 'email'
  target: string
  risk_level: 'safe' | 'low' | 'medium' | 'high' | 'critical'
  findings: string[]
  summary: string
  recommendations: string[]
}

export default function AIDetectivePanel({ onClose }: AIDetectivePanelProps) {
  const [targetType, setTargetType] = useState<'file' | 'link' | 'email'>('link')
  const [target, setTarget] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async () => {
    if (!target.trim()) return
    setLoading(true)
    setError(null)
    try {
      const response = await featuresApi.routeTask({
        task_type: 'ai_detective',
        task_description: `analyze ${targetType}: ${target}`,
      })
      setResult({
        target_type: targetType,
        target,
        risk_level: response.data.risk_level || 'low',
        findings: response.data.findings || ['Analysis completed'],
        summary: response.data.summary || 'No significant issues detected.',
        recommendations: response.data.recommendations || ['Continue monitoring'],
      })
    } catch {
      setError('Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'safe': return 'text-green-400 bg-green-500/10 border-green-500/30'
      case 'low': return 'text-blue-400 bg-blue-500/10 border-blue-500/30'
      case 'medium': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30'
      case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/30'
      case 'critical': return 'text-red-400 bg-red-500/10 border-red-500/30'
      default: return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
    }
  }

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'safe': return <CheckCircle2 className="w-5 h-5" />
      case 'low': return <CheckCircle2 className="w-5 h-5" />
      case 'medium': return <AlertTriangle className="w-5 h-5" />
      case 'high': return <AlertTriangle className="w-5 h-5" />
      case 'critical': return <XCircle className="w-5 h-5" />
      default: return <Shield className="w-5 h-5" />
    }
  }

  const typeIcons = {
    file: <FileText className="w-4 h-4" />,
    link: <Link2 className="w-4 h-4" />,
    email: <Mail className="w-4 h-4" />,
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-yellow-500 to-amber-500 rounded-xl flex items-center justify-center">
            <Search className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">AI Detective</h3>
            <p className="text-xs text-gray-400">Analyze files, links & emails</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      <div className="flex gap-2 mb-4">
        {(['file', 'link', 'email'] as const).map(type => (
          <button
            key={type}
            onClick={() => setTargetType(type)}
            className={`flex-1 p-2 rounded-lg border transition-all flex items-center justify-center gap-2 ${
              targetType === type
                ? 'border-yellow-500/50 bg-yellow-500/10'
                : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
            }`}
          >
            {typeIcons[type]}
            <span className="text-xs text-white capitalize">{type}</span>
          </button>
        ))}
      </div>

      <div className="mb-4">
        <input
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          placeholder={targetType === 'file' ? 'Enter file path or hash...' : targetType === 'link' ? 'Enter URL to analyze...' : 'Enter email address...'}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-yellow-500"
        />
      </div>

      <button
        onClick={handleAnalyze}
        disabled={!target.trim() || loading}
        className="w-full bg-gradient-to-r from-yellow-600 to-amber-600 hover:from-yellow-500 hover:to-amber-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
        {loading ? 'Analyzing...' : 'Analyze'}
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
          className="mt-4 space-y-3"
        >
          <div className={`flex items-center gap-3 p-3 rounded-lg border ${getRiskColor(result.risk_level)}`}>
            {getRiskIcon(result.risk_level)}
            <div>
              <p className="text-sm font-medium capitalize">Risk Level: {result.risk_level}</p>
              <p className="text-xs opacity-80">{result.target_type.toUpperCase()}: {result.target}</p>
            </div>
          </div>

          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
            <h4 className="text-xs font-medium text-gray-400 mb-2">Summary</h4>
            <p className="text-sm text-gray-300">{result.summary}</p>
          </div>

          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
            <h4 className="text-xs font-medium text-gray-400 mb-2">Findings</h4>
            <ul className="space-y-1">
              {result.findings.map((finding, i) => (
                <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                  <span className="text-yellow-400 mt-0.5">•</span>
                  {finding}
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
            <h4 className="text-xs font-medium text-gray-400 mb-2">Recommendations</h4>
            <ul className="space-y-1">
              {result.recommendations.map((rec, i) => (
                <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
