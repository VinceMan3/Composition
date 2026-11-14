// One lift's story, plotted by hand page by page, and every session it
// appears on. The Big Three are tracked by their max (tested, or estimated
// from the best set); every other lift by the heaviest weight lifted.

import { h, put, count, noteField, twoTap } from '../ui.js';
import { bests } from '../strength.js';
import { unitOf, fromLb, show } from '../units.js';
import { maxLogger } from '../maxlog.js';
import { chart } from '../chart.js';
import * as log from '../log.js';
import { musclePicker } from '../musclepick.js';

export function render(el, ctx) {
  const { words, store } = ctx;
  const w = words.lift;
  const data = store.get();
  const lift = log.findLift(data, ctx.state.openLift);
  const big = log.isBigThree(lift.id);
  // Back goes wherever the lift was opened from.
  const from = ['stats', 'page', 'library', 'map'].includes(ctx.state.liftFrom) ? ctx.state.liftFrom : 'library';
  const unit = unitOf(data);

  // Oldest first, one entry per page the lift is on.
  const sessions = [];
  data.pages.forEach((page, i) => {
    for (const entry of page.lifts) {
      if (entry.liftId !== lift.id) continue;
      const best = log.bestSet(entry);
      sessions.push({
        bestText: best ? log.setText(best, lift) : '',
        pageId: page.id,
        note: entry.note || '',
        date: page.date,
        text: log.setsText(entry.sets, lift),
        // In pounds, whatever unit the page was written in.
        est: best ? log.toLb(log.estMax(best.w, best.r), page.unit) : 0,
        top: log.toLb(Math.max(0, ...entry.sets.filter(x => log.num(x.r) > 0).map(x => log.num(x.w))), page.unit),
        unit: page.unit,
      });
    }
  });
  // Maxes logged straight in, for the Big Three, plot alongside the pages.
  const logged = big ? (data.maxes || []).filter(m => m.liftId === lift.id) : [];
  const points = [...sessions, ...logged.map(m => ({ date: m.date, est: log.toLb(m.w, m.unit), top: log.toLb(m.w, m.unit) }))]
    .sort((a, b) => (a.date < b.date ? -1 : 1));
  const plotted = points.filter(s => (big ? s.est : s.top) > 0);
  const b = big ? bests(data, lift.id) : null;
  const heaviest = big ? b.top : (sessions.length ? Math.max(...sessions.map(s => s.top)) : 0);
  const bestSetEver = log.bestSet({
    sets: data.pages.flatMap(page => page.lifts.filter(e => e.liftId === lift.id).flatMap(e => e.sets)),
  });

  // The Big Three can be seen as their max or the heaviest weight that day;
  // other lifts just as the heaviest weight.
  const views = big
    ? [
      { key: 'est', name: w.viewEst, label: w.chartLabel },
      { key: 'top', name: w.viewTop, label: w.chartTopLabel },
    ]
    : [{ key: 'top', name: w.viewTop, label: w.chartTopLabel }];
  let view = views[0];
  const chartArt = h('div', { class: 'chart-art' });
  const chartTitle = h('p', { class: 'kicker' });
  function drawChart() {
    chartTitle.textContent = view.label;
    chartArt.innerHTML = chart(plotted.map(s => ({ date: s.date, value: fromLb(view.key === 'est' ? Math.round(s.est) : s.top, unit) })), unit, { chartLabel: view.label });
  }
  const viewButtons = views.map(v => {
    const b = h('button', {
      class: 'chip',
      type: 'button',
      'aria-pressed': String(v === view),
      onClick() {
        view = v;
        for (const other of viewButtons) other.setAttribute('aria-pressed', String(other === b));
        drawChart();
      },
    }, v.name);
    return b;
  });
  const chartBox = plotted.length >= 2
    ? h('div', { class: 'chart panel' }, chartTitle, chartArt, views.length > 1 && h('div', { class: 'chips' }, viewButtons))
    : null;
  if (chartBox) drawChart();

  const total = (n, label) => h('div', { class: 'total' },
    h('p', { class: 'total-n' }, n, h('span', { class: 'total-unit' }, ` ${unit}`)),
    h('p', { class: 'label' }, label),
  );

  // A lift of your own can have its muscles changed here.
  const own = (data.customLifts || []).some(l => l.id === lift.id);
  const about = h('p', { class: 'quiet' }, [lift.gear, lift.works, lift.helps].filter(Boolean).join(' · '));
  const musclesBox = own && h('div', { class: 'panel lift-muscles' }, musclePicker({
    words,
    works: lift.works,
    helps: lift.helps,
    onChange(m) {
      store.update(d => {
        const mine = d.customLifts.find(l => l.id === lift.id);
        if (mine) log.setLiftMuscles(mine, m);
      });
      about.textContent = [lift.gear, m.works, m.helps].filter(Boolean).join(' · ');
    },
  }).el);

  put(el,
    h('div', { class: 'head-block', style: 'padding-right:0;min-height:0;gap:4px' },
      h('p', { class: 'kicker' }, w.kicker),
      h('h1', { class: 'heading' }, lift.name),
      sessions.length > 0 && h('p', { class: 'hand' }, `${count(sessions.length, words.library.pages)} ${w.inNotebook}`),
      about,
      h('a', { class: 'btn btn-line btn-small', href: `#${from}`, style: 'align-self:flex-start;margin-top:6px' }, `← ${w.backTo[from]}`),
    ),
    h('div', { class: 'panel lift-notes' },
      h('p', { class: 'label' }, w.notesLabel),
      noteField({
        get: () => store.get().liftNotes[lift.id],
        set: text => store.updateSoon(d => {
          if (text.trim()) d.liftNotes[lift.id] = text;
          else delete d.liftNotes[lift.id];
        }),
        placeholder: words.today.notePlaceholder,
        addLabel: words.today.addNote,
        doneLabel: words.today.noteDone,
        label: `${lift.name}: ${words.today.noteLabel}`,
      }),
    ),
    musclesBox,
    big && b.max > 0 && h('div', { class: 'totals' },
      total(show(b.isTested ? b.max : Math.round(b.max), unit), b.isTested ? w.testedMax : w.estMax),
      total(show(heaviest, unit), w.heaviest),
    ),
    big && maxLogger(ctx, lift.id, lift.name),
    !big && heaviest > 0 && h('div', { class: 'totals' },
      total(show(heaviest, unit), w.heaviest),
      h('div', { class: 'total' },
        h('p', { class: 'total-n' }, bestSetEver ? log.setText(bestSetEver, lift) : '–'),
        h('p', { class: 'label' }, w.bestSet),
      ),
    ),
    logged.length > 0 && h('div', null,
      h('p', { class: 'label', style: 'line-height:32px' }, w.loggedLabel),
      h('div', { class: 'compare' }, [...logged].sort((x, y) => (x.date < y.date ? 1 : -1)).map(m => h('div', { class: 'compare-row' },
        h('span', { class: 'kicker' }, log.niceDate(m.date)),
        h('span', { class: 'compare-best' }, `${log.tidy(log.num(m.w))} ${m.unit || 'lb'}`),
        twoTap(h('button', { class: 'lift-remove', type: 'button', style: 'grid-column:1 / -1;justify-self:start' }, w.remove), w.removeConfirm, () => {
          store.update(d => { d.maxes = d.maxes.filter(x => x.id !== m.id); });
          ctx.refresh();
        }),
      ))),
    ),
    plotted.length === 1 && h('p', { class: 'hand', style: 'font-size:18px' }, w.oneMore),
    chartBox,
    sessions.length
      ? h('div', null,
        h('p', { class: 'label', style: 'line-height:32px' }, w.sessionsLabel),
        h('div', { class: 'compare' }, [...sessions].reverse().map(s => h('button', {
          class: 'compare-row session-row',
          type: 'button',
          'data-sound': 'none',
          onClick() { ctx.state.openPage = s.pageId; ctx.state.fixing = false; ctx.go('page'); },
        },
          h('span', { class: 'kicker' }, log.niceDate(s.date)),
          h('span', { class: 'compare-best' }, big ? (s.est ? `${w.best} ${show(Math.round(s.est), unit)} ${unit}` : '') : s.bestText),
          h('span', { class: 'compare-change hand' }, s.text),
          s.note && h('span', { class: 'compare-change day-note-text' }, s.note),
        ))),
      )
      : h('p', { class: 'hand', style: 'font-size:18px' }, w.never),
  );
}
