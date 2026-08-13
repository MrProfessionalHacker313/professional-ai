'use client'

import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Mic, StopCircle, Play, Loader2, X, Volume2, Command, Zap } from 'lucide-react'
import { featuresApi } from '@/lib/api'

interface VoiceCommandPanelProps {
  onClose: () => void
}

interface VoiceCommand {
  id: string
  transcript: string
  action: string
  status: 'listening' | 'processing' | 'completed' | 'error'
  timestamp: string
  confidence?: number
}

export default function VoiceCommandPanel({ onClose }: VoiceCommandPanelProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [commands, setCommands] = useState<VoiceCommand[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop()
      }
    }
  }, [isRecording])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' })
        processVoiceCommand(audioBlob)
      }

      mediaRecorder.start()
      setIsRecording(true)

      const commandId = Date.now().toString()
      setCommands(prev => [...prev, {
        id: commandId,
        transcript: '',
        action: 'Listening...',
        status: 'listening',
        timestamp: new Date().toLocaleTimeString(),
      }])
    } catch {
      setError('Could not access microphone. Please grant permission.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
      setIsRecording(false)
    }
  }

  const processVoiceCommand = async (audioBlob: Blob) => {
    setLoading(true)
    const lastCommand = commands[commands.length - 1]
    try {
      const formData = new FormData()
      formData.append('file', audioBlob, 'recording.wav')
      const response = await featuresApi.speechToText({ audio_path: 'recording.wav' })

      setCommands(prev =>
        prev.map(c =>
          c.id === lastCommand?.id
            ? {
                ...c,
                transcript: response.data.text || 'Voice command received',
                action: response.data.action || 'Processing...',
                status: 'completed' as const,
                confidence: response.data.confidence || 0.9,
              }
            : c
        )
      )
    } catch {
      setCommands(prev =>
        prev.map(c =>
          c.id === lastCommand?.id
            ? { ...c, action: 'Error processing voice', status: 'error' as const }
            : c
        )
      )
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
          <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-green-500 rounded-xl flex items-center justify-center">
            <Mic className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Voice Command</h3>
            <p className="text-xs text-gray-400">Control AI with your voice</p>
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

      <div className="flex flex-col items-center justify-center py-8 mb-4">
        <motion.button
          onClick={isRecording ? stopRecording : startRecording}
          className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${
            isRecording
              ? 'bg-red-500/20 border-2 border-red-500 animate-pulse'
              : 'bg-gradient-to-br from-teal-500 to-green-500 hover:from-teal-400 hover:to-green-400'
          }`}
        >
          {isRecording ? (
            <StopCircle className="w-8 h-8 text-red-400" />
          ) : (
            <StopCircle className="w-8 h-8 text-red-400" />
          )}
        </motion.button>
        <p className="text-xs text-gray-400 mt-3">
          {isRecording ? 'Recording... Click to stop' : 'Click to start recording'}
        </p>
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {commands.map(cmd => (
          <div key={cmd.id} className="bg-gray-800/50 border border-gray-700 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <Volume2 className="w-4 h-4 text-teal-400" />
                <span className="text-xs text-gray-400">{cmd.timestamp}</span>
              </div>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                cmd.status === 'listening' ? 'bg-yellow-500/20 text-yellow-400' :
                cmd.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                cmd.status === 'error' ? 'bg-red-500/20 text-red-400' :
                'bg-blue-500/20 text-blue-400'
              }`}>
                {cmd.status.toUpperCase()}
              </span>
            </div>
            {cmd.transcript && (
              <p className="text-sm text-white mb-1">"{cmd.transcript}"</p>
            )}
            {cmd.action && (
              <div className="flex items-center gap-1 text-xs text-teal-400">
                <Zap className="w-3 h-3" />
                {cmd.action}
              </div>
            )}
            {cmd.confidence && (
              <p className="text-[10px] text-gray-500 mt-1">Confidence: {(cmd.confidence * 100).toFixed(0)}%</p>
            )}
          </div>
        ))}
        {loading && (
          <div className="text-xs text-gray-400 flex items-center gap-2">
            <Loader2 className="w-3 h-3 animate-spin" />
            Processing voice command...
          </div>
        )}
      </div>
    </motion.div>
  )
}
