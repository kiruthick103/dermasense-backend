// DermaSense Service Worker for offline shell caching
const CACHE_NAME = 'dermasense-v2';
const ASSETS_TO_CACHE = [
  '/',
  '/sw.js',
  '/camera.js',
  '/engine/vision.js',
  '/samples/sample_ring_rash.jpg',
  '/samples/sample_rash_wide.jpg',
  '/samples/sample_cream_label.jpg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(ASSETS_TO_CACHE).catch(() => {});
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  // Only intercept GET navigation requests or app shell
  if (event.request.method === 'GET' && event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match('/') || new Response(
          '<!DOCTYPE html><html><body><h1>DermaSense (Offline)</h1><p>You are currently offline. Please reconnect to use AI rash screening.</p></body></html>',
          { headers: { 'Content-Type': 'text/html' } }
        );
      })
    );
  }
});
