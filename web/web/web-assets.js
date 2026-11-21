(() => {
  const metadataName = "winks-boot-meta";
  const url = name => new URL(name, location.href).href;
  const catalogUrl = url("web-assets.json");
  const receipt = url("web-assets.active");

  window.winksCacheReady = (async () => {
    if (!await navigator.serviceWorker.getRegistration()) {
      await navigator.serviceWorker.register(url("coi_serviceworker.js"));
    }
    await navigator.serviceWorker.ready;
    if (!navigator.serviceWorker.controller) {
      await new Promise(resolve => navigator.serviceWorker.addEventListener(
        "controllerchange", resolve, {once: true}));
    }
    return caches.open(metadataName);
  })();

  window.winksCatalog = async () => {
    const metadata = await window.winksCacheReady;
    try {
      const response = await fetch(catalogUrl, {cache: "no-store"});
      if (!response.ok) throw new Error("The asset list could not be loaded.");
      return await response.json();
    } catch (error) {
      const cached = await metadata.match(catalogUrl);
      if (cached) return cached.json();
      throw error;
    }
  };

  window.prepareWinksAssets = async (catalog, tier, progress) => {
    const metadata = await window.winksCacheReady;
    const cacheName = "winks-assets-" + catalog.version;
    const cache = await caches.open(cacheName);
    const texture = catalog.packs[tier];
    const files = [...catalog.assets, ...(texture ? [texture] : [])];
    for (const [index, name] of files.entries()) {
      const request = url(name);
      progress(index + 1, files.length, name);
      if (await cache.match(request)) continue;
      const response = await fetch(request, {cache: "reload"});
      if (!response.ok) throw new Error("Download failed for " + name);
      await cache.put(request, response);
    }
    const textureBlob = texture ? await (await cache.match(url(texture))).blob() : null;
    await metadata.put(catalogUrl, new Response(JSON.stringify(catalog)));
    await metadata.put(receipt, new Response(cacheName));
    return textureBlob ? {name: texture.split("/").at(-1), blob: textureBlob} : null;
  };
})();
