// Progress: the Big Three with their levels, the total with Wilks and DOTS,
// a chart of each lift, bodyweight, the training calendar, and records.

import { h, put, art, pageHead, twoTap } from '../ui.js';
import { chart } from '../chart.js';
import { mark } from '../week.js';
import { levelStrip } from '../levels.js';
import { collect, findSticker } from '../awards.js';
import { dateKey, niceDate, findCardio, num, tidy } from '../log.js';
import { BIG_THREE, bests, history, weighins, bodyweight, scores, level } from '../strength.js';

export function render(el, ctx) {
  const { words, store, sound, toast } = ctx;
  const w = words.stats;
  const data = store.get();
  const bw = bodyweight(data);
  const sex = data.settings.sex;

  // ---------- the Big Three ----------
  const best = Object.fromEntries(BIG_THREE.map(id => [id, bests(data, id)]));

  const sexButtons = ['men', 'women'].map(choice => h('button', {
    class: 'chip',
    type: 'button',
    'aria-pressed': String(sex === choice),
    onClick() {
      store.update(d => { d.settings.sex = choice; });
      ctx.refresh();
    },
  }, w[choice]));

  const liftCard = id => {
    const b = best[id];
    const lv = level(id, b.est, bw, sex);
    const open = () => { ctx.state.openLift = id; ctx.go('lift'); };
    return h('button', { class: 'big panel', type: 'button', 'data-sound': 'none', onClick: open },
      h('span', { class: 'big-name' }, w.names[id]),
      b.est
        ? [
          h('span', { class: 'big-row' },
            h('span', { class: 'big-n' }, String(b.est), h('span', { class: 'total-unit' }, ' lb')),
            h('span', { class: 'big-side' },
              h('span', { class: 'label' }, w.estMax),
              h('span', { class: 'hand' }, `${tidy(b.top)} lb ${w.heaviest}`),
            ),
          ),
          lv ? levelStrip(lv, w) : h('span', { class: 'quiet' }, sex ? w.needBody : w.needSex),
        ]
        : h('span', { class: 'hand' }, w.notYet),
    );
  };

  const total = BIG_THREE.reduce((sum, id) => sum + best[id].top, 0);
  const sc = scores(total, bw, sex);
  const totalCard = h('div', { class: 'big-total panel' },
    h('div', { class: 'row' },
      h('div', null,
        h('p', { class: 'label' }, w.totalLabel),
        h('p', { class: 'big-n' }, tidy(total), h('span', { class: 'total-unit' }, ' lb')),
      ),
      h('div', { class: 'scores' },
        h('p', null, h('span', { class: 'label' }, w.wilks), h('span', { class: 'score-n' }, sc ? String(sc.wilks) : '–')),
        h('p', null, h('span', { class: 'label' }, w.dots), h('span', { class: 'score-n' }, sc ? String(sc.dots) : '–')),
      ),
    ),
    h('p', { class: 'quiet' }, w.totalNote),
    !sc && h('p', { class: 'quiet warn' }, !sex ? w.needSex : w.needBody),
    h('a', { class: 'btn btn-line btn-small', href: '#calc', style: 'align-self:flex-start' }, w.calcButton),
  );

  // ---------- one lift over time ----------
  let shownLift = BIG_THREE.find(id => history(data, id).length >= 2) || 'squat';
  const chartArt = h('div', { class: 'chart-art' });
  function drawChart() {
    const points = history(data, shownLift);
    if (points.length >= 2) chartArt.innerHTML = chart(points, 'lb', { chartLabel: `${w.names[shownLift]}: ${w.chartLabel}` }, 'big');
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
  const monthAgo = dateKey(new Date(Date.now() - 30 * 86400000));
  const before = [...list].reverse().find(x => x.date <= monthAgo) || list[0];
  const change = latest && before && before !== latest ? num(latest.w) - num(before.w) : null;
  const weighBox = h('input', {
    class: 'write-in weigh-in',
    type: 'text',
    inputmode: 'decimal',
    autocomplete: 'off',
    placeholder: w.weighPlaceholder,
    'aria-label': w.bodyLabel,
    enterkeyhint: 'done',
    onKeydown(e) { if (e.key === 'Enter') weighIn(); },
  });
  function weighIn() {
    const value = num(weighBox.value.replace(',', '.'));
    if (!(value > 40 && value < 1000)) { sound.play('tap'); toast(w.weighNeed); weighBox.focus(); return; }
    let fresh = [];
    store.update(d => {
      const today = dateKey();
      d.weighins = (d.weighins || []).filter(x => x.date !== today);
      d.weighins.push({ date: today, w: Math.round(value * 10) / 10 });
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
  const bodyChart = list.length >= 2
    ? h('div', { class: 'chart-art' })
    : null;
  if (bodyChart) bodyChart.innerHTML = chart(list.map(x => ({ date: x.date, value: Math.round(num(x.w) * 10) / 10 })), 'lb', { chartLabel: w.bodyChart }, 'bw');
  const recent = [...list].reverse().slice(0, 4).map(x => h('div', { class: 'compare-row' },
    h('span', { class: 'compare-name' }, niceDate(x.date)),
    h('span', { class: 'compare-best' }, `${tidy(num(x.w))} lb`),
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

  put(el,
    art('sketch-back.webp', 'sketch sketch-back', 640, 587),
    pageHead(words.tabs.stats, w.title, w.note),

    h('section', { class: 'stats-part' },
      h('div', { class: 'row' },
        h('h2', { class: 'part-title' }, w.bigThree),
      ),
      h('div', { class: 'row standards-row' },
        h('span', { class: 'label' }, w.standardsFor),
        h('div', { class: 'chips' }, sexButtons),
      ),
      BIG_THREE.map(liftCard),
      totalCard,
    ),

    h('section', { class: 'stats-part' },
      h('h2', { class: 'part-title' }, w.chartLabel),
      h('div', { class: 'chart panel' }, chartArt, h('div', { class: 'chips' }, liftChips)),
    ),

    h('section', { class: 'stats-part' },
      h('h2', { class: 'part-title' }, w.bodyLabel),
      h('div', { class: 'panel' },
        latest
          ? h('div', { class: 'row' },
            h('p', { class: 'big-n' }, tidy(num(latest.w)), h('span', { class: 'total-unit' }, ' lb')),
            change != null && h('p', { class: `hand ${change < 0 ? 'down-weight' : 'up-weight'}` }, `${change > 0 ? '+' : change < 0 ? '−' : ''}${tidy(Math.abs(change))} lb ${w.inDays}`),
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
          h('span', { class: 'compare-best' }, `${r.now} lb`),
          h('span', { class: 'compare-change hand' }, `${niceDate(r.date)} · ${w.was} ${r.was}`),
        )))
        : h('p', { class: 'hand', style: 'font-size:18px' }, w.recordsNone),
    ),
  );
}
