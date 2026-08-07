/**
 * Professional AI - Connectivity Hook
 * Tracks online/offline status and exposes it to React components.
 */

'use client'

import { useState, useEffect, useCallback } from 'react'

export type ConnectionStatus = 'online' | 'offline' | 'low-bandwidth'

export function useConnectivity() {
  const [isOnline, setIsOnline] = useState<boolean>(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  )
  const [status, setStatus] = useState<ConnectionStatus>(
    typeof navigator !== 'undefined' && navigator.onLine ? 'online' : 'offline'
  )
  const [latency, setLatency] = useState<number | null>(null)

  const checkLatency = useCallback(async () => {
    if (!navigator.onLine) {
      setStatus('offline')
      return
    }
    const start = Date.now()
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 5000)
      await fetch('/api/health', { signal: controller.signal, cache: 'no-store' })
      clearTimeout(timeout)
      const ms = Date.now() - start
      setLatency(ms)
      setStatus(ms > 2000 ? 'low-bandwidth' : 'online')
    } catch {
      setStatus('offline')
    }
  }, [])

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      checkLatency()
    }
    const handleOffline = () => {
      setIsOnline(false)
      setStatus('offline')
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Initial check
    checkLatency()

    // Periodic check every 30s
    const interval = setInterval(checkLatency, 30000)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      clearInterval(interval)
    }
  }, [checkLatency])

  return { isOnline, status, latency }
}