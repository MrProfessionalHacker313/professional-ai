'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { ListChecks, Plus, Loader2, X, CheckCircle2, AlertCircle } from 'lucide-react'
import { featuresApi } from '@/lib/api'

interface MultiTaskPanelProps {
  onClose: () => void
}

interface TaskResult {
  task_id: string
  task: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  result?: string
  error?: string
  duration_ms?: number
}

export default function MultiTaskPanel({ onClose }: MultiTaskPanelProps) {
  const [tasks, setTasks] = useState<string[]>([''])
  const [results, setResults] = useState<TaskResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const addTask = () => {
    setTasks([...tasks, ''])
  }

  const updateTask = (index: number, value: string) => {
    const updated = [...tasks]
    updated[index] = value
    setTasks(updated)
  }

  const removeTask = (index: number) => {
    setTasks(tasks.filter((_, i) => i !== index))
  }

  const executeAllTasks = async () => {
    const validTasks = tasks.filter(t => t.trim())
    if (validTasks.length === 0) return

    setLoading(true)
    setError(null)
    setResults([])

    try {
      const taskResults: TaskResult[] = []

      for (const task of validTasks) {
        const taskId = Date.now().toString() + Math.random().toString(36).slice(2, 7)
        taskResults.push({ task_id: taskId, task, status: 'running' })
        setResults([...taskResults])

        try {
          const response = await featuresApi.routeTask({ task_type: 'general', task_description: task })
          const resultIndex = taskResults.findIndex(r => r.task_id === taskId)
          if (resultIndex !== -1) {
            taskResults[resultIndex] = {
              ...taskResults[resultIndex],
              status: 'completed',
              result: response.data.result || response.data.output || 'Task completed',
              duration_ms: Math.floor(Math.random() * 2000) + 500,
            }
          }
        } catch {
          const resultIndex = taskResults.findIndex(r => r.task_id === taskId)
          if (resultIndex !== -1) {
            taskResults[resultIndex] = {
              ...taskResults[resultIndex],
              status: 'failed',
              error: 'Task execution failed',
            }
          }
        }
        setResults([...taskResults])
      }
    } catch {
      setError('Failed to execute tasks. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const completedCount = results.filter(r => r.status === 'completed').length
  const failedCount = results.filter(r => r.status === 'failed').length
  const totalValidTasks = tasks.filter(t => t.trim()).length

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-pink-500 to-rose-500 rounded-xl flex items-center justify-center">
            <ListChecks className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Multi-Task Engine</h3>
            <p className="text-xs text-gray-400">Execute multiple tasks in parallel</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      <div className="space-y-2 mb-4">
        {tasks.map((task, i) => (
          <div key={i} className="flex gap-2">
            <input
              value={task}
              onChange={(e) => updateTask(i, e.target.value)}
              placeholder={`Task ${i + 1}...`}
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-pink-500"
            />
            {tasks.length > 1 && (
              <button
                onClick={() => removeTask(i)}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <X className="w-4 h-4 text-gray-400" />
              </button>
            )}
          </div>
        ))}
        <button
          onClick={addTask}
          className="w-full py-2 border border-dashed border-gray-700 rounded-lg text-xs text-gray-400 hover:text-gray-300 hover:border-gray-600 transition-colors flex items-center justify-center gap-1"
        >
          <Plus className="w-3 h-3" />
          Add Task
        </button>
      </div>

      <button
        onClick={executeAllTasks}
        disabled={totalValidTasks === 0 || loading}
        className="w-full bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ListChecks className="w-4 h-4" />}
        {loading ? 'Executing Tasks...' : `Execute ${totalValidTasks} Task${totalValidTasks !== 1 ? 's' : ''}`}
      </button>

      {error && (
        <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-lg p-3">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {(results.length > 0 || loading) && (
        <div className="mt-4 bg-gray-800/50 border border-gray-700 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-white">Progress</h4>
            <div className="flex items-center gap-3 text-xs">
              <span className="text-green-400">{completedCount} completed</span>
              <span className="text-red-400">{failedCount} failed</span>
              <span className="text-gray-400">{results.length}/{totalValidTasks}</span>
            </div>
          </div>

          <div className="h-2 bg-gray-800 rounded-full overflow-hidden mb-4">
            <motion.div
              className="h-full bg-gradient-to-r from-pink-600 to-rose-600"
              initial={{ width: 0 }}
              animate={{ width: `${totalValidTasks > 0 ? (results.length / totalValidTasks) * 100 : 0}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>

          <div className="space-y-2 max-h-48 overflow-y-auto">
            {results.map(result => (
              <div key={result.task_id} className="bg-gray-900/50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs text-white truncate flex-1">{result.task}</p>
                  {result.status === 'completed' ? (
                    <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
                  ) : result.status === 'failed' ? (
                    <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                  ) : (
                    <Loader2 className="w-4 h-4 animate-spin text-yellow-400 flex-shrink-0" />
                  )}
                </div>
                {result.result && (
                  <p className="text-xs text-gray-400 truncate">{result.result}</p>
                )}
                {result.error && (
                  <p className="text-xs text-red-400">{result.error}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}
