/* Professional AI - Service Worker for OFFLINE-EVERYTHING mode */

const CACHE_VERSION = 'proai-v1.0.0';
const APP_SHELL_CACHE = `${CACHE_VERSION}-appshell`;
const KNOWLEDGE_CACHE = `${CACHE_VERSION}-knowledge`;
const MODEL_CACHE = `${CACHE_VERSION}-models`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;

const APP_SHELL = [
  '/',
  '/manifest.json',
  '/icon.svg',
  '/icon-maskable.svg',
  '/offline.html',
];

// Routes that must ALWAYS go to network first (real-time data)
const NETWORK_FIRST = [
  '/api/auth',
  '/api/chat',
  '/api/features',
  '/api/payments',
  '/credits',
  '/api/admin',
  '/api/offline',
];

// Model download URLs from Hugging Face - cache in separate store
const MODEL_PATTERNS = [
  'huggingface.co',
  'onnx-community',
  'Xenova',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(APP_SHELL_CACHE)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => !key.startsWith(CACHE_VERSION))
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and non-HTTP(S)
  if (request.method !== 'GET' || !url.protocol.startsWith('http')) return;

  // Model downloads - cache first (resume-capable via Range support in HTTP cache)
  if (MODEL_PATTERNS.some((p) => url.hostname.includes(p) || url.pathname.includes(p))) {
    event.respondWith(cacheThenNetwork(request, MODEL_CACHE));
    return;
  }

  // Knowledge pack files (JSON knowledge index)
  if (url.pathname.includes('/knowledge/')) {
    event.respondWith(cacheFirstThenNetwork(request, KNOWLEDGE_CACHE));
    return;
  }

  // API calls - network first, fall back to offline queue
  if (NETWORK_FIRST.some((prefix) => url.pathname.startsWith(prefix))) {
    event.respondWith(networkFirstThenCache(request));
    return;
  }

  // App shell / static assets - stale while revalidate
  if (request.destination === 'document' || request.destination === 'style' ||
      request.destination === 'script' || request.destination === 'font' ||
      request.destination === 'image') {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // Everything else - network with cache fallback
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
    const cached = await caches.match(request);
    if (cached) return cached;
    // Signal offline to the client (the client will use local engine)
    return new Response(JSON.stringify({
      offline: true,
      error: 'offline',
      message: 'You are offline. Using local engine.',
    }), {
      status: 503,
      headers: {
        'Content-Type': 'application/json',
        'X-Offline-Mode': 'true',
      },
    });
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
  // Let the page handle the install prompt
});