// Add a lift: search the list, filter by body part, or write in your own.

import { h, put, pageHead } from '../ui.js';
import * as log from '../log.js';

export function render(el, ctx) {
  const { words, store, sound } = ctx;
  const w = words.add;
  const data = store.get();
  const onPage = new Set(data.draft.lifts.map(l => l.liftId));
  const lifts = log.allLifts(data);
  // Lifts you have logged before come first.
  const known = new Map(lifts.map(l => [l.id, log.lastTime(data, l.id)]));
  const ordered = [...lifts].sort((a, b) => Number(!!known.get(b.id)) - Number(!!known.get(a.id)));
  const groups = [w.all, ...new Set(lifts.map(l => l.group))];

  let group = w.all;
  let query = '';

  function pick(id) {
    store.update(d => { log.addLift(d, d.draft, id); });
    sound.play('pencil');
    ctx.state.focusLift = store.get().draft.lifts.length - 1;
    ctx.go('today');
  }

  function pickOwn() {
    let id;
    store.update(d => { id = log.addCustomLift(d, query).id; });
    pick(id);
  }

  const listEl = h('div', { class: 'pick-list bleed' });
  function draw() {
    const q = query.trim().toLowerCase();
    const shown = ordered.filter(l =>
      (group === w.all || l.group === group) &&
      (!q || l.name.toLowerCase().includes(q) || (l.gear || '').toLowerCase().includes(q)));
    const kids = shown.map(l => {
      const prev = known.get(l.id);
      const best = prev && log.bestSet(prev);
      const side = onPage.has(l.id) ? w.onPage : best ? log.setText(best, l) : '';
      return h('button', { class: 'pick', type: 'button', 'data-sound': 'none', disabled: onPage.has(l.id), onClick: () => pick(l.id) },
        h('span', { class: 'pick-name' }, l.name),
        h('span', { class: 'pick-last' }, side),
        h('span', { class: 'pick-meta' }, [l.gear, l.works].filter(Boolean).join(' · ')),
      );
    });
    const exact = lifts.some(l => l.name.toLowerCase() === q);
    if (q.length > 1 && !exact) {
      kids.push(h('button', { class: 'pick pick-own', type: 'button', 'data-sound': 'none', onClick: pickOwn },
        h('span', { class: 'pick-name' }, `+ ${query.trim()}`),
        h('span', { class: 'pick-last' }),
        h('span', { class: 'pick-meta' }, shown.length ? w.addOwn : `${w.none} ${w.addOwn}`),
      ));
    }
    listEl.replaceChildren(...kids);
  }

  const search = h('input', {
    class: 'search',
    type: 'search',
    placeholder: w.searchPlaceholder,
    'aria-label': w.searchPlaceholder,
    autocomplete: 'off',
    onInput() { query = search.value; draw(); },
  });
  const chips = groups.map(name => {
    const chip = h('button', {
      class: 'chip',
      type: 'button',
      'aria-pressed': String(name === group),
      onClick() {
        group = name;
        for (const c of chips) c.setAttribute('aria-pressed', String(c === chip));
        draw();
      },
    }, name);
    return chip;
  });

  put(el,
    h('div', { class: 'head-block', style: 'padding-right:0;min-height:0;gap:8px' },
      h('p', { class: 'kicker' }, w.kicker),
      h('h1', { class: 'heading' }, w.title),
      h('a', { class: 'btn btn-line btn-small', href: '#today', style: 'align-self:flex-start' }, `← ${w.back}`),
    ),
    search,
    h('div', { class: 'chips is-scrolling bleed' }, chips),
    listEl,
  );
  draw();
}
