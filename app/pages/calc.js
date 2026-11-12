// The score calculator: put in any bodyweight and lifts, hit or not yet, and
// see the total, Wilks, DOTS and the level of each lift. Nothing is saved.

import { h, put } from '../ui.js';
import { levelStrip } from '../levels.js';
import { num, tidy } from '../log.js';
import { BIG_THREE, bests, bodyweight, scores, level } from '../strength.js';

export function render(el, ctx) {
  const { words, store } = ctx;
  const w = words.calc;
  const sw = words.stats;
  const data = store.get();

  // Starts from your own numbers: latest weigh-in, heaviest lifts.
  const mine = () => ({
    sex: data.settings.sex || 'men',
    bw: bodyweight(data) || '',
    lifts: Object.fromEntries(BIG_THREE.map(id => [id, bests(data, id).top || ''])),
  });
  let now = mine();

  const field = (label, value, onChange) => {
    const input = h('input', {
      class: 'calc-in',
      type: 'text',
      inputmode: 'decimal',
      autocomplete: 'off',
      value: value === '' ? '' : tidy(num(value)),
      'aria-label': label,
      onInput() {
        const clean = input.value.replace(',', '.').replace(/[^0-9.]/g, '');
        if (clean !== input.value) input.value = clean;
        onChange(clean);
        show();
      },
    });
    return { input, row: h('label', { class: 'calc-row' }, h('span', { class: 'setting-name' }, label), input, h('span', { class: 'label' }, 'lb')) };
  };

  const sexButtons = ['men', 'women'].map(choice => {
    const b = h('button', {
      class: 'chip',
      type: 'button',
      'aria-pressed': String(now.sex === choice),
      onClick() {
        now.sex = choice;
        for (const other of sexButtons) other.setAttribute('aria-pressed', String(other === b));
        show();
      },
    }, sw[choice]);
    return b;
  });

  const bwField = field(w.bodyLabel, now.bw, v => { now.bw = v; });
  const liftFields = BIG_THREE.map(id => field(sw.names[id], now.lifts[id], v => { now.lifts[id] = v; }));

  const out = h('div', { class: 'calc-out' });
  function show() {
    const bw = num(now.bw);
    const total = BIG_THREE.reduce((sum, id) => sum + num(now.lifts[id]), 0);
    const sc = scores(total, bw, now.sex);
    out.replaceChildren(
      h('div', { class: 'row' },
        h('div', null,
          h('p', { class: 'label' }, sw.totalLabel),
          h('p', { class: 'big-n' }, tidy(total), h('span', { class: 'total-unit' }, ' lb')),
        ),
        h('div', { class: 'scores' },
          h('p', null, h('span', { class: 'label' }, sw.wilks), h('span', { class: 'score-n' }, sc ? String(sc.wilks) : '–')),
          h('p', null, h('span', { class: 'label' }, sw.dots), h('span', { class: 'score-n' }, sc ? String(sc.dots) : '–')),
        ),
      ),
      ...BIG_THREE.map(id => {
        const lv = level(id, num(now.lifts[id]), bw, now.sex);
        return h('div', { class: 'calc-level' },
          h('p', { class: 'label' }, sw.names[id]),
          lv ? levelStrip(lv, sw) : h('p', { class: 'quiet' }, '–'),
        );
      }),
    );
  }

  const reset = h('button', {
    class: 'btn btn-line btn-small',
    type: 'button',
    onClick() {
      now = mine();
      bwField.input.value = now.bw === '' ? '' : tidy(num(now.bw));
      BIG_THREE.forEach((id, i) => { liftFields[i].input.value = now.lifts[id] === '' ? '' : tidy(num(now.lifts[id])); });
      sexButtons.forEach((b, i) => b.setAttribute('aria-pressed', String(['men', 'women'][i] === now.sex)));
      show();
    },
  }, w.reset);

  put(el,
    h('div', { class: 'head-block', style: 'padding-right:0;min-height:0;gap:8px' },
      h('p', { class: 'kicker' }, w.kicker),
      h('h1', { class: 'heading' }, w.title),
      h('p', { class: 'hand' }, w.note),
      h('a', { class: 'btn btn-line btn-small', href: '#stats', style: 'align-self:flex-start' }, `← ${w.back}`),
    ),
    h('div', { class: 'panel' },
      h('div', { class: 'row standards-row' }, h('span', { class: 'label' }, sw.standardsFor), h('div', { class: 'chips' }, sexButtons)),
      bwField.row,
      h('p', { class: 'label', style: 'margin-top:6px' }, w.liftsLabel),
      liftFields.map(f => f.row),
      reset,
    ),
    h('div', { class: 'panel' },
      h('p', { class: 'label' }, w.resultLabel),
      out,
    ),
  );
  show();
}
