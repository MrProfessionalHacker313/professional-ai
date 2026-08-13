'use client'

import { useState, useEffect, useRef } from 'react'
import { Search, Code2, Shield, Languages, BookOpen, Loader2, Copy, Check } from 'lucide-react'
import { offlineSearch, SearchResult } from '@/lib/offline-search'
import { useConnectivity } from '@/lib/use-connectivity'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [searchUnavailable, setSearchUnavailable] = useState(false)
  const { isOnline } = useConnectivity()
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    // Preload the search index — SOFT FAIL: if init fails the page keeps working
    // and offline search shows "Offline search unavailable".
    offlineSearch.init().catch(() => setSearchUnavailable(true))
  }, [])

  const handleSearch = async (value: string) => {
    setQuery(value)
    if (debounceRef.current) clearTimeout(debounceRef.current)

    if (!value.trim()) {
      setResults([])
      setSearched(false)
      return
    }

    setLoading(true)
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await offlineSearch.search(value, 10)
        setResults(res)
        setSearched(true)
      } catch {
        // Soft failure — never block the page or throw to the console.
        setSearchUnavailable(true)
        setResults([])
        setSearched(true)
      } finally {
        setLoading(false)
      }
    }, 300)
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

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'coding': return <Code2 className="w-4 h-4" />
      case 'security': return <Shield className="w-4 h-4" />
      case 'languages': return <BookOpen className="w-4 h-4" />
      case 'translations': return <Languages className="w-4 h-4" />
      default: return <BookOpen className="w-4 h-4" />
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'coding': return 'from-green-500 to-emerald-600'
      case 'security': return 'from-purple-500 to-pink-600'
      case 'languages': return 'from-blue-500 to-cyan-600'
      case 'translations': return 'from-orange-500 to-amber-600'
      default: return 'from-gray-500 to-gray-600'
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">Offline Knowledge Search</h1>
          <p className="text-gray-400">
            {isOnline
              ? 'Searching local knowledge index + live sources'
              : '📴 Searching local knowledge index — works fully offline'}
          </p>
        </div>

        {/* Search input */}
        <div className="flex items-center gap-2 bg-gray-800/50 border border-gray-700/50 rounded-2xl p-3 mb-6">
          <Search className="w-5 h-5 text-gray-400 flex-shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search coding, security, languages, translations..."
            className="flex-1 bg-transparent border-0 outline-none text-white placeholder-gray-500"
            autoFocus
          />
          {loading && <Loader2 className="w-4 h-4 animate-spin text-gray-400" />}
        </div>

        {/* Results */}
        {searchUnavailable && (
          <div className="text-center py-12 text-amber-400 bg-amber-500/5 border border-amber-500/20 rounded-2xl mb-4">
            <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="font-semibold mb-1">Offline search unavailable</p>
            <p className="text-sm text-amber-500/80">
              The local knowledge index could not be loaded. The rest of the app keeps working normally.
            </p>
          </div>
        )}

        {!searchUnavailable && searched && results.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No results found. Try different keywords.</p>
          </div>
        )}

        <div className="space-y-4">
          {results.map((result) => (
            <div
              key={result.entry.id}
              className="bg-gray-900/50 border border-gray-800 rounded-2xl p-5 hover:border-gray-700 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 bg-gradient-to-br ${getCategoryColor(result.entry.category)} rounded-lg flex items-center justify-center flex-shrink-0`}>
                    {getCategoryIcon(result.entry.category)}
                  </div>
                  <div>
                    <h3 className="font-semibold">{result.entry.title}</h3>
                    <div className="text-xs text-gray-500">
                      {result.entry.category}
                      {result.entry.language ? ` · ${result.entry.language}` : ''}
                      {result.matchType === 'vector' && ' · semantic match'}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => copyToClipboard(result.entry.snippet, result.entry.id)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  {copiedId === result.entry.id ? (
                    <Check className="w-4 h-4 text-green-400" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </div>

              <p className="text-sm text-gray-300 mb-3">{result.entry.content}</p>

              <pre className="bg-gray-950 border border-gray-800 rounded-xl p-3 text-xs text-gray-300 overflow-x-auto mb-3">
                <code>{result.entry.snippet}</code>
              </pre>

              <div className="flex flex-wrap gap-2">
                {result.entry.tags.slice(0, 5).map((tag) => (
                  <span
                    key={tag}
                    className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded-full"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}