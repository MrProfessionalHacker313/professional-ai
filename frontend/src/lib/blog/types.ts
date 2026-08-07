export type BlogSectionType = 'heading' | 'paragraph' | 'list' | 'steps' | 'example' | 'screenshot' | 'table' | 'quote'

export interface BlogSection {
  type: BlogSectionType
  content?: string
  items?: string[]
  caption?: string
  cols?: string[]
  rows?: string[][]
}

export interface BlogFAQ {
  question: string
  answer: string
}

export interface BlogTranslation {
  title: string
  summary: string
}

export interface BlogArticle {
  slug: string
  title: string
  headline: string
  intro: string
  category: string
  tagline: string
  tags: string[]
  author: string
  date: string
  updatedDate: string
  readTime: string
  metaDescription: string
  keywords: string[]
  coverGradient: string
  coverIcon: string
  sections: BlogSection[]
  faq: BlogFAQ[]
  translations: {
    ur: BlogTranslation
    hi: BlogTranslation
  }
  related: string[]
}

export const BLOG_CATEGORIES = [
  { id: 'ai-news', label: 'AI News' },
  { id: 'coding-tutorials', label: 'Coding Tutorials' },
  { id: 'security-guides', label: 'Security Guides' },
  { id: 'media-ai-videos', label: 'Media / AI Videos' },
  { id: 'product-updates', label: 'Product Updates' },
] as const