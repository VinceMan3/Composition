// One filed page, opened from the notebook. It reads like the page you wrote:
// the stamp, the totals, every set in ink. From here you can repeat it, fix a
// wrong number, or tear it out for good.

import { h, put, titleBox, icon, twoTap } from '../ui.js';
import * as log from '../log.js';
import { poseSketch } from '../poses.js';

export function render(el, ctx) {
  return ctx.state.fixing ? fixing(el, ctx) : reading(el, ctx);
}

function find(ctx) {
  const data = ctx.store.get();
  const i = data.pages.findIndex(p => p.id === ctx.state.openPage);
  return { data, i, page: data.pages[i] };
}

// ---------- reading ----------

function reading(el, ctx) {
  const { words, store, sound, toast } = ctx;
  const w = words.page;
  const { data, i, page } = find(ctx);
  const prior = { ...data, pages: data.pages.slice(0, i) };
  const sum = page.summary || log.summarize(prior, page);

  const total = (n, label) => h('div', { class: 'total' },
    h('p', { class: 'total-n' }, Number(n).toLocaleString('en-US')),
    h('p', { class: 'label' }, label),
  );

  put(el,
    poseSketch(data, page),
    h('span', { class: 'stamp' }, words.filed.stamp),
    h('div', { class: 'head-block', style: 'padding-right:0;min-height:0' },
      h('p', { class: 'kicker' }, `${w.kicker} · ${log.niceDate(page.date)}`),
      h('h1', { class: 'heading' }, page.title),
    ),
    h('div', { class: 'totals' },
      total(sum.lifts, words.filed.totals.lifts),
      total(sum.sets, words.filed.totals.sets),
      total(Math.round(sum.volume), words.filed.totals.volume),
      total(sum.minutes, words.filed.totals.minutes),
    ),

    (sum.records || []).length > 0 && h('div', null,
      h('p', { class: 'label' }, w.records),
      h('div', { class: 'compare' }, sum.records.map(r => h('div', { class: 'compare-row' },
        h('span', { class: 'compare-name' }, r.name),
        h('span', { class: 'compare-best' }, `${words.filed.estMax} ${r.now} ${page.unit} · ${words.filed.was} ${r.was}`),
      ))),
    ),

    h('div', { class: 'read-lifts bleed' },
      page.lifts.map(entry => {
        const lift = log.findLift(data, entry.liftId);
        return h('section', { class: 'lift' },
          h('button', {
            class: 'lift-head lift-link',
            type: 'button',
            'aria-label': `${lift.name}: ${w.history}`,
            onClick() { ctx.state.openLift = lift.id; ctx.state.liftFrom = 'page'; ctx.go('lift'); },
          },
            h('div', null,
              h('h2', { class: 'lift-name' }, lift.name),
              h('p', { class: 'lift-last', style: 'color:var(--ink)' }, log.setsText(entry.sets, lift)),
              entry.note && h('p', { class: 'day-note-text' }, entry.note),
            ),
            h('span', { class: 'filed-open' }, w.history),
          ),
        );
      }),
      (page.cardio || []).length > 0 && h('div', { class: 'lift-head', style: 'flex-direction:column;align-items:stretch;gap:2px' },
        h('p', { class: 'label' }, w.cardioLabel),
        (page.cardio || []).map(entry => {
          const kind = log.findCardio(entry.kindId);
          return h('div', { class: 'compare-row' },
            h('span', { class: `compare-name${kind.boxing ? ' is-boxing' : ''}` }, kind.name),
            h('span', { class: 'compare-best' }, log.cardioText(entry)),
          );
        }),
      ),
    ),

    h('div', { class: 'page-actions' },
      h('button', {
        class: 'btn',
        type: 'button',
        onClick() {
          if (store.get().draft) return toast(w.draftBusy);
          store.update(d => { d.draft = log.repeatPage(d, page); });
          sound.play('pencil');
          ctx.go('today');
        },
      }, w.repeatButton),
      h('button', { class: 'btn btn-line', type: 'button', onClick() { ctx.state.fixing = true; ctx.refresh(); } }, w.fixButton),
      h('a', { class: 'btn btn-line', href: '#notebook' }, w.back),
      twoTap(h('button', { class: 'link-btn', type: 'button' }, w.tear), w.tearConfirm, () => {
        store.update(d => { d.pages.splice(i, 1); });
        toast(w.torn);
        ctx.go('notebook');
      }),
    ),
  );
}

// ---------- fixing ----------

function fixing(el, ctx) {
  const { words, store, sound, toast } = ctx;
  const w = words.page;
  const tw = words.today;
  const { data, page } = find(ctx);
  // Work on a copy; nothing is saved until the save button.
  const copy = JSON.parse(JSON.stringify(page));
  const unit = copy.unit;
  const cleanNumber = text => text.replace(',', '.').replace(/[^0-9.]/g, '');

  const title = titleBox({
    maxlength: '40',
    value: copy.title,
    'aria-label': tw.titleLabel,
    autocomplete: 'off',
    onInput() { copy.title = title.value; },
  });

  const listEl = h('div', { class: 'lifts bleed' });
  function draw() {
    listEl.replaceChildren(...copy.lifts.map(liftBlock), ...copy.cardio.map(cardioBlock));
  }

  function field(set, key, label, extra) {
    const input = h('input', {
      type: 'text',
      inputmode: 'decimal',
      autocomplete: 'off',
      class: extra,
      value: set[key],
      'aria-label': label,
      onInput() {
        const clean = cleanNumber(input.value);
        if (clean !== input.value) input.value = clean;
        set[key] = clean;
      },
    });
    return input;
  }

  function liftBlock(entry, li) {
    const lift = log.findLift(data, entry.liftId);
    return h('section', { class: 'lift' },
      h('div', { class: 'lift-head' },
        h('div', null, h('h2', { class: 'lift-name' }, lift.name)),
        twoTap(h('button', { class: 'lift-remove', type: 'button' }, tw.removeLift), tw.removeLiftConfirm,
          () => { copy.lifts.splice(li, 1); draw(); }),
      ),
      h('div', { class: 'set-cols', 'aria-hidden': 'true' },
        h('span'),
        h('span', null, lift.kind === 'bodyweight' ? tw.cols.added : unit),
        h('span', null, lift.kind === 'timed' ? tw.cols.seconds : tw.cols.reps),
        h('span', null, tw.cols.rpe),
        h('span'),
      ),
      entry.sets.map((set, si) => h('div', { class: 'set-row is-done' },
        h('span', { class: 'set-n', style: 'display:grid;place-items:center' }, String(si + 1)),
        field(set, 'w', `${lift.name}, set ${si + 1}, ${unit}`),
        field(set, 'r', `${lift.name}, set ${si + 1}, reps`),
        field(set, 'rpe', `${lift.name}, set ${si + 1}, RPE`, 'rpe'),
        h('span'),
      )),
      h('div', { class: 'lift-foot' },
        h('button', {
          class: 'btn btn-line btn-small',
          type: 'button',
          onClick() {
            const last = entry.sets[entry.sets.length - 1] || { w: '', r: '' };
            entry.sets.push({ w: last.w, r: last.r, rpe: '', done: true });
            draw();
          },
        }, tw.addSet),
        entry.sets.length > 1 && h('button', {
          class: 'btn btn-line btn-small',
          type: 'button',
          onClick() { entry.sets.pop(); draw(); },
        }, tw.removeSet),
      ),
    );
  }

  function cardioBlock(entry, ci) {
    const kind = log.findCardio(entry.kindId);
    return h('section', { class: `lift cardio${kind.boxing ? ' is-boxing' : ''} is-done` },
      h('div', { class: 'lift-head' },
        h('div', null, h('h2', { class: 'lift-name' }, kind.name)),
        twoTap(h('button', { class: 'lift-remove', type: 'button' }, tw.removeLift), tw.removeLiftConfirm,
          () => { copy.cardio.splice(ci, 1); draw(); }),
      ),
      h('div', { class: 'cardio-row' }, kind.fields.map(name =>
        h('label', { class: 'cardio-box' },
          field(entry.values = entry.values || {}, name, `${kind.name}, ${name}`),
          h('span', null, words.today.cols[name] || name),
        ))),
    );
  }

  function save() {
    copy.title = copy.title.trim() || tw.untitled;
    copy.lifts = copy.lifts
      .map(entry => ({ ...entry, sets: entry.sets.filter(s => log.num(s.r) > 0).map(s => ({ ...s, done: true })) }))
      .filter(entry => entry.sets.length);
    copy.cardio = (copy.cardio || []).filter(log.hasNumbers).map(c => ({ ...c, done: true }));
    if (!copy.lifts.length && !copy.cardio.length) return toast(w.needSomething);
    store.update(d => {
      const at = d.pages.findIndex(p => p.id === copy.id);
      if (at < 0) return;
      copy.summary = log.summarize({ ...d, pages: d.pages.slice(0, at) }, copy);
      d.pages[at] = copy;
    });
    sound.play('stamp');
    toast(w.fixed);
    ctx.state.fixing = false;
    ctx.refresh();
  }

  put(el,
    h('div', { class: 'head-block', style: 'padding-right:0;min-height:0' },
      h('p', { class: 'kicker' }, `${w.fixKicker} · ${log.niceDate(copy.date)}`),
      title,
    ),
    listEl,
    h('div', { class: 'page-actions' },
      h('button', { class: 'btn', type: 'button', 'data-sound': 'none', onClick: save }, w.saveButton),
      h('button', { class: 'link-btn', type: 'button', onClick() { ctx.state.fixing = false; ctx.refresh(); } }, w.cancel),
    ),
  );
  draw();
}
