// One lift's story: its estimated max plotted by hand, page by page, and
// every session it appears on.

import { h, put, count, noteField } from '../ui.js';
import * as log from '../log.js';

// The chart is drawn as if by hand on graph paper: a wobbly blue pen line,
// pencil hatching under it, a dot per page, and the best day ringed in red.
// `points` are { date, value } in order; `labels` holds the wording.
function chart(points, unit, labels) {
  const W = 340, H = 230;
  const L = 40, R = 18, T = 26, B = 30;
  const plotW = W - L - R, plotH = H - T - B;
  const times = points.map(p => Date.parse(p.date));
  const t0 = times[0], t1 = times[times.length - 1];
  const xs = i => L + (t1 === t0 ? plotW / 2 : (times[i] - t0) / (t1 - t0) * plotW);
  let lo = Math.min(...points.map(p => p.value));
  let hi = Math.max(...points.map(p => p.value));
  // Round the scale out to tidy steps of 5, 10 or 25.
  const span = Math.max(hi - lo, 10);
  const step = span > 120 ? 25 : span > 40 ? 10 : 5;
  lo = Math.max(0, Math.floor((lo - span * 0.15) / step) * step);
  hi = Math.ceil((hi + span * 0.15) / step) * step;
  const ys = v => T + plotH * (1 - (v - lo) / (hi - lo));
  const bestI = points.reduce((bi, p, i) => (p.value >= points[bi].value ? i : bi), 0);
  const lastI = points.length - 1;
  const ticks = [];
  const every = Math.max(step, Math.ceil((hi - lo) / 4 / step) * step);
  for (let v = lo; v <= hi + 0.01; v += every) ticks.push(v);

  // Month names along the bottom, where a new month starts.
  const months = [];
  let seen = '';
  points.forEach((p, i) => {
    const m = new Date(times[i]).toLocaleDateString('en-US', { month: 'short', timeZone: 'UTC' });
    if (m !== seen) { months.push({ x: xs(i), m }); seen = m; }
  });
  const line = points.map((p, i) => `${xs(i).toFixed(1)},${ys(p.value).toFixed(1)}`).join(' ');
  const area = `${xs(0).toFixed(1)},${T + plotH} ${line} ${xs(lastI).toFixed(1)},${T + plotH}`;
  const bx = xs(bestI), by = ys(points[bestI].value);
  const lx = xs(lastI), ly = ys(points[lastI].value);
  const hand = 'font-family="Handlee, cursive"';
  const tag = (x, y, text, color, anchor) =>
    `<text x="${x.toFixed(1)}" y="${y.toFixed(1)}" text-anchor="${anchor}" ${hand} font-size="15" fill="${color}">${text}</text>`;
  const anchorFor = x => (x > W - 60 ? 'end' : x < L + 30 ? 'start' : 'middle');

  return `
  <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${labels.chartLabel}">
    <defs>
      <pattern id="graph" width="10" height="10" patternUnits="userSpaceOnUse">
        <path d="M10 0H0V10" fill="none" stroke="#A9C4D6" stroke-width=".6" opacity=".7"/>
      </pattern>
      <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-38)">
        <line x1="0" y1="0" x2="0" y2="6" stroke="#8D877B" stroke-width="1.1" opacity=".55"/>
      </pattern>
      <filter id="wob" x="-5%" y="-10%" width="110%" height="120%">
        <feTurbulence type="fractalNoise" baseFrequency=".03" numOctaves="2" seed="11" result="n"/>
        <feDisplacementMap in="SourceGraphic" in2="n" scale="2.6"/>
      </filter>
    </defs>
    <rect x="${L}" y="${T}" width="${plotW}" height="${plotH}" fill="url(#graph)"/>
    <g filter="url(#wob)">
      ${ticks.map(v => `<line x1="${L}" y1="${ys(v).toFixed(1)}" x2="${W - R}" y2="${ys(v).toFixed(1)}" stroke="#8D877B" stroke-width=".9" stroke-dasharray="2 4"/>`).join('')}
      <line x1="${L}" y1="${T - 6}" x2="${L}" y2="${T + plotH}" stroke="#2B2420" stroke-width="1.6"/>
      <line x1="${L}" y1="${T + plotH}" x2="${W - R + 6}" y2="${T + plotH}" stroke="#2B2420" stroke-width="1.6"/>
      <polygon points="${area}" fill="url(#hatch)"/>
      <polyline points="${line}" fill="none" stroke="#22347F" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>
      ${points.map((p, i) => `<circle cx="${xs(i).toFixed(1)}" cy="${ys(p.value).toFixed(1)}" r="3.3" fill="#F6EDCD" stroke="#22347F" stroke-width="2.2"/>`).join('')}
      <ellipse cx="${bx.toFixed(1)}" cy="${by.toFixed(1)}" rx="10" ry="8.5" fill="none" stroke="#C8452F" stroke-width="2" transform="rotate(-14 ${bx.toFixed(1)} ${by.toFixed(1)})"/>
    </g>
    ${tag(bx, by - 14, `${points[bestI].value}`, '#C8452F', anchorFor(bx))}
    ${lastI !== bestI ? tag(lx, ly + 22, `${points[lastI].value}`, '#22347F', anchorFor(lx)) : ''}
    ${ticks.map(v => `<text x="${L - 6}" y="${(ys(v) + 4).toFixed(1)}" text-anchor="end" ${hand} font-size="12" fill="#4A3B2C">${v}</text>`).join('')}
    ${months.map(({ x, m }) => `<text x="${Math.min(x, W - R - 12).toFixed(1)}" y="${H - 9}" text-anchor="middle" ${hand} font-size="12" fill="#4A3B2C">${m}</text>`).join('')}
    <text x="${L}" y="${T - 10}" ${hand} font-size="12" fill="#4A3B2C">${unit}</text>
  </svg>`;
}

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
        ))),
      )
      : h('p', { class: 'hand', style: 'font-size:18px' }, w.never),
  );
}
