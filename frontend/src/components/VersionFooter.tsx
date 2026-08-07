'use client'

import { useEffect, useState } from 'react'

export default function VersionFooter() {
  const [version, setVersion] = useState('1.0.0')

  useEffect(() => {
    if (typeof window !== 'undefined' && (window as any).__APP_VERSION__) {
      setVersion((window as any).__APP_VERSION__)
    }
  }, [])

  return (
    <footer className="w-full py-3 text-center text-xs text-gray-600 border-t border-gray-800/50">
      <span>Professional AI v{version}</span>
      <span className="mx-2">·</span>
      <span>All systems operational</span>
    </footer>
  )
}