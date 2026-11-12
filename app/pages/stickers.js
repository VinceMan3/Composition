// The sticker book: every sticker there is, the ones you have and how to
// earn the rest. Tap one you have to take it off the cover or put it back.

import { h, put, art } from '../ui.js';
import { niceDate } from '../log.js';
import { STICKERS, hasSticker } from '../awards.js';

export function render(el, ctx) {
  const { words, store, sound } = ctx;
  const w = words.stickers;
  const data = store.get();
  const have = STICKERS.filter(s => hasSticker(data, s)).length;

  const cards = STICKERS.map(def => {
    const mine = hasSticker(data, def);
    const state = h('span', { class: 'book-state' });
    const showState = () => {
      const off = (store.get().stickers[def.id] || {}).off;
      state.textContent = off ? w.offCover : w.onCover;
      card.classList.toggle('is-off', !!off);
    };
    const card = h(mine ? 'button' : 'div', {
      class: `book-card${mine ? '' : ' is-locked'}`,
      type: mine ? 'button' : null,
      'data-sound': mine ? 'none' : null,
      onClick: mine ? () => {
        store.update(d => { d.stickers[def.id] = { ...d.stickers[def.id], off: !(d.stickers[def.id] || {}).off }; });
        sound.play('tap');
        showState();
      } : null,
    },
      h('span', { class: 'book-art' }, art(def.art, '', null, null, mine ? `${def.name} sticker` : '')),
      h('span', { class: 'book-name' }, def.name),
      mine
        ? state
        : h('span', { class: 'book-how' }, def.how),
      mine && data.earned[def.id] && h('span', { class: 'book-date' }, `${w.earned} ${niceDate(data.earned[def.id])}`),
    );
    if (mine) showState();
    return card;
  });

  put(el,
    h('div', { class: 'head-block', style: 'padding-right:0;min-height:0;gap:8px' },
      h('p', { class: 'kicker' }, `${have} ${w.of} ${STICKERS.length}`),
      h('h1', { class: 'heading' }, w.title),
      h('p', { class: 'hand' }, w.note),
      h('a', { class: 'btn btn-line btn-small', href: '#more', style: 'align-self:flex-start' }, `← ${w.back}`),
    ),
    h('div', { class: 'book' }, cards),
  );
}
