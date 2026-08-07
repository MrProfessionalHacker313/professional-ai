import type { BlogArticle } from './types'
import { ARTICLES_1_4 } from './articles/articles-1-4'
import { ARTICLES_5_8 } from './articles/articles-5-8'
import { ARTICLES_9_12 } from './articles/articles-9-12'

export const BLOG_ARTICLES: BlogArticle[] = [
  ...ARTICLES_1_4,
  ...ARTICLES_5_8,
  ...ARTICLES_9_12,
]

export function getAllArticles(): BlogArticle[] {
  return BLOG_ARTICLES
}

export function getArticleBySlug(slug: string): BlogArticle | undefined {
  return BLOG_ARTICLES.find((article) => article.slug === slug)
}

export function getArticlesByCategory(category: string): BlogArticle[] {
  return BLOG_ARTICLES.filter((article) => article.category === category)
}

export function getRelatedArticles(article: BlogArticle, limit = 3): BlogArticle[] {
  const related = article.related
    .map((slug) => BLOG_ARTICLES.find((a) => a.slug === slug))
    .filter((a): a is BlogArticle => Boolean(a))

  if (related.length >= limit) {
    return related.slice(0, limit)
  }

  // Fall back to same-category articles
  const sameCategory = BLOG_ARTICLES.filter(
    (a) => a.category === article.category && a.slug !== article.slug
  )
  const fillers = sameCategory.filter((a) => !related.some((r) => r.slug === a.slug))

  return [...related, ...fillers].slice(0, limit)
}

export function searchArticles(query: string): BlogArticle[] {
  const q = query.toLowerCase().trim()
  if (!q) return BLOG_ARTICLES

  return BLOG_ARTICLES.filter((article) => {
    const searchable = [
      article.title,
      article.intro,
      article.metaDescription,
      article.category,
      article.tags.join(' '),
      article.keywords.join(' '),
      article.translations.ur.title,
      article.translations.ur.summary,
      article.translations.hi.title,
      article.translations.hi.summary,
    ]
      .join(' ')
      .toLowerCase()

    return searchable.includes(q)
  })
}