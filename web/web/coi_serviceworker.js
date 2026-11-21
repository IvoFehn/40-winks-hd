const metadata = "winks-boot-meta";
const scope = registration.scope;
const receipt = new URL("web-assets.active", scope).href;

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", event => event.waitUntil(self.clients.claim()));

function isolated(response) {
  const headers = new Headers(response.headers);
  headers.set("Cross-Origin-Opener-Policy", "same-origin");
  headers.set("Cross-Origin-Embedder-Policy", "require-corp");
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers
  });
}

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET" || !request.url.startsWith(scope)) return;
  if (request.cache === "only-if-cached" && request.mode !== "same-origin") return;

  event.respondWith((async () => {
    const meta = await caches.open(metadata);
    const active = await meta.match(receipt);
    const cache = active ? await caches.open(await active.text()) : null;
    if (request.mode === "navigate") {
      try {
        return isolated(await fetch(request));
      } catch (error) {
        const cached = await cache?.match(request, {ignoreSearch: true});
        if (cached) return isolated(cached);
        throw error;
      }
    }
    if (request.cache !== "reload" && request.cache !== "no-store") {
      const cached = await cache?.match(request);
      if (cached) return cached;
    }
    const response = await fetch(request);
    return request.destination.endsWith("worker") ? isolated(response) : response;
  })());
});
