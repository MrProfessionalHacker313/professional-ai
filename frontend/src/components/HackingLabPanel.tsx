'use client'

import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Terminal, Play, Square, Trash2, Copy, Check, Shield, AlertTriangle, Bug, X, Loader2 } from 'lucide-react'
import { featuresApi } from '@/lib/api'

interface HackingLabPanelProps {
  onClose: () => void
}

interface LabSession {
  id: string
  command: string
  output: string
  status: 'running' | 'completed' | 'error'
  timestamp: string
  severity?: 'info' | 'warning' | 'critical'
}

export default function HackingLabPanel({ onClose }: HackingLabPanelProps) {
  const [sessions, setSessions] = useState<LabSession[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const outputRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    outputRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [sessions])

  const runCommand = async () => {
    if (!input.trim()) return
    const command = input.trim()
    setInput('')
    setLoading(true)

    const sessionId = Date.now().toString()
    const newSession: LabSession = {
      id: sessionId,
      command,
      output: '',
      status: 'running',
      timestamp: new Date().toLocaleTimeString(),
    }

    setSessions(prev => [...prev, newSession])

    try {
      const response = await featuresApi.routeTask({
        task_type: 'hacking_lab',
        task_description: command,
      })
      setSessions(prev =>
        prev.map(s =>
          s.id === sessionId
            ? {
                ...s,
                output: response.data.result || response.data.output || 'Command executed successfully',
                status: 'completed' as const,
                severity: response.data.severity || 'info',
              }
            : s
        )
      )
    } catch {
      setSessions(prev =>
        prev.map(s =>
          s.id === sessionId
            ? {
                ...s,
                output: 'Error: Command execution failed. Check syntax and permissions.',
                status: 'error' as const,
                severity: 'critical' as const,
              }
            : s
        )
      )
    } finally {
      setLoading(false)
    }
  }

  const clearOutput = () => {
    setSessions([])
  }

  const copyOutput = async (id: string, output: string) => {
    try {
      await navigator.clipboard.writeText(output)
      setCopiedId(id)
      setTimeout(() => setCopiedId(null), 2000)
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
    }
  }

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 border-red-500/30 bg-red-500/5'
      case 'warning': return 'text-yellow-400 border-yellow-500/30 bg-yellow-500/5'
      default: return 'text-green-400 border-green-500/30 bg-green-500/5'
    }
  }

  const getSeverityIcon = (severity?: string) => {
    switch (severity) {
      case 'critical': return <AlertTriangle className="w-4 h-4" />
      case 'warning': return <Shield className="w-4 h-4" />
      default: return <Bug className="w-4 h-4" />
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
          <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-orange-500 rounded-xl flex items-center justify-center">
            <Terminal className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Hacking Lab</h3>
            <p className="text-xs text-gray-400">Live security testing environment</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 mb-4 h-64 overflow-y-auto font-mono text-sm" ref={outputRef}>
        {sessions.length === 0 && (
          <div className="text-gray-500 text-center py-8">
            <Terminal className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No commands executed yet. Start by entering a security test command below.</p>
          </div>
        )}
        {sessions.map(session => (
          <div key={session.id} className={`mb-3 border rounded-lg p-3 ${getSeverityColor(session.severity)}`}>
            <div className="flex items-center gap-2 mb-1">
              {getSeverityIcon(session.severity)}
              <span className="text-xs text-gray-400">{session.timestamp}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                session.status === 'running' ? 'bg-yellow-500/20 text-yellow-400' :
                session.status === 'error' ? 'bg-red-500/20 text-red-400' :
                'bg-green-500/20 text-green-400'
              }`}>
                {session.status.toUpperCase()}
              </span>
            </div>
            <div className="text-xs text-gray-400 mb-1">$ {session.command}</div>
            <div className="text-xs text-gray-300 whitespace-pre-wrap bg-black/20 rounded p-2">{session.output}</div>
            <button
              onClick={() => copyOutput(session.id, session.output)}
              className="mt-1 text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1"
            >
              {copiedId === session.id ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
              {copiedId === session.id ? 'Copied' : 'Copy'}
            </button>
          </div>
        ))}
        {loading && (
          <div className="text-yellow-400 text-xs flex items-center gap-2">
            <Loader2 className="w-3 h-3 animate-spin" />
            Executing command...
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && runCommand()}
          placeholder="Enter security test command..."
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white font-mono focus:outline-none focus:border-red-500"
        />
        <button
          onClick={runCommand}
          disabled={!input.trim() || loading}
          className="bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl transition-all"
        >
          {loading ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />}
        </button>
        <button
          onClick={clearOutput}
          className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-400 px-4 py-2.5 rounded-xl transition-all"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  )
}
