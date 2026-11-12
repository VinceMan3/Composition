// Hand-plotted charts, shared by the lift history and the stats pages.

// The chart is drawn as if by hand on graph paper: a wobbly blue pen line,
// pencil hatching under it, a dot per page, and the best day ringed in red.
// `points` are { date, value } in order; `labels` holds the wording.
export function chart(points, unit, labels, id = 'c') {
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
      <pattern id="${id}-graph" width="10" height="10" patternUnits="userSpaceOnUse">
        <path d="M10 0H0V10" fill="none" stroke="#A9C4D6" stroke-width=".6" opacity=".7"/>
      </pattern>
      <pattern id="${id}-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-38)">
        <line x1="0" y1="0" x2="0" y2="6" stroke="#8D877B" stroke-width="1.1" opacity=".55"/>
      </pattern>
      <filter id="${id}-wob" x="-5%" y="-10%" width="110%" height="120%">
        <feTurbulence type="fractalNoise" baseFrequency=".03" numOctaves="2" seed="11" result="n"/>
        <feDisplacementMap in="SourceGraphic" in2="n" scale="2.6"/>
      </filter>
    </defs>
    <rect x="${L}" y="${T}" width="${plotW}" height="${plotH}" fill="url(#${id}-graph)"/>
    <g filter="url(#${id}-wob)">
      ${ticks.map(v => `<line x1="${L}" y1="${ys(v).toFixed(1)}" x2="${W - R}" y2="${ys(v).toFixed(1)}" stroke="#8D877B" stroke-width=".9" stroke-dasharray="2 4"/>`).join('')}
      <line x1="${L}" y1="${T - 6}" x2="${L}" y2="${T + plotH}" stroke="#2B2420" stroke-width="1.6"/>
      <line x1="${L}" y1="${T + plotH}" x2="${W - R + 6}" y2="${T + plotH}" stroke="#2B2420" stroke-width="1.6"/>
      <polygon points="${area}" fill="url(#${id}-hatch)"/>
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
