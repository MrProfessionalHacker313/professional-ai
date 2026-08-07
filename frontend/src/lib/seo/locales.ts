export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://professionalai.com'

export const LOCALE_CODES = [
  'en', 'ur', 'hi', 'bn', 'pa', 'ps', 'sd', 'ar', 'fa', 'tr',
  'zh', 'ja', 'ko', 'ru', 'fr', 'de', 'es', 'it', 'pt', 'nl',
  'pl', 'uk', 'el', 'he', 'id', 'ms', 'th', 'vi', 'sw', 'tl',
  'ne', 'si', 'ta', 'te', 'gu', 'mr', 'ku', 'uz', 'kk', 'my', 'km',
] as const

export type SupportedLocale = (typeof LOCALE_CODES)[number]

export const HREFLANG_MAP: Record<string, string> = LOCALE_CODES.reduce((acc, locale) => {
  acc[locale] = `${SITE_URL}/?lang=${locale}`
  return acc
}, {} as Record<string, string>)
