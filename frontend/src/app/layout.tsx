import type { Metadata } from 'next'
import { Inter, Noto_Nastaliq_Urdu, Noto_Sans_Arabic, Noto_Sans_Devanagari, Noto_Sans_Bengali } from 'next/font/google'
import { ThemeProvider } from '@/components/ThemeProvider'
import { LanguageProvider } from '@/components/LanguageProvider'
import './globals.css'
import { Toaster } from 'react-hot-toast'
import VersionFooter from '@/components/VersionFooter'
import { HREFLANG_MAP, SITE_URL } from '@/lib/seo/locales'
import {
  organizationSchema,
  softwareSchema,
  faqSchema,
  reviewSchema,
  websiteSchema,
  breadcrumbSchema,
  productSchema,
} from '@/lib/seo/schemas'

// Optimized font loading with display: swap for instant text rendering
const inter = Inter({ 
  subsets: ['latin'], 
  variable: '--font-latin',
  display: 'swap', // Show text immediately with fallback font
  preload: true,
}) as any

const notoUrdu = Noto_Nastaliq_Urdu({ 
  subsets: ['arabic'], 
  variable: '--font-urdu', 
  weight: ['400', '700'],
  display: 'swap',
  preload: false, // Load lazily - not critical for initial render
}) as any

const notoArabic = Noto_Sans_Arabic({ 
  subsets: ['arabic'], 
  variable: '--font-arabic', 
  weight: ['400', '700'],
  display: 'swap',
  preload: false,
}) as any

const notoHindi = Noto_Sans_Devanagari({ 
  subsets: ['devanagari'], 
  variable: '--font-hindi', 
  weight: ['400', '700'],
  display: 'swap',
  preload: false,
}) as any

const notoBengali = Noto_Sans_Bengali({ 
  subsets: ['bengali'], 
  variable: '--font-bengali', 
  weight: ['400', '700'],
  display: 'swap',
  preload: false,
}) as any

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: 'Professional AI — The World\'s Most Powerful AI Assistant | Code, Create, Secure',
    template: '%s | Professional AI',
  },
  description: 'Professional AI is the ultimate all-in-one AI platform. Code in 35+ languages, secure your apps, generate images, process voice, and chat in Urdu, Hindi, Bengali & more. Start free trial.',
  keywords: [
    'professional ai',
    'best ai in the world',
    'ai in urdu',
    'ai in hindi',
    'ai for pakistan',
    'ai app download',
    'free ai chatbot',
    'ai coding tool',
    'ai security assistant',
    'ai chatbot urdu',
    'best ai coding assistant',
    'ai security tool',
    'world powerful ai',
    'ai image generator',
    'multi-language ai',
  ],
  authors: [{ name: 'Professional AI Team' }],
  creator: 'Professional AI',
  publisher: 'Professional AI',
  category: 'Technology',
  classification: 'Artificial Intelligence Software',
  alternates: {
    canonical: '/',
    languages: {
      ...HREFLANG_MAP,
      'x-default': `${SITE_URL}/`,
    },
  },
  openGraph: {
    title: 'Professional AI — The World\'s Most Powerful AI Assistant',
    description: 'AI coding tool and security assistant in Urdu, Hindi, Arabic, Bengali, and 40+ languages. Direct app downloads available.',
    type: 'website',
    url: SITE_URL,
    siteName: 'Professional AI',
    images: [
      {
        url: `${SITE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: 'Professional AI - World\'s Most Powerful AI Assistant',
      },
    ],
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Professional AI — The World\'s Most Powerful AI Assistant',
    description: 'Free AI chatbot + PRO AI coding and security tools with direct app downloads.',
    images: [`${SITE_URL}/og-image.png`],
  },
  verification: {
    google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION || '',
    yandex: process.env.NEXT_PUBLIC_YANDEX_VERIFICATION || '',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/manifest.json',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const cryptoObj = typeof window !== 'undefined' ? window.crypto : null
  const cspNonce = cryptoObj
    ? Array.from(cryptoObj.getRandomValues(new Uint8Array(16))).map(b => b.toString(16).padStart(2, '0')).join('')
    : 'static-nonce-secured-only-used-server-side'

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Critical SEO schemas - load immediately */}
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteSchema) }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareSchema) }} />
        
        {/* Non-critical schemas - can load async */}
        <script 
          type="application/ld+json" 
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
          async
        />
        <script 
          type="application/ld+json" 
          dangerouslySetInnerHTML={{ __html: JSON.stringify(reviewSchema) }}
          async
        />
        <script 
          type="application/ld+json" 
          dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
          async
        />
        <script 
          type="application/ld+json" 
          dangerouslySetInnerHTML={{ __html: JSON.stringify(productSchema) }}
          async
        />
        
        {/* App version for cache-busting verification */}
        <script dangerouslySetInnerHTML={{ __html: `window.__APP_VERSION__ = '${process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0'}';` }} />
        
        {/* Security headers */}
        <meta httpEquiv="X-Content-Type-Options" content="nosniff" />
        <meta httpEquiv="X-XSS-Protection" content="1; mode=block" />
        <meta httpEquiv="Strict-Transport-Security" content="max-age=31536000; includeSubDomains; preload" />
        <meta httpEquiv="Referrer-Policy" content="strict-origin-when-cross-origin" />
        <meta name="Permissions-Policy" content="camera=(), microphone=(), geolocation=()" />
        <meta name="theme-color" content="#0f172a" />
        <meta name="format-detection" content="telephone=yes" />
        
        {/* SEO */}
        <link rel="canonical" href={SITE_URL} />
        <link rel="alternate" hrefLang="en" href={`${SITE_URL}/?lang=en`} />
        <link rel="alternate" hrefLang="ur" href={`${SITE_URL}/?lang=ur`} />
        <link rel="alternate" hrefLang="hi" href={`${SITE_URL}/?lang=hi`} />
        <link rel="alternate" hrefLang="ar" href={`${SITE_URL}/?lang=ar`} />
        <link rel="alternate" hrefLang="bn" href={`${SITE_URL}/?lang=bn`} />
        <link rel="alternate" hrefLang="x-default" href={SITE_URL} />
        
        {/* Preconnect to critical origins */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="preconnect" href={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'} crossOrigin="anonymous" />
        
        {/* DNS prefetch for non-critical origins */}
        <link rel="dns-prefetch" href="https://cdn.professional-ai.com" />
      </head>
      <body className={`${inter.variable} ${notoUrdu.variable} ${notoArabic.variable} ${notoHindi.variable} ${notoBengali.variable} bg-gray-950 text-white min-h-screen`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          disableTransitionOnChange
        >
          <LanguageProvider>
            {children}
          </LanguageProvider>
        </ThemeProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#1f2937',
              color: '#f9fafb',
              border: '1px solid #374151',
            },
          }}
        />
        <VersionFooter />
      </body>
    </html>
  )
}