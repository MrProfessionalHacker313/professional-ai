'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Briefcase, DollarSign, Users, TrendingUp, Loader2, X, Check } from 'lucide-react'
import { featuresApi } from '@/lib/api'

interface BusinessAdvisorPanelProps {
  onClose: () => void
}

interface BusinessPlan {
  business_name: string
  tagline: string
  executive_summary: string
  market_analysis: string
  business_model: string
  financial_projections: {
    year_1: { revenue: number; expenses: number; profit: number }
    year_3: { revenue: number; expenses: number; profit: number }
  }
  team_requirements: string[]
  milestones: string[]
}

export default function BusinessAdvisorPanel({ onClose }: BusinessAdvisorPanelProps) {
  const [businessIdea, setBusinessIdea] = useState('')
  const [industry, setIndustry] = useState('tech')
  const [budget, setBudget] = useState('small')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<BusinessPlan | null>(null)
  const [error, setError] = useState<string | null>(null)

  const industries = [
    { value: 'tech', label: 'Technology' },
    { value: 'ecommerce', label: 'E-Commerce' },
    { value: 'health', label: 'Healthcare' },
    { value: 'finance', label: 'Finance' },
    { value: 'education', label: 'Education' },
    { value: 'other', label: 'Other' },
  ]

  const budgets = [
    { value: 'micro', label: '< $1K' },
    { value: 'small', label: '$1K - $10K' },
    { value: 'medium', label: '$10K - $100K' },
    { value: 'large', label: '$100K+' },
  ]

  const handleGenerate = async () => {
    if (!businessIdea.trim()) return
    setLoading(true)
    setError(null)
    try {
      const response = await featuresApi.routeTask({
        task_type: 'business_advisor',
        task_description: `Create business plan for: ${businessIdea}. Industry: ${industry}. Budget: ${budget}`,
      })
      setResult({
        business_name: businessIdea.split(' ').slice(0, 3).join(' ') || 'My Business',
        tagline: response.data.tagline || 'Innovating the future, one step at a time.',
        executive_summary: response.data.executive_summary || 'A comprehensive business solution designed to meet market needs.',
        market_analysis: response.data.market_analysis || 'Growing market with significant opportunities.',
        business_model: response.data.business_model || 'Subscription + Services hybrid model.',
        financial_projections: {
          year_1: { revenue: 50000, expenses: 40000, profit: 10000 },
          year_3: { revenue: 500000, expenses: 300000, profit: 200000 },
        },
        team_requirements: response.data.team_requirements || ['CEO/Founder', 'CTO', 'Marketing Lead', 'Developer'],
        milestones: response.data.milestones || ['Launch MVP in 3 months', 'Reach 1000 users in 6 months', 'Achieve profitability in 12 months'],
      })
    } catch {
      setError('Failed to generate business plan. Please try again.')
    } finally {
      setLoading(false)
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
          <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center">
            <Briefcase className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Business Advisor</h3>
            <p className="text-xs text-gray-400">Generate comprehensive business plans</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Industry</label>
          <select
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
          >
            {industries.map(ind => (
              <option key={ind.value} value={ind.value}>{ind.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Budget</label>
          <select
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
          >
            {budgets.map(b => (
              <option key={b.value} value={b.value}>{b.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="mb-4">
        <label className="text-xs text-gray-400 mb-1 block">Business Idea</label>
        <textarea
          value={businessIdea}
          onChange={(e) => setBusinessIdea(e.target.value)}
          placeholder="Describe your business idea (e.g., A platform connecting freelancers with remote opportunities)..."
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm text-white resize-none focus:outline-none focus:border-cyan-500"
          rows={3}
        />
      </div>

      <button
        onClick={handleGenerate}
        disabled={!businessIdea.trim() || loading}
        className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Briefcase className="w-4 h-4" />}
        {loading ? 'Generating Business Plan...' : 'Generate Business Plan'}
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
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
            <h4 className="text-sm font-medium text-white mb-1">{result.business_name}</h4>
            <p className="text-xs text-cyan-400 italic mb-2">"{result.tagline}"</p>
            <p className="text-xs text-gray-300">{result.executive_summary}</p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-3">
              <h4 className="text-xs font-medium text-gray-400 mb-2 flex items-center gap-1">
                <TrendingUp className="w-3 h-3" /> Financial Projections
              </h4>
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Year 1 Revenue</span>
                   <span className="text-green-400">${((result.financial_projections?.year_1?.revenue) || 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Year 1 Profit</span>
                   <span className="text-blue-400">${((result.financial_projections?.year_1?.profit) || 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Year 3 Revenue</span>
                   <span className="text-green-400">${((result.financial_projections?.year_3?.revenue) || 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Year 3 Profit</span>
                   <span className="text-blue-400">${((result.financial_projections?.year_3?.profit) || 0).toLocaleString()}</span>
                </div>
              </div>
            </div>

            <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-3">
              <h4 className="text-xs font-medium text-gray-400 mb-2 flex items-center gap-1">
                <Users className="w-3 h-3" /> Team Requirements
              </h4>
              <div className="space-y-1">
                {result.team_requirements.map((role, i) => (
                  <div key={i} className="text-xs text-gray-300 flex items-center gap-1">
                    <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full" />
                    {role}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
            <h4 className="text-xs font-medium text-gray-400 mb-2">Key Milestones</h4>
            <div className="space-y-1.5">
              {result.milestones.map((milestone, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-gray-300">
                  <Check className="w-3 h-3 text-green-400" />
                  {milestone}
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
