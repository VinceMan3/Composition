// Keeps a copy of the app on the phone so it opens and works with no signal.
//
// Every file is answered from the saved copy straight away (fast, and fine
// offline), and fetched fresh in the background whenever there is a
// connection, so the next launch has the latest version.
//
// The page tells this worker which files it loaded on the very first visit
// (app/offline.js), so everything is saved after one launch.

const CACHE = 'composition-v1';

// Every drawing, saved up front so pages not opened yet still have their
// art offline. A check in the tests fails if a file in art/ is missing here.
const ART = [
  './art/badge-bag-5.webp',
  './art/badge-bench-225.webp',
  './art/badge-bw-bench.webp',
  './art/badge-bw-dead.webp',
  './art/badge-bw-squat.webp',
  './art/badge-club-1000.webp',
  './art/badge-club-1250.webp',
  './art/badge-club-1500.webp',
  './art/badge-dead-405.webp',
  './art/badge-first-page.webp',
  './art/badge-million.webp',
  './art/badge-pages-10.webp',
  './art/badge-pages-50.webp',
  './art/badge-record.webp',
  './art/badge-road-10.webp',
  './art/badge-squat-315.webp',
  './art/badge-week-3.webp',
  './art/coffee-ring.png',
  './art/cover-wear.webp',
  './art/desk.webp',
  './art/ink-stamp.webp',
  './art/muscle-back.svg',
  './art/muscle-front.svg',
  './art/paper.webp',
  './art/ribbon-record.png',
  './art/ring.svg',
  './art/sketch-arm.webp',
  './art/sketch-back-hand.webp',
  './art/sketch-back.webp',
  './art/sketch-dumbbell.png',
  './art/sketch-front.webp',
  './art/sticker-barbell.png',
  './art/sticker-gloves.png',
  './art/sticker-pose.png',
  './art/sticker-ribbons.png',
  './art/icon/icon-180.png',
  './art/icon/icon-192.png',
  './art/icon/icon-512.png',
];

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await cache.addAll(['./', './index.html', './manifest.webmanifest']);
    // One missing drawing should not stop the rest from saving.
    await Promise.all(ART.map(url => cache.add(url).catch(() => {})));
  })());
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    for (const name of await caches.keys()) if (name !== CACHE) await caches.delete(name);
    await self.clients.claim();
  })());
});

// Save a response if it is worth keeping.
async function keep(request, response) {
  if (!response || (response.status !== 200 && response.type !== 'opaque')) return;
  const cache = await caches.open(CACHE);
  await cache.put(request, response);
}

// The page's list of files it has already loaded.
self.addEventListener('message', event => {
  const urls = (event.data && event.data.save) || [];
  event.waitUntil((async () => {
    for (const url of urls) {
      try {
        if (await caches.match(url)) continue;
        const sameSite = new URL(url).origin === self.location.origin;
        const response = await fetch(url, sameSite ? {} : { mode: 'no-cors' });
        await keep(url, response);
      } catch {
        // Skip anything that cannot be fetched right now.
      }
    }
  })());
});

self.addEventListener('fetch', event => {
  const { request } = event;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  const ours = url.origin === self.location.origin;
  const fonts = /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname);
  if (!ours && !fonts) return;

  event.respondWith((async () => {
    // Opening the app at any address inside it serves the app's page.
    const key = request.mode === 'navigate' ? './index.html' : request;
    const saved = await caches.match(key, { ignoreSearch: request.mode === 'navigate' });
    const fresh = fetch(request).then(async response => {
      await keep(key, response.clone());
      return response;
    }).catch(() => null);
    if (saved) {
      event.waitUntil(fresh);
      return saved;
    }
    return (await fresh) || new Response('Offline', { status: 503, statusText: 'Offline' });
  })());
});
