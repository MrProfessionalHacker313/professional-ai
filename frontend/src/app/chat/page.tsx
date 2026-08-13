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
  Minimize2,
  Edit3,
  Mic,
  StopCircle,
  Image,
  Video,
  Wand2,
  Film
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import { chatApi, conversationsApi } from '@/lib/api'
import ChatSidebar from '@/components/ChatSidebar'
import { offlineAI } from '@/lib/offline-ai'
import { offlineSearch } from '@/lib/offline-search'
import { offlineSync } from '@/lib/offline-sync'
import { useConnectivity } from '@/lib/use-connectivity'
import { offlineStorage } from '@/lib/offline-storage'
import { generateOfflineCode, detectCodeLanguage } from '@/lib/offline-code-generator'
import { offlineTranscribe } from '@/lib/api-offline'
import ProfessionalMarkdownRenderer from '@/components/ProfessionalMarkdownRenderer'
import toast from 'react-hot-toast'

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
  const [editingPromptId, setEditingPromptId] = useState<string | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isOfflineMode, setIsOfflineMode] = useState(false)
  const [isOwnerMode, setIsOwnerMode] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessingVoice, setIsProcessingVoice] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const { isOnline } = useConnectivity()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  useEffect(() => { setMounted(true) }, [])

  // Auto-grow textarea height
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = textarea.scrollHeight + 'px'
    }
  }, [input])

  useEffect(() => {
    setIsOfflineMode(!isOnline)
  }, [isOnline])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Load most recent conversation on mount
  useEffect(() => {
    const init = async () => {
      try {
        const response = await conversationsApi.list()
        const convs = response.data
        if (convs.length > 0) {
          try {
            await loadConversationMessages(convs[0].id)
            return
          } catch (e) {
            console.warn('[Chat] Failed to load most recent conversation:', e)
          }
        }
      } catch (error) {
        console.warn('[Chat] Backend conversations unavailable, using local cache:', error)
      }
      // Fallback to IndexedDB - load most recent local conversation
      try {
        const localConvs = await getLocalConversations()
        if (localConvs.length > 0) {
          const sorted = localConvs.sort((a: any, b: any) => (b.updated_at || 0) - (a.updated_at || 0))
          await loadLocalConversationMessages(sorted[0].id)
          return
        }
      } catch (e) {
        console.warn('[Chat] Failed to load local conversations:', e)
      }
    }
    init()
  }, [])

  // Save messages to IndexedDB when they change
  useEffect(() => {
    if (messages.length === 0) return
    const saveMessages = async () => {
      try {
        // Save only the last 100 messages to avoid huge writes
        const toSave = messages.slice(-100)
        await Promise.all(toSave.map((msg) =>
          offlineStorage.set(
            'chat_history',
            msg.id,
            {
              role: msg.role,
              content: msg.content,
              mode: msg.mode,
              timestamp: msg.timestamp.getTime(),
              conversation_id: currentConversationId,
            }
          )
        ))
      } catch (e) {
        console.warn('[Chat] Failed to save history:', e)
      }
    }
    const timer = setTimeout(saveMessages, 500)
    return () => clearTimeout(timer)
  }, [messages, currentConversationId])

  useEffect(() => {
    // Check authentication - token is stored in a cookie at login (not localStorage)
    const hasLocalToken = typeof localStorage !== 'undefined' && !!localStorage.getItem('access_token')
    const hasCookieToken =
      typeof document !== 'undefined' &&
      document.cookie.split('; ').some((row) => row.startsWith('access_token='))
    const hasRefreshToken =
      typeof document !== 'undefined' &&
      document.cookie.split('; ').some((row) => row.startsWith('refresh_token='))
    if (!hasLocalToken && !hasCookieToken && !hasRefreshToken && mounted) {
      router.push('/login')
    }

    // Detect OWNER AI MODE: ?owner=1 query param or owner_ai_mode cookie set by Admin "Use AI" button
    const isOwner =
      typeof window !== 'undefined' &&
      (new URLSearchParams(window.location.search).get('owner') === '1' ||
        document.cookie.split('; ').some((row) => row.startsWith('owner_ai_mode=1')))
    setIsOwnerMode(!!isOwner)
  }, [mounted, router])

  // Offline code generation queue
  const [codeQueue, setCodeQueue] = useState<Array<{ prompt: string; id: string }>>([])
  const [queueVisible, setQueueVisible] = useState(false)

  // When coming back online, process the queued code prompts
  useEffect(() => {
    if (isOnline && codeQueue.length > 0) {
      // Auto-generate queued code when back online
      const processQueue = async () => {
        const queueCopy = [...codeQueue]
        setCodeQueue([])
        for (const item of queueCopy) {
          try {
            const response = await chatApi.generateCode({ prompt: item.prompt, language: detectCodeLanguage(item.prompt) })
            const content = response.data.content || response.data.response || 'No response'
             setMessages(prev => [...prev.filter(m => m.id !== 'typing'), {
               id: generateId(),
               role: 'assistant' as const,
               content,
               mode: 'code' as ChatMode,
               timestamp: new Date(),
             }])
           } catch (e) {
             // Fall back to local generator
             const content = generateOfflineCode(item.prompt, detectCodeLanguage(item.prompt))
             setMessages(prev => [...prev.filter(m => m.id !== 'typing'), {
               id: generateId(),
               role: 'assistant' as const,
               content,
               mode: 'code' as ChatMode,
               timestamp: new Date(),
             }])
          }
        }
      }
      processQueue()
    }
  }, [isOnline, codeQueue, router, chatApi])

  if (!mounted) return null

  const modes = [
    { id: 'chat', label: 'Chat', icon: Sparkles, color: 'from-blue-500 to-cyan-500' },
    { id: 'code', label: 'Code', icon: Code2, color: 'from-green-500 to-emerald-500' },
    { id: 'security', label: 'Security', icon: Shield, color: 'from-purple-500 to-pink-500' },
    { id: 'bugfix', label: 'Bug Fix', icon: Bug, color: 'from-red-500 to-orange-500' },
  ]

  const generateId = () => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID()
    }
    return `msg-${Date.now()}-${Math.random().toString(36).slice(2)}`
  }

  const getLocalConversations = async (): Promise<any[]> => {
    try {
      return await offlineStorage.getAll<any>('chat_conversations')
    } catch {
      return []
    }
  }

  const saveLocalConversation = async (conv: { id: string; title: string; created_at: number; updated_at: number; message_count: number }) => {
    try {
      await offlineStorage.set('chat_conversations', conv.id, {
        id: conv.id,
        title: conv.title,
        created_at: conv.created_at,
        updated_at: conv.updated_at,
        message_count: conv.message_count,
      })
    } catch (e) {
      console.warn('[Chat] Failed to save local conversation:', e)
    }
  }

  const deleteLocalConversation = async (id: string) => {
    try {
      await offlineStorage.delete('chat_conversations', id)
      await offlineStorage.delete('chat_history', id)
    } catch (e) {
      console.warn('[Chat] Failed to delete local conversation:', e)
    }
  }

  const loadLocalConversationMessages = async (id: string) => {
    try {
      const history = await offlineStorage.getAll<any>('chat_history')
      const messages = history
        .filter((item: any) => item.conversation_id === id)
        .sort((a: any, b: any) => a.timestamp - b.timestamp)
        .map((item: any) => ({
          id: item.id,
          role: item.role,
          content: item.content,
          mode: item.mode,
          timestamp: new Date(item.timestamp),
        }))
      setCurrentConversationId(id)
      setMessages(messages)
    } catch (e) {
      console.warn('[Chat] Failed to load local conversation:', e)
    }
  }

  const loadConversationMessages = async (id: string) => {
    try {
      const response = await conversationsApi.get(id)
      const loadedMessages = response.data.messages.map((msg: any) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        mode: msg.mode,
        timestamp: new Date(msg.created_at),
      }))
      setCurrentConversationId(id)
      setMessages(loadedMessages)
    } catch (error) {
      console.error('Failed to load conversation from backend:', error)
      await loadLocalConversationMessages(id)
      toast.error('Backend unavailable. Loaded local history.')
    }
  }

  const handleNewChat = async () => {
    try {
      const response = await conversationsApi.create({ title: 'New Conversation' })
      const newId = response.data.id
      setCurrentConversationId(newId)
      setMessages([])
      setRefreshTrigger(prev => prev + 1)
      await saveLocalConversation({
        id: newId,
        title: 'New Conversation',
        created_at: Date.now(),
        updated_at: Date.now(),
        message_count: 0,
      })
    } catch (error) {
      console.error('Failed to create conversation:', error)
      const localId = generateId()
      setCurrentConversationId(localId)
      setMessages([])
      setRefreshTrigger(prev => prev + 1)
      await saveLocalConversation({
        id: localId,
        title: 'New Conversation',
        created_at: Date.now(),
        updated_at: Date.now(),
        message_count: 0,
      })
      toast.error('Backend unavailable. Starting local chat.')
    }
  }

  const handleSelectConversation = async (id: string) => {
    await loadConversationMessages(id)
    setSidebarOpen(false)
  }

  const handleConversationDeleted = async (id?: string) => {
    const deletedId = id || currentConversationId
    if (deletedId) {
      await deleteLocalConversation(deletedId)
    }
    setCurrentConversationId(null)
    setMessages([])
    setRefreshTrigger(prev => prev + 1)
    try {
      const response = await conversationsApi.create({ title: 'New Conversation' })
      const newId = response.data.id
      setCurrentConversationId(newId)
      await saveLocalConversation({
        id: newId,
        title: 'New Conversation',
        created_at: Date.now(),
        updated_at: Date.now(),
        message_count: 0,
      })
    } catch (error) {
      console.error('Failed to create new conversation after delete:', error)
      const localId = generateId()
      setCurrentConversationId(localId)
      await saveLocalConversation({
        id: localId,
        title: 'New Conversation',
        created_at: Date.now(),
        updated_at: Date.now(),
        message_count: 0,
      })
    }
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return

    let conversationId = currentConversationId
    if (!conversationId) {
      try {
        const title = input.trim().slice(0, 40) || 'New Conversation'
        const response = await conversationsApi.create({ title })
        conversationId = response.data.id
        if (!conversationId) {
          console.error('Failed to create conversation: no ID returned')
          toast.error('Failed to create conversation')
          return
        }
        setCurrentConversationId(conversationId)
        setRefreshTrigger(prev => prev + 1)
        await saveLocalConversation({
          id: conversationId,
          title,
          created_at: Date.now(),
          updated_at: Date.now(),
          message_count: 1,
        })
      } catch (error) {
        console.error('Failed to create conversation:', error)
        conversationId = generateId()
        setCurrentConversationId(conversationId)
        setRefreshTrigger(prev => prev + 1)
        await saveLocalConversation({
          id: conversationId,
          title: input.trim().slice(0, 40) || 'New Conversation',
          created_at: Date.now(),
          updated_at: Date.now(),
          message_count: 1,
        })
        toast.error('Backend unavailable. Saving locally.')
      }
    }

    const userMessage: Message = {
      id: generateId(),
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

    const addAssistantMessage = (content: string) => {
      setMessages(prev => {
        const withoutTyping = prev.filter(m => m.id !== 'typing')
        return [...withoutTyping, {
          id: generateId(),
          role: 'assistant' as const,
          content,
          mode,
          timestamp: new Date(),
        }]
      })
    }

    const saveMessagesToBackend = async (userMsg: Message, assistantContent: string) => {
      if (!conversationId) return
      try {
        await Promise.all([
          conversationsApi.addMessage(conversationId, {
            content: userMsg.content,
            mode: userMsg.mode,
            role: 'user'
          }),
          conversationsApi.addMessage(conversationId, {
            content: assistantContent,
            mode,
            role: 'assistant'
          })
        ])
        await saveLocalConversation({
          id: conversationId,
          title: 'New Conversation',
          created_at: Date.now(),
          updated_at: Date.now(),
          message_count: messages.length + 2,
        })
      } catch (saveError) {
        console.error('Failed to save messages to backend:', saveError)
      }
    }

    try {
      let content = ''

      if (isOfflineMode) {
        // OFFLINE MODE: use local AI engine + knowledge search
        if (mode === 'code') {
          // Use rule-based code generator - always works offline
          const language = detectCodeLanguage(userMessage.content)
          content = generateOfflineCode(userMessage.content, language)

           // Queue this prompt for real AI generation when back online
           setCodeQueue(prev => [...prev, {
             prompt: userMessage.content,
             id: generateId(),
           }])
          setQueueVisible(true)
        } else {
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
        }

        // Save generated code to IndexedDB
        if (mode === 'code' || mode === 'bugfix') {
          await offlineStorage.set('generated_code', userMessage.id, {
            prompt: userMessage.content,
            code: content,
            mode,
            timestamp: Date.now(),
          })
        }

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

      addAssistantMessage(content)
      await saveMessagesToBackend(userMessage, content)
    } catch (error) {
      // If online call fails, fall back to offline engine
      try {
        const searchResults = await offlineSearch.search(userMessage.content, 3)
        const knowledgeContext = searchResults.length > 0
          ? searchResults.map(r => `**${r.entry.title}**\n${r.entry.content}\n\n${r.entry.snippet}`).join('\n\n---\n\n')
          : undefined
        const localResult = await offlineAI.generate(userMessage.content, mode, knowledgeContext)

        addAssistantMessage(localResult.content)
        await saveMessagesToBackend(userMessage, localResult.content)
      } catch (fallbackError) {
        addAssistantMessage('Sorry, I encountered an error. Please try again.')
        await saveMessagesToBackend(userMessage, 'Sorry, I encountered an error. Please try again.')
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

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedId(id)
      setTimeout(() => setCopiedId(null), 2000)
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
    }
  }

  const getModeIcon = (mode: ChatMode) => {
    const modeConfig = modes.find(m => m.id === mode)
    return modeConfig ? modeConfig.icon : Sparkles
  }

  const getModeColor = (mode: ChatMode) => {
    const modeConfig = modes.find(m => m.id === mode)
    return modeConfig ? modeConfig.color : 'from-blue-500 to-cyan-500'
  }

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
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' })
        await processVoiceInput(audioBlob)
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch {
      toast.error('Could not access microphone. Please grant permission.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const processVoiceInput = async (audioBlob: Blob) => {
    setIsProcessingVoice(true)
    try {
      const result = await offlineTranscribe(audioBlob, 'en')
      if (result.text) {
        setInput(prev => prev ? prev + ' ' + result.text : result.text)
        toast.success('Voice transcribed!')
      }
    } catch {
      toast.error('Voice transcription failed')
    } finally {
      setIsProcessingVoice(false)
    }
  }

  return (
    <>
      <ChatSidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewChat}
        onConversationDeleted={handleConversationDeleted}
        refreshTrigger={refreshTrigger}
      />
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

      {/* Media Quick Access */}
      <div className="bg-gray-900/30 border-b border-gray-800/30 px-6 py-3">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3 overflow-x-auto pb-1 scrollbar-hide">
            <span className="text-xs text-gray-500 uppercase tracking-wider whitespace-nowrap font-medium">Quick Access</span>
            {[
              { id: 'image', label: 'Image Gen', icon: Image, href: '/media?mode=image', color: 'from-pink-500 to-rose-500' },
              { id: 'video', label: 'Video Gen', icon: Video, href: '/media?mode=video', color: 'from-red-500 to-orange-500' },
              { id: 'voice', label: 'Voice', icon: Mic, href: '/media?mode=voice', color: 'from-indigo-500 to-blue-500' },
              { id: 'animation', label: 'Animation', icon: Film, href: '/media?mode=animation', color: 'from-purple-500 to-pink-500' },
            ].map(item => (
              <a
                key={item.id}
                href={item.href}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r ${item.color} bg-opacity-10 border border-gray-800 hover:border-gray-700 transition-all whitespace-nowrap`}
              >
                <item.icon className="w-4 h-4 text-white" />
                <span className="text-sm text-gray-300">{item.label}</span>
              </a>
            ))}
          </div>
        </div>
      </div>

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
                      <div className="markdown-body">
                        <ProfessionalMarkdownRenderer content={message.content} />
                      </div>
                    )}
                  </div>
                  <div className="flex items-center justify-between mt-1.5">
                    <div className="text-xs text-gray-500 px-2">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                    {!message.isTyping && (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={async () => {
                            try {
                              await navigator.clipboard.writeText(message.content)
                              setCopiedId(message.id)
                              setTimeout(() => setCopiedId(null), 2000)
                              toast.success('Copied to clipboard')
                            } catch (err) {
                              console.error('Failed to copy to clipboard:', err)
                              toast.error('Failed to copy to clipboard')
                            }
                          }}
                          className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors"
                        >
                          {copiedId === message.id ? (
                            <Check className="w-3.5 h-3.5" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                          <span>{copiedId === message.id ? 'Copied!' : 'Copy'}</span>
                        </button>
                        <button
                          onClick={() => {
                            setInput(message.content)
                            setEditingPromptId(message.id)
                            textareaRef.current?.focus()
                          }}
                          className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                          <span>Edit</span>
                        </button>
                      </div>
                    )}
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

      {/* Offline Code Queue Indicator */}
      {queueVisible && codeQueue.length > 0 && (
        <div className="px-6 py-2 bg-amber-950/50 border-t border-amber-800/50">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-amber-400">
              <Code2 className="w-4 h-4" />
              <span>
                <strong>{codeQueue.length}</strong> code prompt{codeQueue.length > 1 ? 's' : ''} queued for full AI generation
              </span>
            </div>
            <div className="flex items-center gap-3">
              {!isOnline && (
                <span className="text-amber-300">
                  Waiting for connection...
                </span>
              )}
              {isOnline && (
                <span className="text-emerald-400">
                  Generating...
                </span>
              )}
              <button
                onClick={() => {
                  setCodeQueue([])
                  setQueueVisible(false)
                }}
                className="text-amber-400 hover:text-white transition-colors text-xs"
              >
                Clear
              </button>
            </div>
          </div>
        </div>
      )}

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
              className="flex-1 bg-transparent border-0 outline-none resize-none px-4 py-3 text-white placeholder-gray-500 min-h-[120px]"
              rows={1}
              disabled={loading || isProcessingVoice}
            />
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={loading || isProcessingVoice}
              className={`p-3 rounded-xl transition-all ${
                isRecording
                  ? 'bg-red-500/20 text-red-400 animate-pulse'
                  : 'bg-gray-700/50 text-gray-400 hover:text-white hover:bg-gray-700'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              title={isRecording ? 'Stop recording' : 'Voice input'}
            >
              {isProcessingVoice ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : isRecording ? (
                <StopCircle className="w-5 h-5" />
              ) : (
                <Mic className="w-5 h-5" />
              )}
            </button>
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading || isProcessingVoice}
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

    </div>
    </>
  )
}
