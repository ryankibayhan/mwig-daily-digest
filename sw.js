// MIST-40 ULTRA service worker — v4.2 TURBO
// Shell: stale-while-revalidate (instant open, silent update). APIs: always network (honest data).
const VER = 'mist40-v4.2';
const SHELL = ['./', './index.html', './manifest.webmanifest'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VER).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== VER).map((k) => caches.delete(k)))
  ).then(() => self.clients.claim()));
});

self.addEventListener('fetch', (e) => {
  const url = e.request.url;
  if (e.request.method !== 'GET') return;
  const isApi = url.indexOf('yahoo.com') !== -1 || url.indexOf('frankfurter') !== -1 ||
                url.indexOf('allorigins') !== -1 || url.indexOf('codetabs') !== -1 ||
                url.indexOf('corsproxy') !== -1;
  if (isApi) return; // market data must NEVER be served from cache
  e.respondWith(
    caches.open(VER).then(async (cache) => {
      const cached = await cache.match(e.request, {ignoreSearch: true});
      const fetchP = fetch(e.request).then((resp) => {
        if (resp && resp.ok && (url.indexOf(self.location.origin) === 0 || url.indexOf('github.io') === -1)) {
          try { cache.put(e.request, resp.clone()); } catch (e2) {}
        }
        return resp;
      }).catch(() => cached);
      return cached || fetchP;
    })
  );
});
