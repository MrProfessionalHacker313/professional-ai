'use client'

import * as React from 'react'
import { createContext, useContext, useState, useEffect } from 'react'

type Language = 'en' | 'ur' | 'ar' | 'hi' | 'bn' | 'zh' | 'ru' | 'es' | 'fr' | 'de' | 'ja' | 'ko' | 'tr' | 'fa' | 'ps' | 'pa' | 'sd' | 'it' | 'pt' | 'id' | 'ms' | 'th' | 'vi' | 'sw' | 'nl' | 'pl' | 'uk' | 'el' | 'he' | 'ro'

interface LanguageContextType {
  language: Language
  setLanguage: (lang: Language) => void
  getFontClass: () => string
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

const languageFontMap: Record<Language, string> = {
  en: 'font-latin',
  ur: 'font-urdu',
  ar: 'font-arabic',
  hi: 'font-hindi',
  bn: 'font-bengali',
  zh: 'font-latin',
  ru: 'font-latin',
  es: 'font-latin',
  fr: 'font-latin',
  de: 'font-latin',
  ja: 'font-latin',
  ko: 'font-latin',
  tr: 'font-latin',
  fa: 'font-arabic',
  ps: 'font-arabic',
  pa: 'font-latin',
  sd: 'font-arabic',
  it: 'font-latin',
  pt: 'font-latin',
  id: 'font-latin',
  ms: 'font-latin',
  th: 'font-latin',
  vi: 'font-latin',
  sw: 'font-latin',
  nl: 'font-latin',
  pl: 'font-latin',
  uk: 'font-latin',
  el: 'font-latin',
  he: 'font-latin',
  ro: 'font-latin',
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>('en')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const saved = localStorage.getItem('language') as Language
    if (saved && languageFontMap[saved]) {
      setLanguage(saved)
    }
  }, [])

  useEffect(() => {
    if (mounted) {
      localStorage.setItem('language', language)
    }
  }, [language, mounted])

  const getFontClass = () => {
    return languageFontMap[language] || 'font-latin'
  }

  if (!mounted) {
    return (
      <LanguageContext.Provider value={{ language: 'en', setLanguage: () => {}, getFontClass: () => 'font-latin' }}>
        {children}
      </LanguageContext.Provider>
    )
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, getFontClass }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}