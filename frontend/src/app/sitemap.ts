import type { MetadataRoute } from 'next'
import { CONTENT_CALENDAR_90_DAYS } from '@/lib/seo/contentCalendar'
import { BLOG_ARTICLES } from '@/lib/blog'

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://professionalai.com'

const localizedPaths = [
  '/',
  '/chat',
  '/pricing',
  '/features',
  '/login',
  '/download',
  '/blog',
]

const localeCodes = [
  'en', 'ur', 'hi', 'bn', 'pa', 'ps', 'sd', 'ar', 'fa', 'tr',
  'zh', 'ja', 'ko', 'ru', 'fr', 'de', 'es', 'it', 'pt', 'nl',
  'pl', 'uk', 'el', 'he', 'id', 'ms', 'th', 'vi', 'sw', 'tl',
  'ne', 'si', 'ta', 'te', 'gu', 'mr', 'ku', 'uz', 'kk', 'my', 'km',
]

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date()
  const staticPages: MetadataRoute.Sitemap = [
    {
      url: `${SITE_URL}/`,
      lastModified: now,
      changeFrequency: 'daily',
      priority: 1,
    },
    {
      url: `${SITE_URL}/pricing`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 0.9,
    },
    {
      url: `${SITE_URL}/features`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 0.9,
    },
    {
      url: `${SITE_URL}/download`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/chat`,
      lastModified: now,
      changeFrequency: 'daily',
      priority: 0.9,
    },
    {
      url: `${SITE_URL}/login`,
      lastModified: now,
      changeFrequency: 'monthly',
      priority: 0.5,
    },
    {
      url: `${SITE_URL}/blog`,
      lastModified: now,
      changeFrequency: 'daily',
      priority: 0.8,
    },
  ]

  const localePages: MetadataRoute.Sitemap = []
  for (const path of localizedPaths) {
    for (const locale of localeCodes) {
      const query = path === '/' ? `?lang=${locale}` : `${path}?lang=${locale}`
      localePages.push({
        url: `${SITE_URL}${query}`,
        lastModified: now,
        changeFrequency: 'weekly',
        priority: path === '/' ? 0.8 : 0.6,
      })
    }
  }

  const calendarBlogPages: MetadataRoute.Sitemap = CONTENT_CALENDAR_90_DAYS.map((post) => ({
    url: `${SITE_URL}/blog/${post.slug}`,
    lastModified: new Date(`${post.date}T00:00:00.000Z`),
    changeFrequency: 'weekly',
    priority: 0.7,
  }))

  const professionalBlogPages: MetadataRoute.Sitemap = BLOG_ARTICLES.map((article) => ({
    url: `${SITE_URL}/blog/${article.slug}`,
    lastModified: new Date(`${article.updatedDate}T00:00:00.000Z`),
    changeFrequency: 'monthly',
    priority: 0.9,
  }))

  return [...staticPages, ...localePages, ...calendarBlogPages, ...professionalBlogPages]
}