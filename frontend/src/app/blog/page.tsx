'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import { Search, Clock, BookOpen, ArrowRight, Calendar, User, Feather } from 'lucide-react'
import { BLOG_ARTICLES, searchArticles } from '@/lib/blog'
import { BLOG_CATEGORIES } from '@/lib/blog/types'

export default function BlogPage() {
  const [query, setQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState<string>('all')

  const filteredArticles = useMemo(() => {
    const searched = searchArticles(query)
    if (activeCategory === 'all') return searched
    return searched.filter((a) => a.category === activeCategory)
  }, [query, activeCategory])

  const featured = BLOG_ARTICLES[0]

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Hero Banner */}
      <section className="relative overflow-hidden pt-20 pb-16 px-4">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-950 via-gray-950 to-purple-950" />
        <div className="absolute top-10 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl animate-pulse-glow" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl" />
        <div className="relative max-w-6xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 mb-6 px-4 py-2 rounded-full bg-gray-900/60 border border-gray-800 backdrop-blur-xl">
            <Feather className="w-4 h-4 text-cyan-400" />
            <span className="text-sm text-gray-300">Professional AI Knowledge Hub</span>
          </div>
          <h1 className="text-4xl md:text-6xl font-bold mb-4">
            Professional AI Blog
          </h1>
          <p className="text-xl md:text-2xl font-semibold mb-6 text-gradient">
            Learn. Build. Conquer.
          </p>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto mb-10">
            In-depth tutorials, security guides, media workflows, product updates, and AI news —
            written for professionals who build, create, and secure with AI.
          </p>

          {/* Search Box */}
          <div className="max-w-xl mx-auto">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search articles — try 'Urdu', 'code', 'security', 'video'..."
                className="w-full bg-gray-900/70 border border-gray-800 focus:border-cyan-500/50 rounded-2xl pl-12 pr-4 py-4 text-white placeholder-gray-500 outline-none transition-all backdrop-blur-xl"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Category Filter */}
      <section className="px-4 pb-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-wrap gap-3 justify-center">
            <button
              onClick={() => setActiveCategory('all')}
              className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all border ${
                activeCategory === 'all'
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 border-transparent text-white glow'
                  : 'bg-gray-900/60 border-gray-800 text-gray-400 hover:text-white hover:border-gray-600'
              }`}
            >
              All Articles
            </button>
            {BLOG_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id)}
                className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all border ${
                  activeCategory === cat.id
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 border-transparent text-white glow'
                    : 'bg-gray-900/60 border-gray-800 text-gray-400 hover:text-white hover:border-gray-600'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Article */}
      {activeCategory === 'all' && !query && (
        <section className="px-4 pb-12">
          <div className="max-w-6xl mx-auto">
            <Link
              href={`/blog/${featured.slug}`}
              className="group block relative overflow-hidden rounded-3xl border border-gray-800 hover:border-cyan-500/30 transition-all"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${featured.coverGradient} opacity-20 group-hover:opacity-30 transition-opacity`} />
              <div className="relative p-8 md:p-12">
                <div className="flex items-center gap-3 mb-4">
                  <span className="px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-medium">
                    Featured Article
                  </span>
                  <span className="text-xs text-gray-500 flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    {featured.date}
                  </span>
                  <span className="text-xs text-gray-500 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    {featured.readTime}
                  </span>
                </div>
                <h2 className="text-3xl md:text-4xl font-bold mb-4 group-hover:text-blue-400 transition-colors">
                  {featured.title}
                </h2>
                <p className="text-gray-400 text-lg max-w-3xl mb-6">{featured.intro}</p>
                <div className="flex items-center gap-2 text-cyan-400 font-medium">
                  Read article <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </Link>
          </div>
        </section>
      )}

      {/* Articles Grid */}
      <section className="px-4 pb-20">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredArticles.map((article) => (
              <Link
                key={article.slug}
                href={`/blog/${article.slug}`}
                className="group glass-card p-6 rounded-2xl hover:border-cyan-500/30 transition-all hover:-translate-y-1"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${article.coverGradient} flex items-center justify-center mb-5 group-hover:scale-110 transition-transform`}>
                  <BookOpen className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-3 leading-snug group-hover:text-blue-400 transition-colors line-clamp-3">
                  {article.title}
                </h3>
                <p className="text-sm text-gray-400 mb-4 line-clamp-3">{article.intro}</p>
                <div className="flex items-center justify-between text-xs text-gray-500 pt-4 border-t border-gray-800/50">
                  <span className="flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5" />
                    {article.author}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    {article.readTime}
                  </span>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {article.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="px-2.5 py-1 rounded-lg bg-gray-900/60 border border-gray-800 text-xs text-gray-400">
                      #{tag}
                    </span>
                  ))}
                </div>
              </Link>
            ))}
          </div>

          {filteredArticles.length === 0 && (
            <div className="text-center py-20">
              <div className="text-5xl mb-4">🔍</div>
              <h3 className="text-2xl font-semibold mb-2">No articles found</h3>
              <p className="text-gray-400">
                Try a different search term or category.
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Translation Note */}
      <section className="px-4 pb-20">
        <div className="max-w-6xl mx-auto">
          <div className="glass-card p-8 rounded-2xl border border-gray-800 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <h3 className="text-2xl font-bold mb-2">
                Want this in <span className="text-gradient">Urdu or Hindi?</span>
              </h3>
              <p className="text-gray-400">
                Every article includes a summary version in Urdu (اردو) and Hindi (हिंदी).
                Open any article and scroll to the bottom for the translation block.
              </p>
            </div>
            <div className="flex gap-3 shrink-0">
              <span className="font-urdu px-4 py-2 rounded-xl bg-gray-800/60 border border-gray-700 text-lg" dir="rtl">
                اردو
              </span>
              <span className="font-hindi px-4 py-2 rounded-xl bg-gray-800/60 border border-gray-700 text-lg">
                हिंदी
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}