/* Professional AI - Service Worker for OFFLINE-EVERYTHING mode */
/* v2.0.0 - Enhanced: caches Next.js build assets + all routes for full offline */

const CACHE_VERSION = 'proai-v2.0.0';
const APP_SHELL_CACHE = `${CACHE_VERSION}-appshell`;
const KNOWLEDGE_CACHE = `${CACHE_VERSION}-knowledge`;
const MODEL_CACHE = `${CACHE_VERSION}-models`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;
const NEXT_CACHE = `${CACHE_VERSION}-next`;

const APP_SHELL = [
  '/',
  '/landing',
  '/manifest.json',
  '/icon.svg',
  '/icon-maskable.svg',
  '/offline.html',
  '/chat',
  '/login',
  '/dashboard',
  '/media',
  '/pricing',
  '/features',
  '/profile',
  '/search',
  '/download',
  '/blog',
];

// Routes that must ALWAYS go to network first (real-time data)
const NETWORK_FIRST = ['/api/'];

// Model download URLs from Hugging Face - cache in separate store
const MODEL_PATTERNS = [
  'huggingface.co',
  'onnx-community',
  'Xenova',
  'cdn.jsdelivr.net',
  'unpkg.com',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(APP_SHELL_CACHE);
      // Cache app shell pages individually so one failure doesn't block install
      await Promise.allSettled(APP_SHELL.map((url) => cache.add(url)));
      await self.skipWaiting();
    })()
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys.filter((key) => !key.startsWith(CACHE_VERSION)).map((key) => caches.delete(key))
      );
      await self.clients.claim();
    })()
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and non-HTTP(S)
  if (request.method !== 'GET' || !url.protocol.startsWith('http')) return;

  const isSameOrigin = url.origin === self.location.origin;

  // Model downloads / CDN libraries - cache first
  if (!isSameOrigin && MODEL_PATTERNS.some((p) => url.hostname.includes(p) || url.pathname.includes(p))) {
    event.respondWith(cacheThenNetwork(request, MODEL_CACHE));
    return;
  }

  // Knowledge pack files (JSON knowledge index) - cache first
  if (isSameOrigin && url.pathname.includes('/knowledge/')) {
    event.respondWith(cacheFirstThenNetwork(request, KNOWLEDGE_CACHE));
    return;
  }

  // Next.js build assets (_next/static) - cache first with network update
  if (isSameOrigin && url.pathname.startsWith('/_next/static/')) {
    event.respondWith(cacheFirstThenNetwork(request, NEXT_CACHE));
    return;
  }

  // API calls - network first, fall back to cached or offline signal
  if (isSameOrigin && NETWORK_FIRST.some((prefix) => url.pathname.startsWith(prefix))) {
    event.respondWith(networkFirstThenCache(request));
    return;
  }

  // Page navigations - network first, fallback to cache, finally offline.html
  if (isSameOrigin && request.mode === 'navigate') {
    event.respondWith(navigationFallback(request));
    return;
  }

  // App shell / static assets - stale while revalidate
  if (
    isSameOrigin &&
    (request.destination === 'document' || request.destination === 'style' ||
      request.destination === 'script' || request.destination === 'font' ||
      request.destination === 'image')
  ) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // Everything else - network with cache fallback
  if (isSameOrigin) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(DYNAMIC_CACHE).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(() => caches.match(request).then((cached) => cached || caches.match('/offline.html')))
    );
  }
});

async function cacheFirstThenNetwork(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const network = await fetch(request);
    if (network.ok) {
      const clone = network.clone();
      caches.open(cacheName).then((cache) => cache.put(request, clone));
    }
    return network;
  } catch (e) {
    return new Response(JSON.stringify({ error: 'offline', offline: true }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

async function cacheThenNetwork(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const network = await fetch(request);
    if (network.ok) {
      const clone = network.clone();
      caches.open(cacheName).then((cache) => cache.put(request, clone));
    }
    return network;
  } catch (e) {
    return new Response('', { status: 503 });
  }
}

async function networkFirstThenCache(request) {
  try {
    const network = await fetch(request);
    if (network.ok) {
      const clone = network.clone();
      caches.open(DYNAMIC_CACHE).then((cache) => cache.put(request, clone));
    }
    return network;
  } catch (e) {
    // For GET requests return cached data
    if (request.method === 'GET') {
      const cached = await caches.match(request);
      if (cached) return cached;
    }
    // Signal offline to the client (the client will use local engine)
    return new Response(
      JSON.stringify({
        offline: true,
        error: 'offline',
        message: 'You are offline. Using local engine.',
      }),
      {
        status: 503,
        headers: {
          'Content-Type': 'application/json',
          'X-Offline-Mode': 'true',
        },
      }
    );
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(DYNAMIC_CACHE);
  const cached = await cache.match(request);

  const network = fetch(request)
    .then((response) => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => cached);

  return cached || network;
}

async function navigationFallback(request) {
  try {
    const network = await fetch(request);
    if (network.ok) {
      const clone = network.clone();
      caches.open(DYNAMIC_CACHE).then((cache) => cache.put(request, clone));
      return network;
    }
    throw new Error(`HTTP ${network.status}`);
  } catch (e) {
    // Try cache
    const cached = await caches.match(request);
    if (cached) return cached;
    // Fall back to cached root page
    const root = await caches.match('/');
    if (root) return root;
    // Final fallback
    return caches.match('/offline.html');
  }
}

/* ===== BACKGROUND SYNC ===== */
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Period sync for queued offline operations
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'offline-sync') {
    event.waitUntil(syncOfflineQueue());
  }
});

async function syncOfflineQueue() {
  const clients = await self.clients.matchAll({ includeUncontrolled: true, type: 'window' });
  for (const client of clients) {
    client.postMessage({ type: 'OFFLINE_SYNC_REQUEST' });
  }
}

/* ===== PUSH NOTIFICATIONS ===== */
self.addEventListener('push', (event) => {
  let data = { title: 'Professional AI', body: 'New update available' };
  try {
    if (event.data) data = event.data.json();
  } catch (e) { /* ignore */ }

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/icon.svg',
      badge: '/icon-maskable.svg',
      data: data.url || '/',
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        const url = event.notification.data || '/';
        for (const client of clientList) {
          if ('focus' in client) {
            client.focus();
            client.navigate(url);
            return;
          }
        }
        if (clients.openWindow) {
          clients.openWindow(url);
        }
      })
  );
});

/* ===== INSTALL PROMPT ===== */
self.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
});