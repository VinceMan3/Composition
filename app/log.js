// The arithmetic and bookkeeping behind a workout page. Nothing here touches
// the screen, so it is easy to test and reuse on later pages (stats, notebook).
//
// A page looks like this:
//   { id, date: '2026-11-12', title: 'Chest day', startedAt, filedAt, unit: 'lb',
//     lifts: [ { liftId: 'bench-press', sets: [ { w: '185', r: '5', rpe: '', done: true } ] } ] }

import { LIFTS } from '../content/lifts.js';

export const STEP = { lb: 5, kg: 2.5 };
const BAR = { lb: 45, kg: 20 };
const PLATES = { lb: [45, 35, 25, 10, 5, 2.5], kg: [25, 20, 15, 10, 5, 2.5, 1.25] };

export function num(value) {
  const n = parseFloat(value);
  return Number.isFinite(n) ? n : 0;
}

// 185 -> "185", 187.5 -> "187.5"
export function tidy(n) {
  return String(Math.round(n * 100) / 100);
}

export function dateKey(date = new Date()) {
  const pad = n => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

// "Wed · Nov 11" from "2026-11-11"
export function niceDate(key) {
  const [y, m, d] = key.split('-').map(Number);
  const date = new Date(y, m - 1, d);
  const day = date.toLocaleDateString('en-US', { weekday: 'short' });
  return `${day} · ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
}

// ---- lifts ----

export function allLifts(data) {
  return [...LIFTS, ...(data.customLifts || [])];
}

export function findLift(data, id) {
  return allLifts(data).find(l => l.id === id) || { id, name: id, group: 'Other', gear: '' };
}

export function isBarbell(lift) {
  return /barbell/i.test(lift.gear || '');
}

export function addCustomLift(data, name) {
  const clean = name.trim().replace(/\s+/g, ' ');
  const base = 'my-' + (clean.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'lift');
  let id = base;
  for (let i = 2; allLifts(data).some(l => l.id === id); i++) id = `${base}-${i}`;
  const lift = { id, name: clean, group: 'Yours', gear: '' };
  data.customLifts = [...(data.customLifts || []), lift];
  return lift;
}

// ---- pages ----

function blankSet() {
  return { w: '', r: '', rpe: '', done: false };
}

export function newPage(title) {
  return {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
    date: dateKey(),
    title,
    startedAt: Date.now(),
    filedAt: null,
    unit: 'lb',
    lifts: [],
  };
}

// The most recent filed entry for a lift, or null.
export function lastTime(data, liftId) {
  for (let i = data.pages.length - 1; i >= 0; i--) {
    const entry = data.pages[i].lifts.find(l => l.liftId === liftId);
    if (entry) return entry;
  }
  return null;
}

export function addLift(data, page, liftId) {
  const prev = lastTime(data, liftId);
  const count = prev ? Math.min(Math.max(prev.sets.length, 1), 8) : 3;
  page.lifts.push({ liftId, sets: Array.from({ length: count }, blankSet) });
}

// A new page with the same title and lifts as an old one.
export function repeatPage(data, old) {
  const page = newPage(old.title);
  for (const entry of old.lifts) addLift(data, page, entry.liftId);
  return page;
}

// Past pages worth offering to repeat: the newest of each title.
export function pagesToRepeat(data, limit = 4) {
  const seen = new Set();
  const list = [];
  for (let i = data.pages.length - 1; i >= 0 && list.length < limit; i--) {
    const key = data.pages[i].title.trim().toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    list.push(data.pages[i]);
  }
  return list;
}

// What to pencil in for a set, before anything is written.
export function ghost(entry, index, prev) {
  const above = entry.sets.slice(0, index).reverse().find(s => s.w || s.r);
  const then = prev && prev.sets.length ? prev.sets[Math.min(index, prev.sets.length - 1)] : null;
  return {
    w: (above && above.w) || (then && then.w) || '',  // today's weight carries down the page
    r: (then && then.r) || (above && above.r) || '',
  };
}

// "185 × 5, 5, 4" when the weight never changes, otherwise each set in full.
export function setsText(sets, lift) {
  if (!sets.length) return '';
  const sameWeight = sets.every(s => num(s.w) === num(sets[0].w));
  if (sameWeight && num(sets[0].w) && lift.kind !== 'timed') {
    return `${tidy(num(sets[0].w))} × ${sets.map(s => s.r).join(', ')}`;
  }
  return sets.map(s => setText(s, lift)).join(', ');
}

// ---- sums ----

// Estimated one-rep max (Epley). One rep is the weight itself.
export function estMax(w, r) {
  w = num(w); r = num(r);
  if (!w || !r) return 0;
  return r === 1 ? w : w * (1 + r / 30);
}

export function doneSets(entry) {
  return entry.sets.filter(s => s.done);
}

export function bestSet(entry) {
  let best = null;
  for (const s of doneSets(entry)) {
    const score = estMax(s.w, s.r) || num(s.r) / 1000; // no weight: more reps wins
    if (!best || score > best.score) best = { ...s, score };
  }
  return best;
}

export function volume(entry) {
  return doneSets(entry).reduce((sum, s) => sum + num(s.w) * num(s.r), 0);
}

// "185 × 5" or "12 reps" or "45 sec"
export function setText(s, lift) {
  if (lift.kind === 'timed') return num(s.w) ? `${tidy(num(s.w))} × ${s.r} sec` : `${s.r} sec`;
  return num(s.w) ? `${tidy(num(s.w))} × ${s.r}` : `${s.r} reps`;
}

// How one set compares with another: { text: '+5 lb', dir: 1 }
export function compare(cur, prev, unit, lift) {
  if (!prev || !num(prev.r)) return null;
  const dw = num(cur.w) - num(prev.w);
  const dr = num(cur.r) - num(prev.r);
  const repWord = lift && lift.kind === 'timed' ? 'sec' : Math.abs(dr) === 1 ? 'rep' : 'reps';
  const sign = n => (n > 0 ? '+' : '−') + tidy(Math.abs(n));
  if (dw) return { text: `${sign(dw)} ${unit}`, dir: Math.sign(dw) };
  if (dr) return { text: `${sign(dr)} ${repWord}`, dir: Math.sign(dr) };
  return { text: '', dir: 0 };
}

// Which plates go on each side of the bar.
export function plates(total, unit = 'lb') {
  const bar = BAR[unit];
  let side = (num(total) - bar) / 2;
  if (side < 0) return null;
  const list = [];
  for (const p of PLATES[unit]) {
    while (side >= p - 1e-9) { list.push(p); side -= p; }
  }
  return { bar, list, left: Math.round(side * 100) / 100 };
}

// ---- filing ----

// Best estimated max for a lift across every filed page.
function bestEver(data, liftId) {
  let best = 0;
  for (const page of data.pages) {
    for (const entry of page.lifts) {
      if (entry.liftId !== liftId) continue;
      for (const s of doneSets(entry)) best = Math.max(best, estMax(s.w, s.r));
    }
  }
  return best;
}

// Everything the "page filed" screen shows. Work it out before the page
// joins the notebook, so "last time" still means the time before.
export function summarize(data, page) {
  const out = { lifts: 0, sets: 0, volume: 0, minutes: 0, records: [], rows: [] };
  for (const entry of page.lifts) {
    const done = doneSets(entry);
    if (!done.length) continue;
    const lift = findLift(data, entry.liftId);
    const best = bestSet(entry);
    const prev = lastTime(data, entry.liftId);
    const prevBest = prev ? bestSet(prev) : null;
    out.lifts += 1;
    out.sets += done.length;
    out.volume += volume(entry);
    out.rows.push({
      name: lift.name,
      best: setText(best, lift),
      change: prevBest ? compare(best, prevBest, page.unit, lift) : null,
    });
    const top = Math.max(...done.map(s => estMax(s.w, s.r)));
    const before = bestEver(data, entry.liftId);
    if (before && top > before + 0.01) {
      out.records.push({ name: lift.name, now: Math.round(top), was: Math.round(before) });
    }
  }
  out.minutes = Math.max(1, Math.round(((page.filedAt || Date.now()) - page.startedAt) / 60000));
  return out;
}

// Move the page being written into the notebook. Unchecked sets and empty
// lifts are left off. Returns the summary.
export function fileDraft(data) {
  const page = data.draft;
  page.filedAt = Date.now();
  page.title = page.title.trim();
  page.lifts = page.lifts
    .map(entry => ({ ...entry, sets: doneSets(entry) }))
    .filter(entry => entry.sets.length);
  const summary = summarize(data, page);
  page.summary = summary;
  data.pages.push(page);
  data.draft = null;
  return summary;
}
