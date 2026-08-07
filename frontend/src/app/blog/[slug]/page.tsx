import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import Script from 'next/script'
import { Calendar, Clock, ChevronRight, CheckCircle2, MessageCircle, ThumbsUp } from 'lucide-react'
import { SITE_URL } from '@/lib/seo/locales'
import { BLOG_ARTICLES, getArticleBySlug, getRelatedArticles } from '@/lib/blog'
import { BLOG_CATEGORIES } from '@/lib/blog/types'

type PageProps = {
  params: { slug: string }
}

export function generateStaticParams() {
  return BLOG_ARTICLES.map((article) => ({ slug: article.slug }))
}

export function generateMetadata({ params }: PageProps): Metadata {
  const article = getArticleBySlug(params.slug)
  if (!article) return {}

  const categoryLabel = BLOG_CATEGORIES.find((c) => c.id === article.category)?.label || article.category

  return {
    title: `${article.title} | Professional AI Blog`,
    description: article.metaDescription,
    keywords: article.keywords,
    authors: [{ name: article.author }],
    category: categoryLabel,
    alternates: { canonical: `${SITE_URL}/blog/${article.slug}` },
    openGraph: {
      title: article.title,
      description: article.metaDescription,
      type: 'article',
      url: `${SITE_URL}/blog/${article.slug}`,
      siteName: 'Professional AI',
      locale: 'en_US',
      publishedTime: article.date,
      modifiedTime: article.updatedDate,
      authors: [article.author],
      tags: article.tags,
      images: [{ url: `${SITE_URL}/og-image.png`, width: 1200, height: 630, alt: article.title }],
    },
    twitter: {
      card: 'summary_large_image',
      title: article.title,
      description: article.metaDescription,
      images: [`${SITE_URL}/og-image.png`],
    },
  }
}

function buildSchemas(article: ReturnType<typeof getArticleBySlug>) {
  if (!article) return []
  const url = `${SITE_URL}/blog/${article.slug}`
  const categoryLabel = BLOG_CATEGORIES.find((c) => c.id === article.category)?.label || article.category

  const post = {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: article.headline,
    description: article.metaDescription,
    datePublished: article.date,
    dateModified: article.updatedDate,
    author: { '@type': 'Organization', name: article.author, url: SITE_URL },
    publisher: {
      '@type': 'Organization',
      name: 'Professional AI',
      logo: { '@type': 'ImageObject', url: `${SITE_URL}/logo.png` },
    },
    mainEntityOfPage: { '@type': 'WebPage', '@id': url },
    keywords: article.keywords.join(', '),
    articleSection: categoryLabel,
    inLanguage: 'en',
    about: article.tags,
  }

  const breadcrumb = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
      { '@type': 'ListItem', position: 2, name: 'Blog', item: `${SITE_URL}/blog` },
      { '@type': 'ListItem', position: 3, name: article.title, item: url },
    ],
  }

  return [
    post,
    breadcrumb,
    article.faq.length > 0 && {
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: article.faq.map((item) => ({
        '@type': 'Question',
        name: item.question,
        acceptedAnswer: { '@type': 'Answer', text: item.answer },
      })),
    },
  ].filter(Boolean)
}

export default function BlogPostPage({ params }: PageProps) {
  const article = getArticleBySlug(params.slug)
  if (!article) notFound()

  const related = getRelatedArticles(article)
  const categoryLabel = BLOG_CATEGORIES.find((c) => c.id === article.category)?.label || article.category
  const canonicalUrl = `${SITE_URL}/blog/${article.slug}`
  const schemas = buildSchemas(article)

  const shareLinks = {
    whatsapp: `https://wa.me/?text=${encodeURIComponent(`${article.title} — ${canonicalUrl}`)}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(canonicalUrl)}`,
    twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(article.title)}&url=${encodeURIComponent(canonicalUrl)}`,
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {schemas.map((schema, i) => (
        <Script key={i} id={`blog-schema-${i}`} type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
      ))}

      <article className="max-w-4xl mx-auto px-4 pt-12 pb-8">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-gray-500 mb-8">
          <Link href="/" className="hover:text-cyan-400 transition-colors">Home</Link>
          <ChevronRight className="w-4 h-4" />
          <Link href="/blog" className="hover:text-cyan-400 transition-colors">Blog</Link>
          <ChevronRight className="w-4 h-4" />
          <span className="text-gray-400 line-clamp-1">{article.title}</span>
        </nav>

        {/* Cover */}
        <div className="relative overflow-hidden rounded-3xl border border-gray-800 mb-10">
          <div className={`absolute inset-0 bg-gradient-to-br ${article.coverGradient} opacity-25`} />
          <div className="absolute inset-0 bg-gradient-to-t from-gray-950 via-transparent to-transparent" />
          <div className="relative p-8 md:p-12">
            <div className="flex flex-wrap items-center gap-3 mb-6">
              <Link
                href={`/blog?category=${article.category}`}
                className="px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-medium hover:bg-cyan-500/20 transition-colors"
              >
                {categoryLabel}
              </Link>
              <span className="text-xs text-gray-400 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5" /> {article.date}
              </span>
              <span className="text-xs text-gray-400 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5" /> {article.readTime}
              </span>
            </div>
            <h1 className="text-3xl md:text-5xl font-bold leading-tight mb-5">{article.headline}</h1>
            <p className="text-gray-300 text-lg leading-relaxed mb-6">{article.intro}</p>
            <div className="flex items-center gap-3 pt-5 border-t border-gray-800/60">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-sm font-bold">PA</div>
              <div>
                <p className="text-sm font-medium">{article.author}</p>
                <p className="text-xs text-gray-500">Professional AI Editorial</p>
              </div>
            </div>
          </div>
        </div>

        {/* Share Buttons */}
        <div className="flex items-center gap-3 mb-10">
          <span className="text-sm text-gray-500 mr-2">Share:</span>
          <a
            href={shareLinks.whatsapp}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-green-600/20 border border-green-600/30 text-green-400 text-sm font-medium hover:bg-green-600/30 transition-all"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
            WhatsApp
          </a>
          <a
            href={shareLinks.facebook}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600/20 border border-blue-600/30 text-blue-400 text-sm font-medium hover:bg-blue-600/30 transition-all"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
            Facebook
          </a>
          <a
            href={shareLinks.twitter}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-700/20 border border-gray-600/30 text-gray-300 text-sm font-medium hover:bg-gray-700/30 transition-all"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
            X
          </a>
        </div>

        {/* Article Body */}
        <div className="space-y-8">
          {article.sections.map((section, index) => {
            switch (section.type) {
              case 'heading':
                return (
                  <h2 key={index} className="text-2xl md:text-3xl font-bold pt-4 border-t border-gray-800/40 first:border-0 first:pt-0">
                    {section.content}
                  </h2>
                )
              case 'paragraph':
                return (
                  <p key={index} className="text-gray-300 leading-8 text-lg">{section.content}</p>
                )
              case 'list':
                return (
                  <ul key={index} className="space-y-3">
                    {section.items?.map((item, i) => (
                      <li key={i} className="flex items-start gap-3 text-gray-300 leading-7">
                        <CheckCircle2 className="w-5 h-5 text-cyan-400 shrink-0 mt-1" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                )
              case 'steps':
                return (
                  <ol key={index} className="space-y-4">
                    {section.items?.map((item, i) => (
                      <li key={i} className="flex items-start gap-4 glass-card p-5 rounded-xl border border-gray-800">
                        <span className="w-8 h-8 shrink-0 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-sm font-bold">
                          {i + 1}
                        </span>
                        <p className="text-gray-300 leading-7 pt-1">{item}</p>
                      </li>
                    ))}
                  </ol>
                )
              case 'example':
                return (
                  <div key={index} className="glass-card p-6 rounded-2xl border border-gray-800">
                    <p className="text-xs text-cyan-400 font-semibold uppercase tracking-wider mb-3">Example</p>
                    <p className="text-gray-300 leading-7 font-mono text-sm whitespace-pre-wrap">{section.content}</p>
                    {section.caption && <p className="text-xs text-gray-500 mt-4 italic">{section.caption}</p>}
                  </div>
                )
              case 'screenshot':
                return (
                  <figure key={index} className="glass-card rounded-2xl border border-gray-800 overflow-hidden">
                    <div className={`h-56 md:h-72 bg-gradient-to-br ${article.coverGradient} opacity-30 flex items-center justify-center`}>
                      <div className="text-center px-6">
                        <div className="text-5xl mb-3">🖥️</div>
                        <p className="text-sm text-gray-300 font-mono">{section.content}</p>
                      </div>
                    </div>
                    {section.caption && (
                      <figcaption className="px-6 py-4 text-sm text-gray-500 border-t border-gray-800/60">{section.caption}</figcaption>
                    )}
                  </figure>
                )
              case 'table':
                return (
                  <div key={index} className="glass-card rounded-2xl border border-gray-800 overflow-hidden">
                    {section.caption && (
                      <p className="px-6 py-4 text-sm font-semibold text-cyan-400 border-b border-gray-800/60">{section.caption}</p>
                    )}
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-gray-800">
                            {section.cols?.map((col, i) => (
                              <th key={i} className="text-left px-6 py-3 text-gray-400 font-medium">{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {section.rows?.map((row, i) => (
                            <tr key={i} className="border-b border-gray-800/50 last:border-0 hover:bg-gray-900/40">
                              {row.map((cell, j) => (
                                <td key={j} className={`px-6 py-3 text-gray-300 ${j === 0 ? 'font-medium text-white' : ''}`}>{cell}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )
              case 'quote':
                return (
                  <blockquote key={index} className="glass-card p-6 md:p-8 rounded-2xl border-l-4 border-l-cyan-500 border border-gray-800">
                    <p className="text-gray-200 text-lg leading-8 italic">&ldquo;{section.content}&rdquo;</p>
                  </blockquote>
                )
              default:
                return null
            }
          })}
        </div>

        {/* Tags */}
        <div className="mt-10 pt-6 border-t border-gray-800 flex flex-wrap gap-2">
          {article.tags.map((tag) => (
            <span key={tag} className="px-3 py-1.5 rounded-lg bg-gray-900/60 border border-gray-800 text-xs text-gray-400">#{tag}</span>
          ))}
        </div>

        {/* CTA Block */}
        <div className="mt-12 relative overflow-hidden rounded-3xl border border-cyan-500/20 bg-gradient-to-br from-blue-950 via-gray-950 to-purple-950 p-8 md:p-12 text-center">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl" />
          <div className="relative">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Ready to <span className="text-gradient">Build. Create. Secure?</span>
            </h2>
            <p className="text-gray-400 text-lg max-w-xl mx-auto mb-8">
              Start Free — 3-day PRO trial. Unlimited generations, 4K/8K media export, security scanner, offline mode, and AI in 40+ languages.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/login?tab=register"
                className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all glow"
              >
                Start Free — 3-day PRO trial
              </Link>
              <Link
                href="/pricing"
                className="inline-flex items-center gap-2 border border-gray-700 hover:border-gray-500 text-gray-300 px-8 py-4 rounded-xl font-semibold text-lg transition-all"
              >
                View Pricing
              </Link>
            </div>
          </div>
        </div>

        {/* FAQ Block */}
        {article.faq.length > 0 && (
          <div className="mt-12">
            <h2 className="text-3xl font-bold mb-6">Frequently Asked Questions</h2>
            <div className="space-y-4">
              {article.faq.map((faqItem, i) => (
                <details key={i} className="group glass-card rounded-2xl border border-gray-800 overflow-hidden">
                  <summary className="flex items-center justify-between gap-4 px-6 py-5 cursor-pointer text-lg font-medium hover:text-cyan-400 transition-colors">
                    {faqItem.question}
                    <span className="text-cyan-400 transition-transform group-open:rotate-45 text-2xl shrink-0">+</span>
                  </summary>
                  <p className="px-6 pb-6 text-gray-300 leading-7">{faqItem.answer}</p>
                </details>
              ))}
            </div>
          </div>
        )}

        {/* Translation Block */}
        <div className="mt-12 grid md:grid-cols-2 gap-6">
          <div className="glass-card rounded-2xl border border-gray-800 p-6">
            <p className="font-urdu text-lg mb-3" dir="rtl">اردو خلاصہ</p>
            <h3 className="font-urdu text-xl font-bold mb-3 leading-relaxed" dir="rtl">{article.translations.ur.title}</h3>
            <p className="font-urdu text-gray-300 leading-8" dir="rtl">{article.translations.ur.summary}</p>
          </div>
          <div className="glass-card rounded-2xl border border-gray-800 p-6">
            <p className="font-hindi text-lg mb-3">हिंदी सारांश</p>
            <h3 className="font-hindi text-xl font-bold mb-3 leading-relaxed">{article.translations.hi.title}</h3>
            <p className="font-hindi text-gray-300 leading-8">{article.translations.hi.summary}</p>
          </div>
        </div>

        {/* Related Articles */}
        <div className="mt-12">
          <h2 className="text-3xl font-bold mb-6">Related Articles</h2>
          <div className="grid md:grid-cols-3 gap-5">
            {related.map((item) => (
              <Link
                key={item.slug}
                href={`/blog/${item.slug}`}
                className="group glass-card p-5 rounded-2xl border border-gray-800 hover:border-cyan-500/30 transition-all hover:-translate-y-1"
              >
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${item.coverGradient} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <span className="text-white text-lg">📄</span>
                </div>
                <h3 className="font-semibold text-sm leading-snug group-hover:text-blue-400 transition-colors line-clamp-3">{item.title}</h3>
                <p className="mt-3 text-xs text-gray-500">{item.readTime}</p>
              </Link>
            ))}
          </div>
        </div>

        {/* Comments Section */}
        <div className="mt-12 glass-card rounded-2xl border border-gray-800 p-8">
          <div className="flex items-center gap-3 mb-6">
            <MessageCircle className="w-6 h-6 text-cyan-400" />
            <h2 className="text-2xl font-bold">Comments</h2>
          </div>
          <div className="mb-6 space-y-4">
            <textarea
              placeholder="Share your thoughts... (sign in to comment)"
              className="w-full bg-gray-900/70 border border-gray-800 focus:border-cyan-500/50 rounded-xl px-4 py-3 text-white placeholder-gray-500 outline-none transition-all"
              rows={4}
            />
            <div className="flex items-center justify-between">
              <button className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-2.5 rounded-xl text-sm font-medium hover:from-blue-500 hover:to-purple-500 transition-all">
                Post Comment
              </button>
              <Link href="/login" className="text-sm text-cyan-400 hover:text-cyan-300">Sign in first</Link>
            </div>
          </div>
          <div className="space-y-4">
            <div className="glass-card rounded-xl border border-gray-800 p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center text-xs font-bold">AK</div>
                <div>
                  <p className="text-sm font-medium">Ayesha Khan</p>
                  <p className="text-xs text-gray-500">2 days ago</p>
                </div>
              </div>
              <p className="text-gray-300 text-sm leading-6">
                This was exactly what I needed! I used the 10-minute app tutorial to build my first project. Highly recommend.
              </p>
              <button className="mt-3 inline-flex items-center gap-1.5 text-xs text-gray-500 hover:text-cyan-400 transition-colors">
                <ThumbsUp className="w-3.5 h-3.5" /> Helpful (12)
              </button>
            </div>
            <div className="glass-card rounded-xl border border-gray-800 p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-teal-600 flex items-center justify-center text-xs font-bold">UR</div>
                <div>
                  <p className="text-sm font-medium">Usman R.</p>
                  <p className="text-xs text-gray-500">5 days ago</p>
                </div>
              </div>
              <p className="text-gray-300 text-sm leading-6">
                The Urdu translation section is a great touch. Finally an AI platform that takes South Asian users seriously!
              </p>
              <button className="mt-3 inline-flex items-center gap-1.5 text-xs text-gray-500 hover:text-cyan-400 transition-colors">
                <ThumbsUp className="w-3.5 h-3.5" /> Helpful (8)
              </button>
            </div>
          </div>
        </div>
      </article>
    </div>
  )
}