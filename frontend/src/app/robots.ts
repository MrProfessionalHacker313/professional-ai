import type { MetadataRoute } from 'next'

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://professionalai.com'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: ['/', '/chat', '/pricing', '/features', '/login', '/download', '/blog'],
        disallow: ['/admin', '/api/', '/profile', '/owner'],
      },
      {
        userAgent: 'Googlebot',
        allow: ['/', '/chat', '/pricing', '/features', '/login', '/download', '/blog'],
        disallow: ['/admin', '/api/', '/profile', '/owner'],
        crawlDelay: 0,
      },
    ],
    sitemap: [`${SITE_URL}/sitemap.xml`],
    host: SITE_URL,
  }
}
