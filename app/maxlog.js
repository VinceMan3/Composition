// Logging a one-rep max straight in, outside a page: a test day, a meet, a
// single. Used on a Big Three lift's history page.

import { h } from './ui.js';
import { collect, findSticker } from './awards.js';
import { dateKey, num, tidy } from './log.js';
import { bests } from './strength.js';
import { unitOf, toLbFrom } from './units.js';

export function maxLogger(ctx, liftId, liftName) {
  const { words, store, sound, toast } = ctx;
  const w = words.stats;
  const unit = unitOf(store.get());

  const weight = h('input', { class: 'calc-in', type: 'text', inputmode: 'decimal', autocomplete: 'off', 'aria-label': w.logWeight });
  const day = h('input', { class: 'calc-in log-day', type: 'date', value: dateKey(), max: dateKey(), 'aria-label': w.logDate });

  function save() {
    const value = num(weight.value.replace(',', '.'));
    if (!(value > 0)) { sound.play('tap'); toast(w.logNeedWeight); weight.focus(); return; }
    const before = bests(store.get(), liftId).max;
    let fresh = [];
    store.update(d => {
      d.maxes = d.maxes || [];
      d.maxes.push({ id: Date.now().toString(36), liftId, w: value, unit, date: day.value || dateKey() });
      fresh = collect(d);
    });
    sound.play('stamp');
    const parts = [toLbFrom(value, unit) > before + 0.01 ? `${w.logRecord} ${liftName} ${tidy(value)} ${unit}` : w.logSaved];
    if (fresh.length) {
      ctx.state.newStickers = [...(ctx.state.newStickers || []), ...fresh];
      parts.push(`${w.newSticker} ${fresh.map(id => findSticker(id).name).join(', ')}`);
    }
    toast(parts.join(' '));
    ctx.refresh();
  }

  const form = h('div', { class: 'panel log-max', hidden: true },
    h('p', { class: 'label' }, w.logTitle),
    h('p', { class: 'quiet' }, w.logNote),
    h('label', { class: 'calc-row' }, h('span', { class: 'setting-name' }, w.logWeight), weight, h('span', { class: 'label' }, unit)),
    h('label', { class: 'calc-row' }, h('span', { class: 'setting-name' }, w.logDate), day, h('span')),
    h('div', { class: 'wrap' },
      h('button', { class: 'btn btn-small', type: 'button', 'data-sound': 'none', onClick: save }, w.logSave),
      h('button', { class: 'btn btn-line btn-small', type: 'button', onClick() { form.hidden = true; open.hidden = false; } }, w.logCancel),
    ),
  );
  const open = h('button', {
    class: 'btn btn-small log-open',
    type: 'button',
    onClick() { form.hidden = false; open.hidden = true; weight.focus(); },
  }, w.logMax);
  return [open, form];
}
