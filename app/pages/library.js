// The lift library: every lift, the ones you have logged first. Tap one to
// see its whole story.

import { h, put, count, pageHead } from '../ui.js';
import * as log from '../log.js';

export function render(el, ctx) {
  const { words, store } = ctx;
  const w = words.library;
  const data = store.get();

  // How many filed pages each lift is on, and its best set.
  const story = new Map();
  for (const page of data.pages) {
    for (const entry of page.lifts) {
      const s = story.get(entry.liftId) || { pages: 0 };
      s.pages += 1;
      story.set(entry.liftId, s);
    }
  }
  const lifts = log.allLifts(data);
  const ordered = [...lifts].sort((a, b) =>
    ((story.get(b.id) || {}).pages || 0) - ((story.get(a.id) || {}).pages || 0) || a.name.localeCompare(b.name));

  let query = '';
  const listEl = h('div', { class: 'pick-list bleed' });
  function draw() {
    const q = query.trim().toLowerCase();
    const shown = ordered.filter(l => !q || l.name.toLowerCase().includes(q) || (l.gear || '').toLowerCase().includes(q));
    listEl.replaceChildren(...shown.map(l => {
      const s = story.get(l.id);
      const prev = s && log.lastTime(data, l.id);
      const best = prev && log.bestSet(prev);
      return h('button', {
        class: 'pick',
        type: 'button',
        'data-sound': 'none',
        onClick() { ctx.state.openLift = l.id; ctx.go('lift'); },
      },
        h('span', { class: 'pick-name' }, l.name),
        h('span', { class: 'pick-last' }, s ? count(s.pages, w.pages) : ''),
        h('span', { class: 'pick-meta' }, s && best ? `${words.today.lastTime}: ${log.setText(best, l)}` : s ? '' : w.never),
      );
    }));
  }

  const search = h('input', {
    class: 'search',
    type: 'search',
    placeholder: w.searchPlaceholder,
    'aria-label': w.searchPlaceholder,
    autocomplete: 'off',
    onInput() { query = search.value; draw(); },
  });

  put(el,
    h('div', { class: 'head-block', style: 'padding-right:0;min-height:0;gap:8px' },
      h('p', { class: 'kicker' }, w.kicker),
      h('h1', { class: 'heading' }, w.title),
      h('p', { class: 'hand' }, w.note),
      h('a', { class: 'btn btn-line btn-small', href: '#notebook', style: 'align-self:flex-start' }, `← ${w.back}`),
    ),
    search,
    listEl,
  );
  draw();
}
