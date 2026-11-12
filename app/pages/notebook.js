// The notebook: every filed page, newest on top. Tap one to open it.

import { h, put, count, art, pageHead } from '../ui.js';
import { niceDate, findCardio } from '../log.js';

export function render(el, ctx) {
  const { words, store } = ctx;
  const w = words.notebook;
  const pages = [...store.get().pages].reverse();
  put(el,
    art('sketch-dumbbell.png', 'sketch sketch-dumbbell', 440, 240),
    pageHead(words.tabs.notebook, w.title, w.note),
    h('a', { class: 'btn btn-line', href: '#library', style: 'align-self:flex-start' }, w.libraryButton),
    h('div', null,
      h('p', { class: 'label', style: 'line-height:32px' }, w.filedLabel),
      pages.length
        ? h('div', { class: 'filed-list' }, pages.map(page => {
          const sets = page.lifts.reduce((n, entry) => n + entry.sets.length, 0);
          const cardio = (page.cardio || []).map(c => findCardio(c.kindId).name.toLowerCase());
          const meta = [page.lifts.length && count(page.lifts.length, words.count.lift), sets && count(sets, words.count.set), ...cardio].filter(Boolean).join(' · ');
          return h('button', {
            class: 'filed-row',
            type: 'button',
            'data-sound': 'none',
            onClick() { ctx.state.openPage = page.id; ctx.state.fixing = false; ctx.go('page'); },
          },
            h('span', { class: 'kicker' }, niceDate(page.date)),
            h('span', { class: 'filed-title' }, page.title),
            h('span', { class: 'filed-meta' }, meta),
            h('span', { class: 'filed-open' }, w.open),
          );
        }))
        : h('p', { class: 'hand', style: 'font-size:18px;line-height:32px' }, w.empty),
    ),
    art('coffee-ring.png', 'coffee coffee-low', 330, 330),
  );
}
