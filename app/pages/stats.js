// Progress: the Big Three, records, charts and the calendar. Built in step 5.

import { put, art, pageHead, comingList } from '../ui.js';

export function render(el, { words }) {
  const w = words.stats;
  put(el,
    art('sketch-back.webp', 'sketch sketch-back', 640, 587),
    pageHead(words.tabs.stats, w.title, w.note),
    comingList(w.comingLabel, w.coming),
  );
}
