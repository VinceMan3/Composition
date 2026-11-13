// Add a lift: search the list, filter by body part, or write in a new one.

import { h, put } from '../ui.js';
import * as log from '../log.js';
import { musclePicker } from '../musclepick.js';

export function render(el, ctx) {
  const { words, store, sound, toast } = ctx;
  const w = words.add;
  const data = store.get();
  const onPage = new Set(data.draft.lifts.map(l => l.liftId));
  const lifts = log.allLifts(data);
  // Lifts you have logged before come first.
  const known = new Map(lifts.map(l => [l.id, log.lastTime(data, l.id)]));
  const ordered = [...lifts].sort((a, b) => Number(!!known.get(b.id)) - Number(!!known.get(a.id)));
  const bodyParts = [...new Set(lifts.map(l => l.group))];
  const groups = [w.all, ...bodyParts];

  let group = w.all;
  let query = '';

  function pick(id) {
    store.update(d => { log.addLift(d, d.draft, id); });
    sound.play('pencil');
    ctx.state.focusLift = store.get().draft.lifts.length - 1;
    ctx.go('today');
  }

  // ----- the list -----
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
    if (!shown.length) kids.push(h('p', { class: 'pick-group' }, w.none));
    listEl.replaceChildren(...kids);
    newButton.textContent = q.length > 1 && !lifts.some(l => l.name.toLowerCase() === q)
      ? `${w.newLift}: ${query.trim()}`
      : w.newLift;
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

  // ----- writing in a new lift -----
  // One row of choices where exactly one is picked.
  function choice(options, start) {
    let value = start;
    const buttons = options.map(name => {
      const b = h('button', {
        class: 'chip',
        type: 'button',
        'aria-pressed': String(name === value),
        onClick() {
          value = name;
          for (const other of buttons) other.setAttribute('aria-pressed', String(other === b));
        },
      }, name);
      return b;
    });
    return { el: h('div', { class: 'chips' }, buttons), get: () => value, set(v) { value = v; buttons.forEach((b, i) => b.setAttribute('aria-pressed', String(options[i] === v))); } };
  }
  const nameBox = h('input', { class: 'write-in', type: 'text', maxlength: '40', placeholder: w.namePlaceholder, 'aria-label': w.nameLabel, autocomplete: 'off' });
  const partChoice = choice([...bodyParts.filter(g => g !== 'Yours'), w.other], w.other);
  const gearChoice = choice(w.gearOptions, w.gearOptions[0]);
  const muscles = musclePicker({ words });
  const form = h('div', { class: 'panel', hidden: true },
    h('p', { class: 'label' }, w.newTitle),
    nameBox,
    h('p', { class: 'label' }, w.partLabel),
    partChoice.el,
    h('p', { class: 'label' }, w.gearLabel),
    gearChoice.el,
    muscles.el,
    h('button', {
      class: 'btn',
      type: 'button',
      'data-sound': 'none',
      onClick() {
        const name = nameBox.value.trim();
        if (!name) { sound.play('tap'); toast(w.needName); nameBox.focus(); return; }
        const same = lifts.find(l => l.name.toLowerCase() === name.toLowerCase());
        if (same) return onPage.has(same.id) ? ctx.go('today') : pick(same.id);
        let id;
        store.update(d => { id = log.addCustomLift(d, name, partChoice.get(), gearChoice.get() === w.other ? '' : gearChoice.get(), muscles.get()).id; });
        pick(id);
      },
    }, w.createButton),
    h('button', { class: 'link-btn', type: 'button', onClick: () => showForm(false) }, w.backToList),
  );
  function showForm(on) {
    form.hidden = !on;
    browse.hidden = on;
    if (!on) return;
    nameBox.value = search.value.trim();
    if (group !== w.all && group !== 'Yours') partChoice.set(group);
    nameBox.focus();
  }
  const newButton = h('button', { class: 'btn btn-line', type: 'button', onClick: () => showForm(true) }, w.newLift);
  const browse = h('div', { class: 'browse' },
    search,
    h('div', { class: 'chips is-scrolling bleed' }, chips),
    newButton,
    listEl,
  );

  put(el,
    h('div', { class: 'head-block', style: 'padding-right:0;min-height:0;gap:8px' },
      h('p', { class: 'kicker' }, w.kicker),
      h('h1', { class: 'heading' }, w.title),
      h('a', { class: 'btn btn-line btn-small', href: '#today', style: 'align-self:flex-start' }, `← ${w.back}`),
    ),
    browse,
    form,
  );
  draw();
}
