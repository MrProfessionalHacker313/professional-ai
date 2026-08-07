import { SITE_URL } from './locales'

export interface ContentDay {
  day: number
  date: string
  keyword: string
  title: string
  slug: string
  metaDescription: string
  url: string
}

const KEYWORDS = [
  'professional ai',
  'best ai in the world',
  'ai in urdu',
  'ai in hindi',
  'ai for pakistan',
  'ai app download',
  'free ai chatbot',
  'ai coding tool',
  'ai security assistant',
]

const TITLE_PATTERNS = [
  'How {k} helps teams ship faster in 2026',
  '{k}: practical guide for beginners and pros',
  'Why founders choose {k} for productivity',
  '{k} for students, developers, and security teams',
  'Complete benchmark: {k} performance and quality',
  'Top workflows to master with {k}',
  '{k} for multilingual users: Urdu, Hindi, Arabic, Bengali',
  'From idea to launch: building with {k}',
  '{k} and offline-first AI: what to implement now',
  'Choosing the right stack for {k} in 2026',
]

function slugify(input: string): string {
  return input
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
}

function makeTitle(day: number, keyword: string): string {
  const pattern = TITLE_PATTERNS[day % TITLE_PATTERNS.length]
  return pattern.replace('{k}', keyword)
}

function makeDescription(keyword: string): string {
  return `Daily SEO article focused on ${keyword}, covering practical use cases, comparisons, workflows, and app download guidance for global and South Asian audiences.`
}

export function generate90DayCalendar(startDateISO: string = '2026-08-01'): ContentDay[] {
  const start = new Date(`${startDateISO}T00:00:00Z`)
  const items: ContentDay[] = []

  for (let i = 0; i < 90; i += 1) {
    const date = new Date(start)
    date.setUTCDate(start.getUTCDate() + i)

    const keyword = KEYWORDS[i % KEYWORDS.length]
    const title = makeTitle(i, keyword)
    const slug = `${String(i + 1).padStart(2, '0')}-${slugify(title)}`

    items.push({
      day: i + 1,
      date: date.toISOString().slice(0, 10),
      keyword,
      title,
      slug,
      metaDescription: makeDescription(keyword),
      url: `${SITE_URL}/blog/${slug}`,
    })
  }

  return items
}

export const CONTENT_CALENDAR_90_DAYS = generate90DayCalendar()
