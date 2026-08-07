import type { Metadata } from 'next'
import { SITE_URL } from '@/lib/seo/locales'

export const metadata: Metadata = {
  title: 'Professional AI Blog — Learn. Build. Conquer.',
  description:
    'Professional AI Blog — in-depth tutorials, cybersecurity guides, AI video workflows, product updates, and AI news for professionals. Articles available in English, Urdu, and Hindi.',
  keywords: [
    'professional ai blog',
    'ai in urdu',
    'ai in hindi',
    'ai coding tutorial',
    'ai security guide',
    'ai video generation',
    'best ai 2026',
  ],
  alternates: {
    canonical: `${SITE_URL}/blog`,
  },
  openGraph: {
    title: 'Professional AI Blog — Learn. Build. Conquer.',
    description:
      'Professional tutorials, security guides, media workflows, and AI news — in English, Urdu, and Hindi.',
    type: 'website',
    url: `${SITE_URL}/blog`,
    siteName: 'Professional AI',
    images: [
      {
        url: `${SITE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: 'Professional AI Blog',
      },
    ],
  },
}

export default function BlogLayout({ children }: { children: React.ReactNode }) {
  return children
}