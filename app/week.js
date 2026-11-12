// "This week": seven days, Monday to Sunday, each marked with what was done.
//   a blue check   a page with lifts
//   a purple X     boxing
//   a navy wave    other cardio
// Tap a day that has a page to open it.

import { h } from './ui.js';
import { dateKey, findCardio, doneSets } from './log.js';

const NS = 'http://www.w3.org/2000/svg';

export function mark(kind) {
  const paths = {
    lift: 'M5 13l4.5 4.5L19 6.5',
    box: 'M6 6l12 12M18 6L6 18',
    cardio: 'M3 13c2.5-4 4.5-4 6 0s3.5 4 6 0 4.5-4 6 0',
  };
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('class', `week-mark is-${kind}`);
  svg.setAttribute('aria-hidden', 'true');
  const p = document.createElementNS(NS, 'path');
  p.setAttribute('d', paths[kind]);
  svg.append(p);
  return svg;
}

// What happened on each day of the week holding `today`.
export function weekOf(data, today = new Date()) {
  const monday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - ((today.getDay() + 6) % 7));
  return Array.from({ length: 7 }, (_, i) => {
    const day = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + i);
    const key = dateKey(day);
    const pages = data.pages.filter(p => p.date === key);
    const cardio = pages.flatMap(p => p.cardio || []).filter(c => c.done !== false);
    return {
      key,
      day,
      pages,
      lifted: pages.some(p => p.lifts.some(e => doneSets(e).length || e.sets.length)),
      boxed: cardio.some(c => findCardio(c.kindId).boxing),
      ran: cardio.some(c => !findCardio(c.kindId).boxing),
      isToday: key === dateKey(today),
      isFuture: day > today,
    };
  });
}

export function weekStrip(data, words, onOpen) {
  const days = weekOf(data);
  const trained = days.filter(d => d.pages.length).length;
  const strip = h('div', { class: 'week', role: 'list' }, days.map(d => {
    const marks = [d.lifted && mark('lift'), d.boxed && mark('box'), d.ran && mark('cardio')].filter(Boolean);
    const said = [d.lifted && words.lifted, d.boxed && words.boxed, d.ran && words.cardio].filter(Boolean).join(', ') || words.rest;
    const label = `${d.day.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}: ${d.isFuture ? words.ahead : said}`;
    const cls = `week-day${d.isToday ? ' is-today' : ''}${d.isFuture ? ' is-future' : ''}`;
    const inside = [
      h('span', { class: 'week-name' }, d.day.toLocaleDateString('en-US', { weekday: 'narrow' })),
      h('span', { class: 'week-date' }, String(d.day.getDate())),
      h('span', { class: 'week-marks' }, marks),
    ];
    return d.pages.length
      ? h('button', { class: cls, type: 'button', role: 'listitem', 'aria-label': label, onClick: () => onOpen(d.pages[d.pages.length - 1]) }, inside)
      : h('div', { class: cls, role: 'listitem', 'aria-label': label }, inside);
  }));
  return h('div', { class: 'week-box' },
    h('div', { class: 'row' },
      h('p', { class: 'label' }, words.label),
      h('p', { class: 'hand week-count' }, `${trained} ${trained === 1 ? words.day : words.days}`),
    ),
    strip,
    h('p', { class: 'week-key' },
      mark('lift'), words.lifted, mark('box'), words.boxed, mark('cardio'), words.cardio,
    ),
  );
}
