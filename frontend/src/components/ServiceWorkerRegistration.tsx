'use client'

import { useEffect } from 'react'

/**
 * Global Service Worker Registration
 * Registers /sw.js on every page load (not just chat/media).
 * Handles updates, offline sync messaging, and connectivity events.
 */
export default function ServiceWorkerRegistration() {
  useEffect(() => {
    if (typeof window === 'undefined') return
    if (!('serviceWorker' in navigator)) return

    let registration: ServiceWorkerRegistration | null = null

    const register = async () => {
      try {
        registration = await navigator.serviceWorker.register('/sw.js', {
          scope: '/',
        })

        await navigator.serviceWorker.ready
        registration.update()

        navigator.serviceWorker.addEventListener('controllerchange', () => {
          if (window.__SW_UPDATED__) return
          window.__SW_UPDATED__ = true
        })
      } catch (e) {
        console.error('[SW] Registration failed:', e)
      }
    }

    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === 'OFFLINE_SYNC_REQUEST') {
        import('@/lib/offline-sync').then(({ offlineSync }) => {
          offlineSync.syncPending()
        })
      }
    }

    navigator.serviceWorker.addEventListener('message', handleMessage)

    if (document.readyState === 'complete') {
      register()
    } else {
      window.addEventListener('load', register)
    }

    return () => {
      window.removeEventListener('load', register)
      navigator.serviceWorker.removeEventListener('message', handleMessage)
    }
  }, [])

  return null
}