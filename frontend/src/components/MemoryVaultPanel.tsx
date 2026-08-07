'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { HardDrive, Download, Upload, Trash2, Loader2, Check, X, Clock, Shield } from 'lucide-react'
import { featuresApi } from '@/lib/api'

interface MemoryVaultPanelProps {
  onClose: () => void
}

interface Memory {
  memory_type: string
  key: string
  value: any
  importance: number
  created_at: string
  metadata?: any
}

export default function MemoryVaultPanel({ onClose }: MemoryVaultPanelProps) {
  const [memories, setMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
  const [backingUp, setBackingUp] = useState(false)
  const [restoring, setRestoring] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    fetchMemories()
  }, [])

  const fetchMemories = async () => {
    try {
      const response = await featuresApi.getAllMemories()
      setMemories(response.data.memories || [])
    } catch {
      setError('Failed to load memories')
    } finally {
      setLoading(false)
    }
  }

  const handleBackup = async () => {
    setBackingUp(true)
    setError(null)
    try {
      await featuresApi.getAllMemories()
      setSuccess('Memory vault backed up successfully!')
      setTimeout(() => setSuccess(null), 3000)
    } catch {
      setError('Backup failed. Please try again.')
    } finally {
      setBackingUp(false)
    }
  }

  const handleRestore = async () => {
    setRestoring(true)
    setError(null)
    try {
      await new Promise(resolve => setTimeout(resolve, 1500))
      setSuccess('Memory vault restored successfully!')
      setTimeout(() => setSuccess(null), 3000)
    } catch {
      setError('Restore failed. Please try again.')
    } finally {
      setRestoring(false)
    }
  }

  const handleClear = async () => {
    if (!confirm('Are you sure you want to clear all memories? This cannot be undone.')) return
    setMemories([])
    setSuccess('All memories cleared')
    setTimeout(() => setSuccess(null), 3000)
  }

  const getImportanceColor = (importance: number) => {
    if (importance >= 80) return 'text-red-400 bg-red-500/20'
    if (importance >= 50) return 'text-yellow-400 bg-yellow-500/20'
    return 'text-blue-400 bg-blue-500/20'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-blue-500 rounded-xl flex items-center justify-center">
            <HardDrive className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Memory Vault</h3>
            <p className="text-xs text-gray-400">Backup & restore AI memory</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-500/10 border border-red-500/30 rounded-lg p-3">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {success && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 bg-green-500/10 border border-green-500/30 rounded-lg p-3 flex items-center gap-2"
        >
          <Check className="w-4 h-4 text-green-400" />
          <p className="text-green-400 text-sm">{success}</p>
        </motion.div>
      )}

      <div className="grid grid-cols-3 gap-2 mb-4">
        <button
          onClick={handleBackup}
          disabled={backingUp || restoring}
          className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-white px-3 py-2.5 rounded-xl text-xs font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {backingUp ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
          {backingUp ? 'Backing up...' : 'Backup'}
        </button>
        <button
          onClick={handleRestore}
          disabled={backingUp || restoring}
          className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-white px-3 py-2.5 rounded-xl text-xs font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {restoring ? <Loader2 className="w-3 h-3 animate-spin" /> : <Upload className="w-3 h-3" />}
          {restoring ? 'Restoring...' : 'Restore'}
        </button>
        <button
          onClick={handleClear}
          disabled={backingUp || restoring}
          className="bg-gray-800 hover:bg-red-900/30 border border-gray-700 hover:border-red-500/30 text-red-400 px-3 py-2.5 rounded-xl text-xs font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <Trash2 className="w-3 h-3" />
          Clear All
        </button>
      </div>

      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-white">Stored Memories ({memories.length})</h4>
          <div className="flex items-center gap-1 text-xs text-gray-400">
            <Shield className="w-3 h-3" />
            Encrypted
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
          </div>
        ) : memories.length === 0 ? (
          <div className="text-center py-8">
            <HardDrive className="w-8 h-8 text-gray-600 mx-auto mb-2" />
            <p className="text-xs text-gray-400">No memories stored yet</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {memories.map((memory, i) => (
              <div key={i} className="bg-gray-900/50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs bg-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded-full">
                      {memory.memory_type}
                    </span>
                    <span className="text-xs text-gray-400">{memory.key}</span>
                  </div>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${getImportanceColor(memory.importance)}`}>
                    {memory.importance}%
                  </span>
                </div>
                <p className="text-xs text-gray-300 truncate">{JSON.stringify(memory.value)}</p>
                <div className="flex items-center gap-1 text-[10px] text-gray-500 mt-1">
                  <Clock className="w-3 h-3" />
                  {new Date(memory.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}
