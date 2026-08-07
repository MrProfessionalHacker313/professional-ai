'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send,
  Sparkles,
  Code2,
  Shield,
  Bug,
  Copy,
  Check,
  Loader2,
  User,
  Bot,
  Maximize2,
  Minimize2
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import { chatApi } from '@/lib/api'
import { offlineAI } from '@/lib/offline-ai'
import { offlineSearch } from '@/lib/offline-search'
import { offlineSync } from '@/lib/offline-sync'
import { useConnectivity } from '@/lib/use-connectivity'
import OfflineStatusBar from '@/components/OfflineStatusBar'
import PWAInstaller from '@/components/PWAInstaller'

type ChatMode = 'chat' | 'code' | 'security' | 'bugfix'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  mode: ChatMode
  timestamp: Date
  isTyping?: boolean
}

export default function ChatPage() {
  const router = useRouter()
  const [mounted, setMounted] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [mode, setMode] = useState<ChatMode>('chat')
  const [loading, setLoading] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isOfflineMode, setIsOfflineMode] = useState(false)
  const [isOwnerMode, setIsOwnerMode] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { isOnline } = useConnectivity()

  useEffect(() => { setMounted(true) }, [])

  useEffect(() => {
    setIsOfflineMode(!isOnline)
  }, [isOnline])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    // Check authentication - token is stored in a cookie at login (not localStorage)
    const hasLocalToken = typeof localStorage !== 'undefined' && !!localStorage.getItem('access_token')
    const hasCookieToken =
      typeof document !== 'undefined' &&
      document.cookie.split('; ').some((row) => row.startsWith('access_token='))
    if (!hasLocalToken && !hasCookieToken && mounted) {
      router.push('/login')
    }

    // Detect OWNER AI MODE: ?owner=1 query param or owner_ai_mode cookie set by Admin "Use AI" button
    const isOwner =
      typeof window !== 'undefined' &&
      (new URLSearchParams(window.location.search).get('owner') === '1' ||
        document.cookie.split('; ').some((row) => row.startsWith('owner_ai_mode=1')))
    setIsOwnerMode(!!isOwner)
  }, [mounted, router])

  if (!mounted) return null

  const modes = [
    { id: 'chat', label: 'Chat', icon: Sparkles, color: 'from-blue-500 to-cyan-500' },
    { id: 'code', label: 'Code', icon: Code2, color: 'from-green-500 to-emerald-500' },
    { id: 'security', label: 'Security', icon: Shield, color: 'from-purple-500 to-pink-500' },
    { id: 'bugfix', label: 'Bug Fix', icon: Bug, color: 'from-red-500 to-orange-500' },
  ]

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      mode,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    // Add typing indicator
    const typingMessage: Message = {
      id: 'typing',
      role: 'assistant',
      content: '',
      mode,
      timestamp: new Date(),
      isTyping: true,
    }
    setMessages(prev => [...prev, typingMessage])

    try {
      let content = ''

      if (isOfflineMode) {
        // OFFLINE MODE: use local AI engine + knowledge search
        // 1. Search knowledge index for relevant context
        const searchResults = await offlineSearch.search(userMessage.content, 3)
        const knowledgeContext = searchResults.length > 0
          ? searchResults.map(r => `**${r.entry.title}**\n${r.entry.content}\n\n${r.entry.snippet}`).join('\n\n---\n\n')
          : undefined

        // 2. Generate with local model (or knowledge fallback)
        const localResult = await offlineAI.generate(
          userMessage.content,
          mode,
          knowledgeContext
        )
        content = localResult.content

        // 3. Queue for cloud sync when back online
        await offlineSync.enqueue(mode, {
          prompt: userMessage.content,
          mode,
          offline_response: content,
          timestamp: new Date().toISOString(),
        })
      } else {
        // ONLINE MODE: use cloud API
        let response: { data: { content?: string; response?: string } } = { data: {} }
        if (mode === 'chat') {
          response = await chatApi.send({ prompt: userMessage.content, mode })
        } else if (mode === 'code') {
          response = await chatApi.generateCode({ prompt: userMessage.content, language: 'python' })
        } else if (mode === 'security') {
          response = await chatApi.securityQuery({ query: userMessage.content })
        } else if (mode === 'bugfix') {
          response = await chatApi.fixBug({ code: userMessage.content })
        }
        content = response.data.content || response.data.response || 'No response'
      }

      // Remove typing indicator and add real response
      setMessages(prev => {
        const withoutTyping = prev.filter(m => m.id !== 'typing')
        return [...withoutTyping, {
          id: (Date.now() + 1).toString(),
          role: 'assistant' as const,
          content,
          mode,
          timestamp: new Date(),
        }]
      })
    } catch (error) {
      // If online call fails, fall back to offline engine
      try {
        const searchResults = await offlineSearch.search(userMessage.content, 3)
        const knowledgeContext = searchResults.length > 0
          ? searchResults.map(r => `**${r.entry.title}**\n${r.entry.content}\n\n${r.entry.snippet}`).join('\n\n---\n\n')
          : undefined
        const localResult = await offlineAI.generate(userMessage.content, mode, knowledgeContext)

        setMessages(prev => {
          const withoutTyping = prev.filter(m => m.id !== 'typing')
          return [...withoutTyping, {
            id: (Date.now() + 1).toString(),
            role: 'assistant' as const,
            content: localResult.content,
            mode,
            timestamp: new Date(),
          }]
        })
      } catch (fallbackError) {
        setMessages(prev => {
          const withoutTyping = prev.filter(m => m.id !== 'typing')
          return [...withoutTyping, {
            id: (Date.now() + 1).toString(),
            role: 'assistant' as const,
            content: 'Sorry, I encountered an error. Please try again.',
            mode,
            timestamp: new Date(),
          }]
        })
      }
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const getModeIcon = (mode: ChatMode) => {
    const modeConfig = modes.find(m => m.id === mode)
    return modeConfig ? modeConfig.icon : Sparkles
  }

  const getModeColor = (mode: ChatMode) => {
    const modeConfig = modes.find(m => m.id === mode)
    return modeConfig ? modeConfig.color : 'from-blue-500 to-cyan-500'
  }

  return (
    <div className={`min-h-screen bg-gray-950 text-white flex flex-col ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      {/* Header */}
      <header className="bg-gray-900/50 backdrop-blur-xl border-b border-gray-800/50 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            >
              ←
            </button>
            <div>
              <h1 className="text-xl font-bold flex items-center gap-2">
                AI Assistant
                {isOwnerMode && (
                  <span className="rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 px-2.5 py-0.5 text-xs font-bold text-white">
                    👑 OWNER — UNLIMITED
                  </span>
                )}
              </h1>
              <p className="text-sm text-gray-400">
                {isOwnerMode ? 'Full owner power — no limits, no credits, priority routing' : 'Professional AI - Ready to help'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Mode Selector */}
            <div className="flex items-center gap-1 bg-gray-800/50 p-1 rounded-xl">
              {modes.map(modeItem => (
                <button
                  key={modeItem.id}
                  onClick={() => setMode(modeItem.id as ChatMode)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    mode === modeItem.id
                      ? 'bg-gradient-to-r ' + modeItem.color + ' text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <modeItem.icon className="w-4 h-4 inline mr-1" />
                  {modeItem.label}
                </button>
              ))}
            </div>

            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            >
              {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-20">
              <div className={`w-20 h-20 bg-gradient-to-br ${getModeColor(mode)} rounded-2xl flex items-center justify-center mx-auto mb-4`}>
                <Sparkles className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-2xl font-bold mb-2">How can I help you today?</h2>
              <p className="text-gray-400">Ask me anything in {mode} mode</p>
            </div>
          )}

          <AnimatePresence>
            {messages.map(message => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className={`w-8 h-8 bg-gradient-to-br ${getModeColor(message.mode)} rounded-lg flex items-center justify-center flex-shrink-0`}>
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}

                <div className={`max-w-2xl ${message.role === 'user' ? 'order-first' : ''}`}>
                  <div
                    className={`rounded-2xl px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                        : 'bg-gray-800/50 border border-gray-700/50 text-gray-100'
                    }`}
                  >
                    {message.isTyping ? (
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-gray-400">Thinking...</span>
                      </div>
                    ) : (
                      <>
                        <div className="whitespace-pre-wrap break-words">{message.content}</div>
                        {message.role === 'assistant' && (
                          <button
                            onClick={() => copyToClipboard(message.content, message.id)}
                            className="mt-2 text-gray-400 hover:text-white transition-colors"
                          >
                            {copiedId === message.id ? (
                              <Check className="w-4 h-4" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>
                        )}
                      </>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mt-1 px-2">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>

                {message.role === 'user' && (
                  <div className="w-8 h-8 bg-gray-700 rounded-lg flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-gray-300" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-800/50 bg-gray-900/50 backdrop-blur-xl p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end gap-2 bg-gray-800/50 border border-gray-700/50 rounded-2xl p-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Message AI in ${mode} mode...`}
              className="flex-1 bg-transparent border-0 outline-none resize-none px-3 py-2 text-white placeholder-gray-500 max-h-32"
              rows={1}
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="p-3 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl hover:from-blue-500 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <div className="text-xs text-gray-500 text-center mt-2">
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </div>

      {/* Offline status bar + PWA installer */}
      <OfflineStatusBar />
      <PWAInstaller />
    </div>
  )
}
