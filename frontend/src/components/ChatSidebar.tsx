'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus,
  Search,
  MessageSquare,
  Trash2,
  Edit3,
  X,
  Check,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { conversationsApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

interface ChatSidebarProps {
  isOpen: boolean
  onToggle: () => void
  currentConversationId: string | null
  onSelectConversation: (conversationId: string) => void
  onNewConversation: () => void
  onConversationDeleted: () => void
}

export default function ChatSidebar({
  isOpen,
  onToggle,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onConversationDeleted,
}: ChatSidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (mounted) {
      loadConversations()
    }
  }, [])

  useEffect(() => {
    if (isOpen && mounted) {
      loadConversations()
    }
  }, [isOpen])

  const loadConversations = async () => {
    try {
      setLoading(true)
      const response = await conversationsApi.list({ search: searchQuery || undefined })
      setConversations(response.data)
    } catch (error) {
      console.error('Failed to load conversations:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const debounce = setTimeout(() => {
      if (isOpen && mounted) {
        loadConversations()
      }
    }, 300)
    return () => clearTimeout(debounce)
  }, [searchQuery])

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    
    if (!confirm('Delete this conversation permanently?')) {
      return
    }

    try {
      await conversationsApi.delete(id)
      setConversations(prev => prev.filter(c => c.id !== id))
      toast.success('Conversation deleted')
      
      if (currentConversationId === id) {
        onConversationDeleted()
      }
    } catch (error) {
      toast.error('Failed to delete conversation')
    }
  }

  const handleRename = async (id: string, e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation()
    
    if (!editTitle.trim()) {
      setEditingId(null)
      return
    }

    try {
      const response = await conversationsApi.rename(id, { title: editTitle.trim() })
      setConversations(prev => prev.map(c => 
        c.id === id ? { ...c, title: response.data.title } : c
      ))
      toast.success('Conversation renamed')
      setEditingId(null)
    } catch (error) {
      toast.error('Failed to rename conversation')
    }
  }

  const startEditing = (conv: Conversation, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(conv.id)
    setEditTitle(conv.title)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    // Use a fixed reference date during SSR to avoid hydration mismatch
    const now = mounted ? new Date() : new Date(dateString)
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    if (days < 7) return `${days} days ago`
    // Use UTC-based formatting to avoid server/client timezone mismatch
    // Only use locale formatting after mount
    if (!mounted) {
      const month = date.getUTCMonth()
      const day = date.getUTCDate()
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
      return `${months[month]} ${day}`
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return (
    <>
      {/* Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onToggle}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.div
        initial={false}
        animate={{ x: isOpen ? 0 : '-100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="fixed left-0 top-0 h-full w-80 bg-gray-900 border-r border-gray-800 z-50 flex flex-col"
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-white">Chat History</h2>
            <button
              onClick={onToggle}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors lg:hidden"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          {/* New Chat Button */}
          <button
            onClick={() => {
              onNewConversation()
              onToggle()
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 rounded-xl text-white font-medium transition-all"
          >
            <Plus className="w-5 h-5" />
            New Chat
          </button>
        </div>

        {/* Search */}
        <div className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search conversations..."
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto px-4 pb-4">
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-16 bg-gray-800 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : conversations.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No conversations yet</p>
            </div>
          ) : (
            <div className="space-y-1">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => {
                    onSelectConversation(conv.id)
                    onToggle()
                  }}
                  className={`group relative p-3 rounded-lg cursor-pointer transition-all ${
                    currentConversationId === conv.id
                      ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/50'
                      : 'bg-gray-800/50 hover:bg-gray-800 border border-transparent'
                  }`}
                >
                  {editingId === conv.id ? (
                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleRename(conv.id, e)
                          } else if (e.key === 'Escape') {
                            setEditingId(null)
                          }
                        }}
                        autoFocus
                        className="flex-1 px-2 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:border-blue-500"
                      />
                      <button
                        onClick={(e) => handleRename(conv.id, e)}
                        className="p-1 hover:bg-gray-700 rounded"
                      >
                        <Check className="w-4 h-4 text-green-400" />
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-white truncate">
                            {conv.title}
                          </h3>
                          <p className="text-xs text-gray-400 mt-1">
                            {formatDate(conv.updated_at)} • {conv.message_count} messages
                          </p>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => startEditing(conv, e)}
                            className="p-1.5 hover:bg-gray-700 rounded transition-colors"
                            title="Rename"
                          >
                            <Edit3 className="w-3.5 h-3.5 text-gray-400" />
                          </button>
                          <button
                            onClick={(e) => handleDelete(conv.id, e)}
                            className="p-1.5 hover:bg-gray-700 rounded transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-3.5 h-3.5 text-red-400" />
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-800">
          <p className="text-xs text-gray-500 text-center">
            History stored encrypted
          </p>
        </div>
      </motion.div>

      {/* Toggle Button (when sidebar is closed) */}
      {!isOpen && (
        <button
          onClick={onToggle}
          className="fixed left-4 top-4 z-30 p-3 bg-gray-900 border border-gray-800 rounded-xl hover:bg-gray-800 transition-colors shadow-lg"
        >
          <ChevronRight className="w-5 h-5 text-gray-400" />
        </button>
      )}
    </>
  )
}