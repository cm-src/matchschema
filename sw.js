// Service worker for PWA offline support.
//
// Caching strategy:
//   - Navigations / HTML  : network-first (fresh shell, cache fallback offline)
//   - data/ files         : network-first (always try fresh schedule data)
//   - other static assets : stale-while-revalidate (serve cache instantly,
//                           refresh from network in the background)
//
// Static assets here have stable, non-hashed filenames that are edited in
// place, so cache-first would freeze them indefinitely. Stale-while-
// revalidate propagates edits within ~1 visit without manual CACHE_NAME
// bumps, which are now emergency-only (force-invalidate the whole cache).
const CACHE_NAME = 'central-basket-v6';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/assets/styles.css',
  '/assets/app.js',
  '/assets/manifest.json',
  '/assets/fonts/inter-latin.woff2',
  '/assets/fonts/outfit-latin.woff2',
  '/assets/favicon.ico',
  '/assets/favicon-32x32.png',
  '/assets/favicon-16x16.png',
  '/assets/apple-touch-icon.png'
];

// Install event - precache the shell so the app works offline from first load
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(ASSETS_TO_CACHE))
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

// Network-first: try the network, fall back to cache when offline.
// Used for navigations (fresh HTML shell) and data/ files (fresh schedule).
function networkFirst(event) {
  return fetch(event.request)
    .then((networkResponse) => {
      if (networkResponse && networkResponse.status === 200) {
        const cloned = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, cloned));
      }
      return networkResponse;
    })
    .catch(() => caches.match(event.request));
}

// Stale-while-revalidate: serve cached asset instantly (if any), and fetch
// from the network in the background to update the cache for next time.
// Falls back to cache/offline when the network is down.
function staleWhileRevalidate(event) {
  const fromCache = caches.match(event.request);
  const fromNetwork = fetch(event.request)
    .then((networkResponse) => {
      if (networkResponse && networkResponse.status === 200) {
        const cloned = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, cloned));
      }
      return networkResponse;
    })
    .catch(() => caches.match(event.request));

  // Race: cached response wins if present, else wait for the network.
  return fromCache.then((cached) => cached || fromNetwork);
}

// Fetch event - route requests by kind
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  // Only handle same-origin requests; let the browser handle the rest.
  if (url.origin !== self.location.origin) return;

  const pathname = url.pathname;
  const isNavigation = event.request.mode === 'navigate';
  const isDataFile = pathname.startsWith('/data/');

  if (isNavigation || isDataFile) {
    event.respondWith(networkFirst(event));
  } else {
    event.respondWith(staleWhileRevalidate(event));
  }
});