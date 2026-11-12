// One lift's story: its estimated max plotted by hand, page by page, and
// every session it appears on.

import { h, put, count, noteField } from '../ui.js';
import { chart } from '../chart.js';
import * as log from '../log.js';

export function render(el, ctx) {
  const { words, store } = ctx;
  const w = words.lift;
  const data = store.get();
  const lift = log.findLift(data, ctx.state.openLift);

  // Oldest first, one entry per page the lift is on.
  const sessions = [];
  data.pages.forEach((page, i) => {
    for (const entry of page.lifts) {
      if (entry.liftId !== lift.id) continue;
      const best = log.bestSet(entry);
      sessions.push({
        pageId: page.id,
        note: entry.note || '',
        date: page.date,
        text: log.setsText(entry.sets, lift),
        est: best ? Math.round(log.estMax(best.w, best.r)) : 0,
        top: Math.max(0, ...entry.sets.filter(x => log.num(x.r) > 0).map(x => log.num(x.w))),
        unit: page.unit,
      });
    }
  });
  const plotted = sessions.filter(s => s.est > 0);
  const bestEver = plotted.length ? Math.max(...plotted.map(s => s.est)) : 0;
  const heaviest = plotted.length ? Math.max(...plotted.map(s => s.top)) : 0;

  // Two ways to look at it: estimated max, or the heaviest weight that day.
  const views = [
    { key: 'est', name: w.viewEst, label: w.chartLabel },
    { key: 'top', name: w.viewTop, label: w.chartTopLabel },
  ];
  let view = views[0];
  const chartArt = h('div', { class: 'chart-art' });
  const chartTitle = h('p', { class: 'kicker' });
  function drawChart() {
    chartTitle.textContent = view.label;
    chartArt.innerHTML = chart(plotted.map(s => ({ date: s.date, value: s[view.key] })), 'lb', { chartLabel: view.label });
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
    ? h('div', { class: 'chart panel' }, chartTitle, chartArt, h('div', { class: 'chips' }, viewButtons))
    : null;
  if (chartBox) drawChart();

  const total = (n, label) => h('div', { class: 'total' },
    h('p', { class: 'total-n' }, n, h('span', { class: 'total-unit' }, ' lb')),
    h('p', { class: 'label' }, label),
  );

  put(el,
    h('div', { class: 'head-block', style: 'padding-right:0;min-height:0;gap:4px' },
      h('p', { class: 'kicker' }, w.kicker),
      h('h1', { class: 'heading' }, lift.name),
      sessions.length > 0 && h('p', { class: 'hand' }, `${count(sessions.length, words.library.pages)} ${w.inNotebook}`),
      h('p', { class: 'quiet' }, [lift.gear, lift.works, lift.helps].filter(Boolean).join(' · ')),
      h('a', { class: 'btn btn-line btn-small', href: '#library', style: 'align-self:flex-start;margin-top:6px' }, `← ${w.back}`),
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
    bestEver > 0 && h('div', { class: 'totals' },
      total(`${bestEver}`, w.estMax),
      total(`${heaviest}`, w.heaviest),
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
          h('span', { class: 'compare-best' }, s.est ? `${w.best} ${s.est} ${s.unit}` : ''),
          h('span', { class: 'compare-change hand' }, s.text),
          s.note && h('span', { class: 'compare-change day-note-text' }, s.note),
        ))),
      )
      : h('p', { class: 'hand', style: 'font-size:18px' }, w.never),
  );
}
