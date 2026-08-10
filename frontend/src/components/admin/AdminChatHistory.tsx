'use client'

import { useState, useEffect } from 'react'
import { conversationsApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface Conversation {
  id: string
  title: string
  user_email: string
  user_id: string
  created_at: string
  updated_at: string
  message_count: number
}

export default function AdminChatHistory() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadConversations()
  }, [searchQuery])

  const loadConversations = async () => {
    try {
      setLoading(true)
      const response = await conversationsApi.adminListAll({ search: searchQuery || undefined })
      setConversations(response.data)
    } catch (error) {
      toast.error('Failed to load conversations')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this conversation permanently? This action cannot be undone.')) {
      return
    }

    try {
      await conversationsApi.adminDelete(id)
      setConversations(prev => prev.filter(c => c.id !== id))
      toast.success('Conversation deleted')
    } catch (error) {
      toast.error('Failed to delete conversation')
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Chat History Management</h2>
        <p className="text-slate-400">View and manage all user conversations across the platform</p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search conversations by title or user email..."
          className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
        />
      </div>

      {/* Conversations Table */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="h-16 bg-slate-800 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : conversations.length === 0 ? (
        <div className="text-center py-12 text-slate-400">
          <p>No conversations found</p>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-800 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Title
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  User
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Messages
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Last Updated
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {conversations.map((conv) => (
                <tr key={conv.id} className="hover:bg-slate-800/50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="text-sm font-medium text-white">{conv.title}</div>
                    <div className="text-xs text-slate-500 mt-1">ID: {conv.id.slice(0, 8)}...</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-slate-300">{conv.user_email}</div>
                    <div className="text-xs text-slate-500 mt-1">ID: {conv.user_id.slice(0, 8)}...</div>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-300">
                    {conv.message_count}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-400">
                    {formatDate(conv.created_at)}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-400">
                    {formatDate(conv.updated_at)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(conv.id)}
                      className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded-lg transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Stats */}
      {!loading && conversations.length > 0 && (
        <div className="mt-6 text-sm text-slate-400">
          Showing {conversations.length} conversation{conversations.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  )
}