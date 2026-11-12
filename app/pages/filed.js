// Page filed: the stamp, the totals, any new records, and how each lift
// compared with last time.

import { h, put, art } from '../ui.js';
import { niceDate } from '../log.js';

export function render(el, ctx) {
  const { words, store, sound } = ctx;
  const w = words.filed;
  const data = store.get();
  const page = data.pages[data.pages.length - 1];
  const sum = page.summary || { lifts: page.lifts.length, sets: 0, volume: 0, minutes: 0, records: [], rows: [] };
  const unit = page.unit;

  // Straight after filing, the stamp comes down once the page has landed.
  const fresh = ctx.state.justFiled;
  ctx.state.justFiled = false;
  const stamp = h('span', { class: 'stamp stamp-big' }, w.stamp);
  let timer = 0;
  if (fresh) {
    stamp.style.visibility = 'hidden';
    timer = setTimeout(() => {
      stamp.style.visibility = '';
      stamp.classList.add('is-stamping');
      sound.play('stamp');
    }, 430);
  }

  const total = (n, label) => h('div', { class: 'total' },
    h('p', { class: 'total-n' }, Number(n).toLocaleString('en-US')),
    h('p', { class: 'label' }, label),
  );
  const changeLine = row => {
    if (!row.change) return h('p', { class: 'compare-change hand' }, w.firstTime);
    if (!row.change.dir) return h('p', { class: 'compare-change hand' }, w.same);
    return h('p', { class: `compare-change ${row.change.dir > 0 ? 'up' : 'down'}` }, row.change.text);
  };

  put(el,
    art('sketch-arm.webp', 'sketch sketch-arm', 540, 605),
    stamp,
    h('div', { class: 'head-block', style: 'padding-right:0;min-height:0' },
      h('p', { class: 'kicker' }, `${w.kicker} · ${niceDate(page.date)}`),
      h('h1', { class: 'heading' }, page.title),
    ),
    h('div', { class: 'totals' },
      total(sum.lifts, w.totals.lifts),
      total(sum.sets, w.totals.sets),
      total(Math.round(sum.volume), w.totals.volume),
      total(sum.minutes, w.totals.minutes),
    ),
    sum.records.map(r => h('div', { class: 'record' },
      art('ribbon-record.png', '', 240, 326),
      h('div', null,
        h('p', { class: 'label' }, w.recordLabel),
        h('p', { class: 'record-name' }, r.name),
        h('p', { class: 'hand' }, `${w.estMax} ${r.now} ${unit} · ${w.was} ${r.was}`),
      ),
    )),
    sum.rows.length > 0 && h('div', null,
      h('p', { class: 'label' }, w.compareLabel),
      h('div', { class: 'compare' }, sum.rows.map(row => h('div', { class: 'compare-row' },
        h('span', { class: 'compare-name' }, row.name),
        h('span', { class: 'compare-best' }, row.best),
        changeLine(row),
      ))),
    ),
    h('div', { class: 'page-actions' },
      h('a', { class: 'btn', href: '#cover' }, w.toCover),
      h('a', { class: 'btn btn-line', href: '#notebook' }, w.toNotebook),
    ),
  );

  return () => clearTimeout(timer);
}
