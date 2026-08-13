'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Activity,
  Server,
  DollarSign,
  Zap,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  TrendingUp,
  Cpu,
  Globe,
  Loader2,
} from 'lucide-react'
import { featuresApi } from '@/lib/api'

interface ProviderInfo {
  provider: string
  name: string
  status: string
  healthy: boolean
  model: string
  code_model: string
  keys_configured: number
  current_key_index: number
  consecutive_failures: number
  avg_response_time_ms: number
  cost_per_1k_input: number
  cost_per_1k_output: number
  rate_limit_rpm: number
  max_tokens: number
  features: string[]
  total_calls: number
  success_rate: number
  total_cost_usd: number
}

interface DashboardData {
  mode: string
  active_provider: string | null
  providers: Record<string, ProviderInfo>
  cost_summary: {
    total_cost_usd: number
    total_calls: number
    avg_cost_per_call: number
    period_days: number
  }
  local_fallback: {
    status: string
    engine: string
    onnx_available: boolean
  }
  recent_calls: any[]
}

const PROVIDER_COLORS: Record<string, string> = {
  openai: 'bg-emerald-500',
  anthropic: 'bg-orange-500',
  gemini: 'bg-blue-500',
  groq: 'bg-purple-500',
  deepseek: 'bg-cyan-500',
  mistral: 'bg-orange-400',
  openrouter: 'bg-gray-500',
  together: 'bg-indigo-500',
  xai: 'bg-yellow-500',
  stability: 'bg-pink-500',
}

export default function AIDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState(7)

  const fetchDashboard = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await featuresApi.getAIDashboard(days)
      setData(res.data)
    } catch (err) {
      setError('Failed to load AI dashboard')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
    const interval = setInterval(fetchDashboard, 30000)
    return () => clearInterval(interval)
  }, [days])

  const getStatusBadge = (status: string, healthy: boolean) => {
    if (status === 'skipped') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-gray-500/20 text-gray-400">
          <AlertTriangle className="w-3 h-3" />
          Skipped
        </span>
      )
    }
    if (healthy) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-green-500/20 text-green-400">
          <CheckCircle2 className="w-3 h-3" />
          Healthy
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-red-500/20 text-red-400">
        <XCircle className="w-3 h-3" />
        Down
      </span>
    )
  }

  if (loading && !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          <p className="text-gray-400">Loading AI Dashboard...</p>
        </div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={fetchDashboard}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <Activity className="w-8 h-8 text-blue-500" />
              AI Provider Dashboard
            </h1>
            <p className="text-gray-400 mt-1">
              Monitor {data?.providers ? Object.keys(data.providers).length : 0} AI providers, costs, and health status
            </p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={1}>Last 24 hours</option>
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
            <button
              onClick={fetchDashboard}
              disabled={loading}
              className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-600 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <TrendingUp className="w-4 h-4" />}
              Refresh
            </button>
          </div>
        </div>

        {data && (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gray-800/50 border border-gray-700 rounded-xl p-4"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm">Mode</p>
                    <p className="text-2xl font-bold text-white capitalize">{data.mode}</p>
                  </div>
                  <Globe className="w-8 h-8 text-blue-500" />
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="bg-gray-800/50 border border-gray-700 rounded-xl p-4"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm">Active Provider</p>
                    <p className="text-2xl font-bold text-white">
                      {data.active_provider || 'Local Fallback'}
                    </p>
                  </div>
                  <Zap className="w-8 h-8 text-yellow-500" />
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-gray-800/50 border border-gray-700 rounded-xl p-4"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm">Total Cost</p>
                    <p className="text-2xl font-bold text-white">
                      ${data.cost_summary.total_cost_usd.toFixed(4)}
                    </p>
                  </div>
                  <DollarSign className="w-8 h-8 text-green-500" />
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-gray-800/50 border border-gray-700 rounded-xl p-4"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm">Total Calls</p>
                    <p className="text-2xl font-bold text-white">
                       {(data.cost_summary.total_calls || 0).toLocaleString()}
                    </p>
                  </div>
                  <Activity className="w-8 h-8 text-purple-500" />
                </div>
              </motion.div>
            </div>

            {/* Providers Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(data.providers).map(([key, provider]: [string, ProviderInfo], index) => (
                <motion.div
                  key={key}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`bg-gray-800/50 border rounded-xl p-5 ${
                    provider.provider === data.active_provider
                      ? 'border-blue-500 ring-2 ring-blue-500/20'
                      : 'border-gray-700'
                  }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${PROVIDER_COLORS[key] || 'bg-gray-500'}`} />
                      <div>
                        <h3 className="text-white font-semibold">{provider.name}</h3>
                        <p className="text-gray-400 text-xs capitalize">{key}</p>
                      </div>
                    </div>
                    {getStatusBadge(provider.status, provider.healthy)}
                  </div>

                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-gray-500">Chat Model</p>
                        <p className="text-gray-300 font-mono text-xs truncate">{provider.model}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Code Model</p>
                        <p className="text-gray-300 font-mono text-xs truncate">{provider.code_model}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div>
                        <p className="text-gray-500">Keys</p>
                        <p className="text-gray-300">{provider.keys_configured}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Latency</p>
                        <p className="text-gray-300">{provider.avg_response_time_ms.toFixed(0)}ms</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Failures</p>
                        <p className="text-gray-300">{provider.consecutive_failures}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-gray-500">Input Cost</p>
                        <p className="text-gray-300">${provider.cost_per_1k_input}/1K</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Output Cost</p>
                        <p className="text-gray-300">${provider.cost_per_1k_output}/1K</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-gray-500">Total Calls</p>
                        <p className="text-gray-300">{provider.total_calls}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Total Cost</p>
                        <p className="text-gray-300">${provider.total_cost_usd.toFixed(4)}</p>
                      </div>
                    </div>

                    <div>
                      <p className="text-gray-500 text-xs mb-1">Features</p>
                      <div className="flex flex-wrap gap-1">
                        {provider.features.map((feature) => (
                          <span
                            key={feature}
                            className="px-2 py-0.5 text-xs bg-gray-700 text-gray-300 rounded"
                          >
                            {feature}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Local Fallback */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gray-800/50 border border-gray-700 rounded-xl p-5"
            >
              <div className="flex items-center gap-3 mb-3">
                <Cpu className="w-5 h-5 text-gray-400" />
                <h3 className="text-white font-semibold">Local Fallback Engine</h3>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  data.local_fallback.status === 'active'
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-gray-500/20 text-gray-400'
                }`}>
                  {data.local_fallback.status}
                </span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Engine</p>
                  <p className="text-gray-300">{data.local_fallback.engine}</p>
                </div>
                <div>
                  <p className="text-gray-500">ONNX Available</p>
                  <p className="text-gray-300">{data.local_fallback.onnx_available ? 'Yes' : 'No'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Cost</p>
                  <p className="text-gray-300">$0.00</p>
                </div>
                <div>
                  <p className="text-gray-500">Guarantee</p>
                  <p className="text-gray-300">Always available</p>
                </div>
              </div>
            </motion.div>

            {/* Recent Calls */}
            {data.recent_calls.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gray-800/50 border border-gray-700 rounded-xl p-5"
              >
                <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-gray-400" />
                  Recent API Calls
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-gray-400 border-b border-gray-700">
                        <th className="text-left py-2 px-3">Time</th>
                        <th className="text-left py-2 px-3">Provider</th>
                        <th className="text-left py-2 px-3">Model</th>
                        <th className="text-left py-2 px-3">Status</th>
                        <th className="text-left py-2 px-3">Latency</th>
                        <th className="text-left py-2 px-3">Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recent_calls.slice(0, 10).map((call: any, idx: number) => (
                        <tr key={idx} className="border-b border-gray-700/50">
                          <td className="py-2 px-3 text-gray-400">
                            {new Date(call.timestamp).toLocaleTimeString()}
                          </td>
                          <td className="py-2 px-3 text-gray-300 capitalize">{call.provider}</td>
                          <td className="py-2 px-3 text-gray-300 font-mono text-xs">{call.model}</td>
                          <td className="py-2 px-3">
                            {call.success ? (
                              <CheckCircle2 className="w-4 h-4 text-green-500" />
                            ) : (
                              <XCircle className="w-4 h-4 text-red-500" />
                            )}
                          </td>
                          <td className="py-2 px-3 text-gray-300">{call.latency_ms}ms</td>
                          <td className="py-2 px-3 text-gray-300">${call.cost_usd?.toFixed(4) || '0.00'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
