/**
 * Professional AI - Offline Search Engine
 * FTS5-style full-text search + vector similarity over local knowledge packs.
 * Runs 100% on-device in IndexedDB. No internet required.
 */

export interface KnowledgeEntry {
  id: string
  title: string
  category: string
  language?: string
  tags: string[]
  content: string
  snippet: string
  answers: string[]
  vector?: number[]
}

export interface SearchResult {
  entry: KnowledgeEntry
  score: number
  matchedTerms: string[]
  matchType: 'fts' | 'vector' | 'answer'
}

interface SearchIndex {
  [term: string]: string[]  // term -> entry IDs
}

const DB_NAME = 'proai-offline'
const DB_VERSION = 1
const KNOWLEDGE_STORE = 'knowledge'
const INDEX_STORE = 'fts-index'

// Simple character n-gram hashing for vector generation (lightweight embedding)
// Each entry gets a 128-dim vector from hashed token n-grams.
const VECTOR_DIM = 128

function hashString(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0
    hash = Math.abs(hash)
  }
  return hash
}

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s+]/gu, ' ')
    .split(/\s+/)
    .filter((t) => t.length > 1)
}

export function generateVector(text: string): number[] {
  const tokens = tokenize(text)
  const vector = new Array(VECTOR_DIM).fill(0)
  for (const token of tokens) {
    for (let i = 0; i <= token.length - 2; i++) {
      const ngram = token.slice(i, i + 2)
      const idx = hashString(ngram) % VECTOR_DIM
      vector[idx] += 1
    }
    // Unigram contribution
    const uniIdx = hashString(token) % VECTOR_DIM
    vector[uniIdx] += 2
  }
  // Normalize (L2)
  const norm = Math.sqrt(vector.reduce((sum, v) => sum + v * v, 0)) || 1
  return vector.map((v) => v / norm)
}

export function cosineSimilarity(a: number[], b: number[]): number {
  if (!a || !b || a.length !== b.length) return 0
  let dot = 0
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i]
  }
  return dot
}

function stemTerm(term: string): string {
  // Lightweight Porter-style stemming (basic English)
  const t = term.toLowerCase()
  if (t.length <= 3) return t
  return t
    .replace(/(sses|ies)$/, (m) => m.endsWith('ies') ? 'y' : 'ss')
    .replace(/(ing|ed|es|s)$/, '')
    .replace(/(ational|tional)$/, 'ate')
}

class OfflineSearchEngine {
  private db: IDBDatabase | null = null
  private index: SearchIndex = {}
  private entries: Map<string, KnowledgeEntry> = new Map()
  private loaded = false
  private loading: Promise<void> | null = null

  async init(): Promise<void> {
    if (this.loaded) return
    if (this.loading) return this.loading

    this.loading = this._initInternal()
    return this.loading
  }

  private _failed = false

  private async _initInternal(): Promise<void> {
    try {
      await this._openDb()
      await this._loadIndex()
      if (this.entries.size === 0) {
        await this._buildIndexFromPacks()
      }
      this.loaded = true
      this._failed = false
    } catch (e) {
      console.warn('[OfflineSearch] init failed — falling back to safe mode:', e)
      // Soft failure: NEVER let a broken index block the page.
      this.loaded = true
      this._failed = true
      this.entries.clear()
      this.index = {}
    }
  }

  private _openDb(): Promise<void> {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION)
      req.onupgradeneeded = (ev) => {
        const db = (ev.target as IDBOpenDBRequest).result
        if (!db.objectStoreNames.contains(KNOWLEDGE_STORE)) {
          db.createObjectStore(KNOWLEDGE_STORE, { keyPath: 'id' })
        }
        if (!db.objectStoreNames.contains(INDEX_STORE)) {
          db.createObjectStore(INDEX_STORE, { keyPath: 'term' })
        }
      }
      req.onsuccess = () => {
        this.db = req.result
        resolve()
      }
      req.onerror = () => reject(req.error)
    })
  }

  private async _loadIndex(): Promise<void> {
    if (!this.db) return
    await new Promise<void>((resolve, reject) => {
      const tx = this.db!.transaction(INDEX_STORE, 'readonly')
      const store = tx.objectStore(INDEX_STORE)
      const req = store.getAll()
      req.onsuccess = () => {
        const items = req.result as { term: string; ids: string[] }[]
        for (const item of items) {
          this.index[item.term] = item.ids
        }
        resolve()
      }
      req.onerror = () => reject(req.error)
    })

    // Load entries
    await new Promise<void>((resolve, reject) => {
      const tx = this.db!.transaction(KNOWLEDGE_STORE, 'readonly')
      const store = tx.objectStore(KNOWLEDGE_STORE)
      const req = store.getAll()
      req.onsuccess = () => {
        const items = req.result as KnowledgeEntry[]
        for (const item of items) {
          this.entries.set(item.id, item)
        }
        resolve()
      }
      req.onerror = () => reject(req.error)
    })
  }

  private async _buildIndexFromPacks(): Promise<void> {
    const packs = [
      '/knowledge/coding-basics.json',
      '/knowledge/security.json',
      '/knowledge/languages.json',
      '/knowledge/translations.json',
    ]

    const allEntries: KnowledgeEntry[] = []
    for (const packUrl of packs) {
      try {
        const res = await fetch(packUrl, { cache: 'force-cache' })
        if (res.ok) {
          const data = await res.json()
          // DEFENSIVE: data must be an array, and each pack entry must be a valid object.
          if (Array.isArray(data)) {
            for (const item of data) {
              if (item && typeof item === 'object' && Array.isArray((item as KnowledgeEntry).tags) && Array.isArray((item as KnowledgeEntry).answers)) {
                allEntries.push(item as KnowledgeEntry)
              } else {
                console.warn('[OfflineSearch] Skipping invalid pack entry in', packUrl, item)
              }
            }
          } else {
            console.warn(`[OfflineSearch] Pack ${packUrl} is not an array — skipping`)
          }
        }
      } catch (e) {
        // Try cache API fallback
        try {
          const cache = await caches.open('proai-v1.0.0-knowledge')
          const cached = await cache.match(packUrl)
          if (cached) {
            const data = await cached.json()
            // Same defensive validation for cache fallback
            if (Array.isArray(data)) {
              for (const item of data) {
                if (item && typeof item === 'object' && Array.isArray((item as KnowledgeEntry).tags) && Array.isArray((item as KnowledgeEntry).answers)) {
                  allEntries.push(item as KnowledgeEntry)
                } else {
                  console.warn('[OfflineSearch] Skipping invalid cached pack entry in', packUrl, item)
                }
              }
            } else {
              console.warn(`[OfflineSearch] Cached pack ${packUrl} is not an array — skipping`)
            }
          }
        } catch (ce) {
          console.error(`[OfflineSearch] Failed to load ${packUrl}:`, ce)
        }
      }
    }

    // Build FTS index
    const newIndex: SearchIndex = {}
    for (const entry of allEntries) {
      this.entries.set(entry.id, entry)
      const searchable = [
        entry.title,
        entry.content,
        entry.snippet,
        ...entry.tags,
        ...entry.answers,
      ].join(' ')

      entry.vector = generateVector(searchable)

      const terms = new Set(tokenize(searchable).map(stemTerm))
      for (const term of terms) {
        // DEFENSIVE FIX: guard against `t[s].push is not a function`.
        // If the bucket is not an array (corrupt/stale index data), re-initialize it.
        let bucket = newIndex[term]
        if (!Array.isArray(bucket)) {
          bucket = []
          newIndex[term] = bucket
        }
        bucket.push(entry.id)
      }
    }

    this.index = newIndex

    // Persist to IDB
    if (this.db) {
      const tx = this.db.transaction([KNOWLEDGE_STORE, INDEX_STORE], 'readwrite')
      const kStore = tx.objectStore(KNOWLEDGE_STORE)
      const iStore = tx.objectStore(INDEX_STORE)

      for (const entry of allEntries) {
        kStore.put(entry)
      }
      for (const [term, ids] of Object.entries(this.index)) {
        iStore.put({ term, ids })
      }
    }
  }

  async search(query: string, limit = 10): Promise<SearchResult[]> {
    await this.init()
    if (!query.trim()) return []

    const queryTerms = tokenize(query).map(stemTerm)
    const results = new Map<string, SearchResult>()

    // 1. FTS match scoring
    for (const term of queryTerms) {
      const ids = this.index[term]
      if (!ids) continue
      for (const id of ids) {
        const entry = this.entries.get(id)
        if (!entry) continue

        const existing = results.get(id)
        const titleHit = entry.title.toLowerCase().includes(term)
        const tagHit = entry.tags.some((t) => t.toLowerCase().includes(term))
        const answerHit = entry.answers.some((a) => a.toLowerCase().includes(query.toLowerCase()))

        const score = existing?.score || 0
        const matched = existing?.matchedTerms || []
        if (!matched.includes(term)) matched.push(term)

        let delta = 1.0
        if (titleHit) delta += 3.0
        if (tagHit) delta += 2.0
        if (answerHit) delta += 4.0

        results.set(id, {
          entry,
          score: score + delta,
          matchedTerms: matched,
          matchType: answerHit ? 'answer' : 'fts',
        })
      }
    }

    // 2. Vector similarity fallback for queries with no FTS hits
    if (results.size === 0) {
      const queryVec = generateVector(query)
      for (const [id, entry] of this.entries) {
        if (!entry.vector) {
          const searchable = [entry.title, entry.content, entry.snippet, ...entry.tags, ...entry.answers].join(' ')
          entry.vector = generateVector(searchable)
        }
        const sim = cosineSimilarity(queryVec, entry.vector)
        if (sim > 0.15) {
          const existing = results.get(id)
          const score = existing ? Math.max(existing.score, sim * 10) : sim * 10
          results.set(id, {
            entry,
            score,
            matchedTerms: queryTerms,
            matchType: 'vector',
          })
        }
      }
    }

    // Rank results
    const ranked = [...results.values()].sort((a, b) => b.score - a.score)
    return ranked.slice(0, limit)
  }

  async getAllEntries(): Promise<KnowledgeEntry[]> {
    await this.init()
    return [...this.entries.values()]
  }

  async getEntry(id: string): Promise<KnowledgeEntry | undefined> {
    await this.init()
    return this.entries.get(id)
  }

  getStats(): { entries: number; indexTerms: number } {
    return {
      entries: this.entries.size,
      indexTerms: Object.keys(this.index).length,
    }
  }
}

export const offlineSearch = new OfflineSearchEngine()