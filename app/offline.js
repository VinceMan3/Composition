// Turns on the offline copy (sw.js) where the app is properly hosted, and
// hands it the list of files this visit loaded so they are all saved.
// Skipped in previews, which cannot keep an offline copy.

export function startOffline() {
  const hosted = document.querySelector('link[rel="manifest"]');
  if (!hosted || !('serviceWorker' in navigator)) return;
  navigator.serviceWorker.register('sw.js').then(() => navigator.serviceWorker.ready).then(reg => {
    const save = () => {
      const urls = [location.href.split('#')[0], ...performance.getEntriesByType('resource').map(e => e.name)];
      if (reg.active) reg.active.postMessage({ save: urls });
    };
    // Once now, and again after a moment for art that loads later.
    save();
    setTimeout(save, 4000);
  }).catch(() => {
    // No offline copy here; the app works the same online.
  });
}
