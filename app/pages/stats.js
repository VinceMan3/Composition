// Progress: the Big Three with their levels, the total with Wilks and DOTS,
// a chart of each lift, bodyweight, the training calendar, and records.
// Everything is worked out in pounds and shown in the unit picked under More.

import { h, put, art, twoTap } from '../ui.js';
import { chart } from '../chart.js';
import { mark } from '../week.js';
import { levelStrip } from '../levels.js';
import { collect, findSticker } from '../awards.js';
import { dateKey, niceDate, findCardio, num, tidy } from '../log.js';
import { BIG_THREE, bests, history, weighins, bodyweight, scores, level, monthChange } from '../strength.js';
import { unitOf, fromLb, toLbFrom, show } from '../units.js';

export function render(el, ctx) {
  const { words, store, sound, toast } = ctx;
  const w = words.stats;
  const data = store.get();
  const unit = unitOf(data);
  const bw = bodyweight(data);
  const sex = data.settings.sex;
  const unitTag = () => h('span', { class: 'total-unit' }, ` ${unit}`);
  const monthAgo = dateKey(new Date(Date.now() - 30 * 86400000));

  // ---------- the Big Three ----------
  const best = Object.fromEntries(BIG_THREE.map(id => [id, bests(data, id)]));
  const recentRecord = id => data.pages.some(p => p.date >= monthAgo &&
    ((p.summary && p.summary.records) || []).some(r => r.name === w.names[id] && r.kind !== 'top'));

  const sexButtons = ['men', 'women'].map(choice => h('button', {
    class: 'chip',
    type: 'button',
    'aria-pressed': String(sex === choice),
    onClick() {
      store.update(d => { d.settings.sex = choice; });
      ctx.refresh();
    },
  }, w[choice]));

  // One row: the max big on the left; name, the month's change and the level.
  const liftRow = id => {
    const b = best[id];
    const lv = level(id, b.max, bw, sex);
    const change = monthChange(data, id);
    const record = recentRecord(id);
    return h('button', {
      class: `b3-row${record ? ' is-record' : ''}`,
      type: 'button',
      'data-sound': 'none',
      onClick() { ctx.state.openLift = id; ctx.go('lift'); },
    },
      h('span', { class: 'b3-n' }, b.max ? show(b.isTested ? b.max : Math.round(b.max), unit) : '–', b.max ? unitTag() : null),
      h('span', { class: 'b3-info' },
        h('span', { class: 'b3-name' }, w.names[id]),
        b.max
          ? h('span', { class: `b3-change${change > 0 ? ' up' : ''}` },
            change > 0 ? `▲ +${show(Math.round(change), unit)} ${unit} ${w.thisMonth}` : w.steady)
          : h('span', { class: 'b3-change' }, w.notYet),
        b.max ? h('span', { class: 'b3-source' }, b.isTested ? w.tested : w.estimated) : null,
      ),
      record && art('ribbon-record.png', 'b3-ribbon', 240, 326),
      b.max
        ? h('span', { class: 'b3-level' }, lv ? levelStrip(lv, w, unit) : h('span', { class: 'quiet' }, sex ? w.needBody : w.needSex))
        : null,
    );
  };

  const total = BIG_THREE.reduce((sum, id) => sum + best[id].top, 0);
  const sc = scores(total, bw, sex);
  const banner = h('div', { class: 'b3-total' },
    h('span', { class: 'b3-total-label' }, w.totalLabel),
    h('span', { class: 'b3-total-n' }, show(total, unit), h('span', { class: 'total-unit' }, ` ${unit}`)),
    h('span', { class: 'b3-scores' }, sc ? `${w.wilks} ${sc.wilks} · ${w.dots} ${sc.dots}` : w.scoresNeed),
  );

  // ----- logging a max straight in -----
  let logLift = 'bench-press';
  const logChips = BIG_THREE.map(id => {
    const chip = h('button', {
      class: 'chip',
      type: 'button',
      'aria-pressed': String(id === logLift),
      onClick() {
        logLift = id;
        for (const c of logChips) c.setAttribute('aria-pressed', String(c === chip));
      },
    }, w.names[id]);
    return chip;
  });
  const logWeight = h('input', { class: 'calc-in', type: 'text', inputmode: 'decimal', autocomplete: 'off', 'aria-label': w.logWeight });
  const logDay = h('input', { class: 'calc-in log-day', type: 'date', value: dateKey(), max: dateKey(), 'aria-label': w.logDate });
  const logForm = h('div', { class: 'panel log-max', hidden: true },
    h('p', { class: 'label' }, w.logTitle),
    h('p', { class: 'quiet' }, w.logNote),
    h('div', { class: 'chips' }, logChips),
    h('label', { class: 'calc-row' }, h('span', { class: 'setting-name' }, w.logWeight), logWeight, h('span', { class: 'label' }, unit)),
    h('label', { class: 'calc-row' }, h('span', { class: 'setting-name' }, w.logDate), logDay, h('span')),
    h('div', { class: 'wrap' },
      h('button', {
        class: 'btn btn-small',
        type: 'button',
        'data-sound': 'none',
        onClick() {
          const value = num(logWeight.value.replace(',', '.'));
          if (!(value > 0)) { sound.play('tap'); toast(w.logNeedWeight); logWeight.focus(); return; }
          const before = bests(store.get(), logLift).max;
          const lb = toLbFrom(value, unit);
          let fresh = [];
          store.update(d => {
            d.maxes = d.maxes || [];
            d.maxes.push({ id: Date.now().toString(36), liftId: logLift, w: value, unit, date: logDay.value || dateKey() });
            fresh = collect(d);
          });
          sound.play('stamp');
          const parts = [lb > before + 0.01 ? `${w.logRecord} ${w.names[logLift]} ${tidy(value)} ${unit}` : w.logSaved];
          if (fresh.length) {
            ctx.state.newStickers = [...(ctx.state.newStickers || []), ...fresh];
            parts.push(`${w.newSticker} ${fresh.map(id => findSticker(id).name).join(', ')}`);
          }
          toast(parts.join(' '));
          ctx.refresh();
        },
      }, w.logSave),
      h('button', { class: 'btn btn-line btn-small', type: 'button', onClick() { logForm.hidden = true; logOpen.hidden = false; } }, w.logCancel),
    ),
  );
  const logOpen = h('button', {
    class: 'btn btn-line btn-small',
    type: 'button',
    onClick() { logForm.hidden = false; logOpen.hidden = true; logWeight.focus(); },
  }, w.logMax);

  // ---------- one lift over time ----------
  let shownLift = BIG_THREE.find(id => history(data, id).length >= 2) || 'squat';
  const chartArt = h('div', { class: 'chart-art' });
  function drawChart() {
    const points = history(data, shownLift).map(p => ({ date: p.date, value: fromLb(p.value, unit) }));
    if (points.length >= 2) chartArt.innerHTML = chart(points, unit, { chartLabel: `${w.names[shownLift]}: ${w.chartLabel}` }, 'big');
    else chartArt.replaceChildren(h('p', { class: 'hand chart-empty' }, w.chartEmpty));
  }
  const liftChips = BIG_THREE.map(id => {
    const chip = h('button', {
      class: 'chip',
      type: 'button',
      'aria-pressed': String(id === shownLift),
      onClick() {
        shownLift = id;
        for (const c of liftChips) c.setAttribute('aria-pressed', String(c === chip));
        drawChart();
      },
    }, w.names[id]);
    return chip;
  });
  drawChart();

  // ---------- bodyweight ----------
  const list = weighins(data);
  const latest = list[list.length - 1];
  const before = [...list].reverse().find(x => x.date <= monthAgo) || list[0];
  const change = latest && before && before !== latest ? num(latest.w) - num(before.w) : null;
  const weighBox = h('input', {
    class: 'write-in weigh-in',
    type: 'text',
    inputmode: 'decimal',
    autocomplete: 'off',
    placeholder: unit,
    'aria-label': w.bodyLabel,
    enterkeyhint: 'done',
    onKeydown(e) { if (e.key === 'Enter') weighIn(); },
  });
  function weighIn() {
    const value = num(weighBox.value.replace(',', '.'));
    const lb = toLbFrom(value, unit);
    if (!(lb > 40 && lb < 1000)) { sound.play('tap'); toast(w.weighNeed); weighBox.focus(); return; }
    let fresh = [];
    store.update(d => {
      const today = dateKey();
      d.weighins = (d.weighins || []).filter(x => x.date !== today);
      d.weighins.push({ date: today, w: Math.round(lb * 10) / 10 });
      fresh = collect(d);
    });
    sound.play('pencil');
    if (fresh.length) {
      ctx.state.newStickers = [...(ctx.state.newStickers || []), ...fresh];
      sound.play('stamp');
      toast(`${w.newSticker} ${fresh.map(id => findSticker(id).name).join(', ')}`);
    } else {
      toast(w.weighSaved);
    }
    ctx.refresh();
  }
  const bodyChart = list.length >= 2 ? h('div', { class: 'chart-art' }) : null;
  if (bodyChart) bodyChart.innerHTML = chart(list.map(x => ({ date: x.date, value: fromLb(x.w, unit) })), unit, { chartLabel: w.bodyChart }, 'bw');
  const recent = [...list].reverse().slice(0, 4).map(x => h('div', { class: 'compare-row' },
    h('span', { class: 'compare-name' }, niceDate(x.date)),
    h('span', { class: 'compare-best' }, `${show(x.w, unit)} ${unit}`),
    twoTap(h('button', { class: 'lift-remove', type: 'button', style: 'grid-column:1 / -1;justify-self:start' }, w.remove), w.removeConfirm, () => {
      store.update(d => { d.weighins = d.weighins.filter(y => !(y.date === x.date && y.w === x.w)); });
      ctx.refresh();
    }),
  ));

  // ---------- the training calendar ----------
  const calBox = h('div', { class: 'cal-box' });
  let month = ctx.state.calendarMonth || new Date(new Date().getFullYear(), new Date().getMonth(), 1);
  function drawCalendar() {
    const first = new Date(month.getFullYear(), month.getMonth(), 1);
    const days = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
    const lead = (first.getDay() + 6) % 7;
    const todayKey = dateKey();
    const cells = [];
    for (let i = 0; i < lead; i++) cells.push(h('span', { class: 'cal-day is-blank' }));
    for (let d = 1; d <= days; d++) {
      const key = dateKey(new Date(month.getFullYear(), month.getMonth(), d));
      const pages = data.pages.filter(p => p.date === key);
      const cardio = pages.flatMap(p => p.cardio || []);
      const marks = [
        pages.some(p => p.lifts.length) && mark('lift'),
        cardio.some(c => findCardio(c.kindId).boxing) && mark('box'),
        cardio.some(c => !findCardio(c.kindId).boxing) && mark('cardio'),
      ].filter(Boolean);
      const cls = `cal-day${key === todayKey ? ' is-today' : ''}${pages.length ? ' has-page' : ''}`;
      const inside = [h('span', { class: 'cal-n' }, String(d)), h('span', { class: 'cal-marks' }, marks)];
      cells.push(pages.length
        ? h('button', {
          class: cls,
          type: 'button',
          'aria-label': `${niceDate(key)}: ${pages.map(p => p.title).join(', ')}`,
          onClick() { ctx.state.openPage = pages[pages.length - 1].id; ctx.state.fixing = false; ctx.go('page'); },
        }, inside)
        : h('span', { class: cls }, inside));
    }
    const shift = n => {
      month = new Date(month.getFullYear(), month.getMonth() + n, 1);
      ctx.state.calendarMonth = month;
      drawCalendar();
    };
    const trained = new Set(data.pages.filter(p => p.date.startsWith(dateKey(first).slice(0, 7))).map(p => p.date)).size;
    calBox.replaceChildren(
      h('div', { class: 'cal-head' },
        h('button', { class: 'cal-arrow', type: 'button', 'aria-label': w.prevMonth, onClick: () => shift(-1) }, '‹'),
        h('span', { class: 'cal-month' }, first.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })),
        h('button', { class: 'cal-arrow', type: 'button', 'aria-label': w.nextMonth, onClick: () => shift(1) }, '›'),
      ),
      h('div', { class: 'cal-grid' },
        ['M', 'T', 'W', 'T', 'F', 'S', 'S'].map(d => h('span', { class: 'cal-name' }, d)),
        cells,
      ),
      h('p', { class: 'hand cal-count' }, `${trained} ${trained === 1 ? words.notebook.week.day : words.notebook.week.days}`),
    );
  }
  drawCalendar();

  // ---------- records and ribbons ----------
  const records = [];
  for (const page of data.pages) {
    for (const r of (page.summary && page.summary.records) || []) records.push({ ...r, date: page.date, id: page.id });
  }
  records.reverse();

  const monthName = new Date().toLocaleDateString('en-US', { month: 'long' });

  put(el,
    h('div', { class: 'b3-head' },
      h('div', { class: 'b3-title' },
        h('p', { class: 'kicker' }, `${w.chartNo} · ${monthName}`),
        h('h1', { class: 'b3-heading' }, w.bigThree),
        h('p', { class: 'b3-sub' }, w.bigNote),
      ),
      h('figure', { class: 'b3-fig' },
        h('span', { class: 'b3-frame' }, art('sketch-back-hand.webp', '', 550, 720)),
        h('figcaption', null, w.figure),
      ),
    ),
    h('div', { class: 'row standards-row' },
      h('span', { class: 'label' }, w.standardsFor),
      h('div', { class: 'chips' }, sexButtons),
    ),
    h('div', { class: 'b3' }, BIG_THREE.map(liftRow)),
    banner,
    h('div', { class: 'wrap' },
      logOpen,
      h('a', { class: 'btn btn-line btn-small', href: '#calc' }, w.calcButton),
    ),
    logForm,

    h('section', { class: 'stats-part' },
      h('h2', { class: 'part-title' }, w.chartLabel),
      h('div', { class: 'chart panel' }, chartArt, h('div', { class: 'chips' }, liftChips)),
    ),

    h('section', { class: 'stats-part' },
      h('h2', { class: 'part-title' }, w.bodyLabel),
      h('div', { class: 'panel' },
        latest
          ? h('div', { class: 'row' },
            h('p', { class: 'big-n' }, show(latest.w, unit), unitTag()),
            change != null && h('p', { class: `hand ${change < 0 ? 'down-weight' : 'up-weight'}` }, `${change > 0 ? '+' : change < 0 ? '−' : ''}${show(Math.abs(change), unit)} ${unit} ${w.inDays}`),
          )
          : h('p', { class: 'hand' }, w.bodyNone),
        h('div', { class: 'weigh-row' },
          weighBox,
          h('button', { class: 'btn btn-small', type: 'button', 'data-sound': 'none', onClick: weighIn }, w.weighIn),
        ),
        bodyChart,
        recent.length > 0 && h('div', { class: 'compare' }, recent),
      ),
    ),

    h('section', { class: 'stats-part' },
      h('h2', { class: 'part-title' }, w.calendarLabel),
      h('div', { class: 'panel' }, calBox),
    ),

    h('section', { class: 'stats-part' },
      h('h2', { class: 'part-title' }, w.recordsLabel),
      records.length
        ? h('div', { class: 'compare' }, records.slice(0, 12).map(r => h('button', {
          class: 'compare-row record-row',
          type: 'button',
          onClick() { ctx.state.openPage = r.id; ctx.state.fixing = false; ctx.go('page'); },
        },
          h('span', { class: 'compare-name' }, art('ribbon-record.png', 'record-ribbon', 240, 326), r.name),
          h('span', { class: 'compare-best' }, `${r.now} ${r.unit || 'lb'}`),
          h('span', { class: 'compare-change hand' }, `${niceDate(r.date)} · ${w.was} ${r.was}`),
        )))
        : h('p', { class: 'hand', style: 'font-size:18px' }, w.recordsNone),
    ),
  );
}
