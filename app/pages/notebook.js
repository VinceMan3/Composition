// The notebook: every filed page, newest on top. Step 3 lets you open them.

import { h, put, count, art, pageHead, comingList } from '../ui.js';
import { niceDate } from '../log.js';

export function render(el, { words, store }) {
  const w = words.notebook;
  const pages = [...store.get().pages].reverse();
  put(el,
    art('sketch-dumbbell.png', 'sketch sketch-dumbbell', 440, 240),
    pageHead(words.tabs.notebook, w.title, w.note),
    h('div', null,
      h('p', { class: 'label', style: 'line-height:32px' }, w.filedLabel),
      pages.length
        ? h('div', { class: 'filed-list' }, pages.map(page => {
          const sets = page.lifts.reduce((n, entry) => n + entry.sets.length, 0);
          return h('div', { class: 'filed-row' },
            h('span', { class: 'kicker' }, niceDate(page.date)),
            h('span', { class: 'filed-title' }, page.title),
            h('span', { class: 'filed-meta' }, `${count(page.lifts.length, words.count.lift)} · ${count(sets, words.count.set)}`),
          );
        }))
        : h('p', { class: 'hand', style: 'font-size:18px;line-height:32px' }, w.empty),
    ),
    comingList(w.comingLabel, w.coming),
    art('coffee-ring.png', 'coffee coffee-low', 330, 330),
  );
}
