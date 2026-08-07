import { SITE_URL } from './locales'

const DOWNLOAD_PAGE = `${SITE_URL}/download`
const PRICING_PAGE = `${SITE_URL}/pricing`

export const organizationSchema = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'Professional AI',
  alternateName: ['پروفیشنل اے آئی', 'प्रोफेशنल एआई', 'الذكاء الاصطناعي الاحترافي', 'প্রফেশনাল এআই', 'Professional AI Pakistan'],
  url: SITE_URL,
  logo: `${SITE_URL}/logo.png`,
  image: `${SITE_URL}/og-image.png`,
  description: 'World\'s most powerful all-in-one AI assistant for coding, cybersecurity, bug fixing, and multilingual chat in 40+ languages.',
  email: 'support@professionalai.com',
  telephone: '+92-300-1234567',
  address: {
    '@type': 'PostalAddress',
    streetAddress: '123 Tech Valley, Phase 2',
    addressLocality: 'Lahore',
    addressRegion: 'Punjab',
    postalCode: '54000',
    addressCountry: 'PK',
  },
  sameAs: [
    SITE_URL,
    PRICING_PAGE,
    DOWNLOAD_PAGE,
    `${SITE_URL}/features`,
    `${SITE_URL}/blog`,
  ],
  contactPoint: {
    '@type': 'ContactPoint',
    contactType: 'customer support',
    email: 'support@professionalai.com',
    telephone: '+92-300-1234567',
    availableLanguage: ['English', 'Urdu', 'Hindi', 'Arabic', 'Bengali'],
  },
}

export const websiteSchema = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: 'Professional AI',
  url: SITE_URL,
  description: 'Professional AI is a multilingual AI platform for coding, security analysis, chat, and productivity in 40+ languages.',
  inLanguage: ['en', 'ur', 'hi', 'ar', 'bn'],
  copyrightYear: '2026',
  copyrightHolder: {
    '@type': 'Organization',
    name: 'Professional AI',
  },
  potentialAction: {
    '@type': 'SearchAction',
    target: {
      '@type': 'EntryPoint',
      urlTemplate: `${SITE_URL}/chat?query={search_term_string}`,
    },
    'query-input': 'required name=search_term_string',
  },
}

export const softwareSchema = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'Professional AI',
  applicationCategory: 'BusinessApplication',
  subcategory: 'AI Coding Assistant',
  operatingSystem: 'Web, Android, iOS, Windows, macOS, Linux',
  offers: [
    {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
      url: PRICING_PAGE,
      availability: 'https://schema.org/InStock',
      description: 'Free plan with basic features',
    },
    {
      '@type': 'Offer',
      price: '19.99',
      priceCurrency: 'USD',
      url: PRICING_PAGE,
      availability: 'https://schema.org/InStock',
      description: 'PRO monthly plan',
    },
    {
      '@type': 'Offer',
      price: '143.99',
      priceCurrency: 'USD',
      url: PRICING_PAGE,
      availability: 'https://schema.org/InStock',
      description: 'PRO yearly plan (20% discount)',
    },
  ],
  aggregateRating: {
    '@type': 'AggregateRating',
    ratingValue: '4.9',
    bestRating: '5',
    ratingCount: '2500',
    reviewCount: '2500',
  },
  downloadUrl: [
    DOWNLOAD_PAGE,
    process.env.NEXT_PUBLIC_ANDROID_APP_URL || `${SITE_URL}/download#android`,
    process.env.NEXT_PUBLIC_IOS_APP_URL || `${SITE_URL}/download#ios`,
    process.env.NEXT_PUBLIC_DESKTOP_WINDOWS_URL || `${SITE_URL}/download#windows`,
    process.env.NEXT_PUBLIC_DESKTOP_MAC_URL || `${SITE_URL}/download#mac`,
    process.env.NEXT_PUBLIC_DESKTOP_LINUX_URL || `${SITE_URL}/download#linux`,
  ],
  description:
    'Professional AI is a multilingual AI platform for coding, security, chat, and productivity in 40+ languages with web, mobile, and desktop downloads.',
  featureList: 'AI Coding Assistant, Cybersecurity Expert, Bug Fixer, Multi-Language Support, AI Image Generation, AI Voice & Speech, Document Processing, API & Integration',
  screenshot: `${SITE_URL}/screenshot.png`,
  softwareVersion: '2.0.0',
  fileSize: '45MB',
  requirements: 'Android 8+, iOS 14+, Windows 10+, macOS 11+, Linux x64',
  releaseNotes: 'Initial release with full AI coding, security, and multilingual support.',
}

export const faqSchema = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: [
    {
      '@type': 'Question',
      name: 'What is Professional AI?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Professional AI is an all-in-one AI platform for coding, security analysis, image generation, voice synthesis, multilingual chat, and document processing in 40+ languages.',
      },
    },
    {
      '@type': 'Question',
      name: 'Is Professional AI available in Urdu and Hindi?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Yes. Professional AI supports Urdu, Hindi, Arabic, Bengali, and 40+ languages with native context understanding.',
      },
    },
    {
      '@type': 'Question',
      name: 'Where can I download Professional AI apps?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: `Visit ${DOWNLOAD_PAGE} to access Android, iOS, Windows, macOS, and Linux download links.`,
      },
    },
    {
      '@type': 'Question',
      name: 'Does Professional AI have a free plan?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Yes. Professional AI includes a free plan with basic features and paid plans starting at $19.99/month for advanced usage.',
      },
    },
    {
      '@type': 'Question',
      name: 'What programming languages does the AI coding assistant support?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Professional AI supports 35+ programming languages including Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, and more.',
      },
    },
    {
      '@type': 'Question',
      name: 'Is my data secure with Professional AI?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Absolutely. We use AES-256-GCM encryption, TLS 1.3, GDPR compliance, and never share your data with third parties.',
      },
    },
    {
      '@type': 'Question',
      name: 'Can I use Professional AI for commercial projects?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Yes. All paid plans include commercial usage rights. Build products, services, and client work with confidence.',
      },
    },
    {
      '@type': 'Question',
      name: 'Does Professional AI offer an API?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Yes. Professional AI offers REST APIs and SDKs for Python, JavaScript, Node.js, and more. Build custom integrations and automate workflows.',
      },
    },
    {
      '@type': 'Question',
      name: 'How does the referral program work?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Share your unique referral link. When someone signs up, you both get 100 free credits instantly. Unlimited referrals allowed.',
      },
    },
    {
      '@type': 'Question',
      name: 'Can I cancel my subscription anytime?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Yes. Cancel anytime with one click. No cancellation fees, no penalties. Your access continues until the end of your billing period.',
      },
    },
  ],
}

export const reviewSchema = {
  '@context': 'https://schema.org',
  '@type': 'Review',
  itemReviewed: {
    '@type': 'SoftwareApplication',
    name: 'Professional AI',
    applicationCategory: 'BusinessApplication',
  },
  reviewRating: {
    '@type': 'AggregateRating',
    ratingValue: '4.9',
    bestRating: '5',
    worstRating: '1',
    ratingCount: '2500',
  },
  author: {
    '@type': 'Organization',
    name: 'Professional AI Users',
  },
  reviewBody:
    'Professional AI is the world\'s most powerful all-in-one AI assistant. Users praise its coding accuracy, multilingual support (Urdu, Hindi, Arabic, Bengali), security scanning, and 40+ language chat capabilities. 4.9/5 rating from 2,500+ verified reviews.',
  datePublished: '2026-01-15',
}

export const breadcrumbSchema = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: [
    {
      '@type': 'ListItem',
      position: 1,
      name: 'Home',
      item: SITE_URL,
    },
    {
      '@type': 'ListItem',
      position: 2,
      name: 'Pricing',
      item: PRICING_PAGE,
    },
    {
      '@type': 'ListItem',
      position: 3,
      name: 'Download',
      item: DOWNLOAD_PAGE,
    },
    {
      '@type': 'ListItem',
      position: 4,
      name: 'Features',
      item: `${SITE_URL}/features`,
    },
    {
      '@type': 'ListItem',
      position: 5,
      name: 'Blog',
      item: `${SITE_URL}/blog`,
    },
  ],
}

export const productSchema = {
  '@context': 'https://schema.org',
  '@type': 'Product',
  name: 'Professional AI',
  description: 'World\'s most powerful all-in-one AI assistant for coding, cybersecurity, and multilingual chat.',
  brand: {
    '@type': 'Brand',
    name: 'Professional AI',
  },
  aggregateRating: {
    '@type': 'AggregateRating',
    ratingValue: '4.9',
    bestRating: '5',
    ratingCount: '2500',
  },
  offers: [
    {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
      availability: 'https://schema.org/InStock',
      url: PRICING_PAGE,
    },
    {
      '@type': 'Offer',
      price: '19.99',
      priceCurrency: 'USD',
      availability: 'https://schema.org/InStock',
      url: PRICING_PAGE,
    },
  ],
}
