// "Muscles it works": the chooser for a lift of your own, so it counts on the
// muscle map like the built-in lifts. Tap the main muscles; helpers are
// tucked under a link so the usual case stays one row of taps.
//   musclePicker({ words, works, helps, onChange })
// works and helps are the same comma lists the lift list uses: 'chest, triceps'.

import { h } from './ui.js';
import { PICK, splitNames } from './muscles.js';

export function musclePicker({ words, works = '', helps = '', onChange = () => {} }) {
  const w = words.muscles;
  const picked = { works: new Set(splitNames(works)), helps: new Set(splitNames(helps)) };
  for (const name of picked.works) picked.helps.delete(name);

  const value = () => ({
    works: PICK.filter(n => picked.works.has(n.toLowerCase())).map(n => n.toLowerCase()).join(', '),
    helps: PICK.filter(n => picked.helps.has(n.toLowerCase())).map(n => n.toLowerCase()).join(', '),
  });

  function row(kind, label) {
    const buttons = PICK.map(name => h('button', {
      class: 'chip',
      type: 'button',
      'data-muscle': name.toLowerCase(),
      'aria-pressed': String(picked[kind].has(name.toLowerCase())),
      onClick() {
        const key = name.toLowerCase();
        const set = picked[kind];
        if (set.has(key)) set.delete(key);
        else {
          set.add(key);
          // A muscle is either main or a helper, never both.
          picked[kind === 'works' ? 'helps' : 'works'].delete(key);
        }
        draw();
        onChange(value());
      },
    }, name));
    return { buttons, el: h('div', { class: 'chips muscle-chips', role: 'group', 'aria-label': label, 'data-kind': kind }, buttons) };
  }

  const main = row('works', w.worksLabel);
  const help = row('helps', w.helpsLabel);
  const helpBox = h('div', { class: 'muscle-helpers', hidden: picked.helps.size === 0 },
    h('p', { class: 'label' }, w.helpsLabel),
    help.el,
  );
  const helpLink = h('button', {
    class: 'link-btn',
    type: 'button',
    hidden: picked.helps.size > 0,
    onClick() { helpBox.hidden = false; helpLink.hidden = true; },
  }, w.addHelpers);

  function draw() {
    for (const [kind, r] of [['works', main], ['helps', help]]) {
      r.buttons.forEach((b, i) => b.setAttribute('aria-pressed', String(picked[kind].has(PICK[i].toLowerCase()))));
    }
  }

  const el = h('div', { class: 'muscle-pick' },
    h('p', { class: 'label' }, w.label),
    h('p', { class: 'quiet muscle-hint' }, w.hint),
    main.el,
    helpLink,
    helpBox,
  );
  return { el, get: value };
}
