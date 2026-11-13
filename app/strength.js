// The numbers behind the Stats page: bodyweight from weigh-ins, the best
// lifts, Wilks, DOTS and strength levels. Nothing here touches the screen.
// Formulas work in kilograms; the app shows pounds.

import { LEVELS, STANDARDS } from '../content/standards.js';
import { estMax, doneSets, num } from './log.js';

export const KG = 0.45359237;
export const BIG_THREE = ['squat', 'bench-press', 'deadlift'];
const IN_POUNDS = { lb: 1, kg: 1 / KG };

// ---- bodyweight ----

// Weigh-ins, oldest first: [{ date: '2026-11-12', w: 181.4 }]
export function weighins(data) {
  return [...(data.weighins || [])].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
}

// The latest bodyweight in pounds, or 0 if there is none.
export function bodyweight(data) {
  const list = weighins(data);
  return list.length ? num(list[list.length - 1].w) : 0;
}

// ---- best lifts, in pounds ----

export function bests(data, liftId) {
  let est = 0, top = 0, estDate = '', topDate = '';
  for (const page of data.pages) {
    const toLb = IN_POUNDS[page.unit || 'lb'];
    for (const entry of page.lifts) {
      if (entry.liftId !== liftId) continue;
      for (const s of doneSets(entry)) {
        const e = estMax(s.w, s.r) * toLb;
        const t = num(s.r) >= 1 ? num(s.w) * toLb : 0;
        if (e > est) { est = e; estDate = page.date; }
        if (t > top) { top = t; topDate = page.date; }
      }
    }
  }
  // One-rep maxes logged straight in: tested, so they count as lifted.
  let tested = 0, testedDate = '';
  for (const m of data.maxes || []) {
    if (m.liftId !== liftId) continue;
    const w = num(m.w) * IN_POUNDS[m.unit || 'lb'];
    if (w > tested) { tested = w; testedDate = m.date; }
  }
  if (tested > top) { top = tested; topDate = testedDate; }
  // The max shown is whichever is higher: a tested max or the estimate.
  const max = Math.max(est, tested);
  return {
    est: Math.round(est),
    top: Math.round(top * 10) / 10,
    tested: Math.round(tested * 10) / 10,
    max: Math.round(max * 10) / 10,
    isTested: tested > 0 && tested >= est,
    estDate,
    topDate,
    maxDate: tested > 0 && tested >= est ? testedDate : estDate,
  };
}

// How much a lift's max has moved in the last 30 days, in pounds.
export function monthChange(data, liftId) {
  const points = history(data, liftId);
  if (!points.length) return 0;
  const cutoff = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);
  const before = points.filter(p => p.date < cutoff);
  const was = before.length ? Math.max(...before.map(p => p.value)) : null;
  const now = Math.max(...points.map(p => p.value));
  return was == null ? 0 : Math.round((now - was) * 10) / 10;
}

// Best estimated max on each page a lift appears, for the charts.
export function history(data, liftId) {
  const points = [];
  for (const page of data.pages) {
    const toLb = IN_POUNDS[page.unit || 'lb'];
    let best = 0;
    for (const entry of page.lifts) {
      if (entry.liftId !== liftId) continue;
      for (const s of doneSets(entry)) best = Math.max(best, estMax(s.w, s.r) * toLb);
    }
    if (best > 0) points.push({ date: page.date, value: Math.round(best) });
  }
  for (const m of data.maxes || []) {
    if (m.liftId === liftId) points.push({ date: m.date, value: Math.round(num(m.w) * IN_POUNDS[m.unit || 'lb']) });
  }
  // One point a day: the best of that day.
  const byDay = new Map();
  for (const p of points) byDay.set(p.date, Math.max(byDay.get(p.date) || 0, p.value));
  return [...byDay].map(([date, value]) => ({ date, value })).sort((a, b) => (a.date < b.date ? -1 : 1));
}

// ---- scores ----

function poly(x, coefficients) {
  return coefficients.reduce((sum, c, i) => sum + c * x ** i, 0);
}

// Wilks (the original formula), as a multiplier for a total in kilograms.
export function wilksCoefficient(bwKg, sex) {
  if (sex === 'women') {
    const x = Math.min(Math.max(bwKg, 26.51), 154.53);
    return 500 / poly(x, [594.31747775582, -27.23842536447, 0.82112226871, -0.00930733913, 4.731582e-05, -9.054e-08]);
  }
  const x = Math.min(Math.max(bwKg, 40), 201.9);
  return 500 / poly(x, [-216.0475144, 16.2606339, -0.002388645, -0.00113732, 7.01863e-06, -1.291e-08]);
}

// DOTS, as a multiplier for a total in kilograms.
export function dotsCoefficient(bwKg, sex) {
  if (sex === 'women') {
    const x = Math.min(Math.max(bwKg, 40), 150);
    return 500 / poly(x, [-57.96288, 13.6175032, -0.1126655495, 0.0005158568, -0.0000010706]);
  }
  const x = Math.min(Math.max(bwKg, 40), 210);
  return 500 / poly(x, [-307.75076, 24.0900756, -0.1918759221, 0.0007391293, -0.000001093]);
}

// Both scores for a total and a bodyweight given in pounds.
export function scores(totalLb, bwLb, sex) {
  if (!(totalLb > 0) || !(bwLb > 0) || !sex) return null;
  const totalKg = totalLb * KG;
  const bwKg = bwLb * KG;
  return {
    wilks: Math.round(totalKg * wilksCoefficient(bwKg, sex) * 10) / 10,
    dots: Math.round(totalKg * dotsCoefficient(bwKg, sex) * 10) / 10,
  };
}

// ---- strength levels ----

// Where each level starts for this lifter, in pounds.
export function levelBars(liftId, bwLb, sex) {
  const table = STANDARDS[sex];
  if (!table || !table[liftId] || !(bwLb > 0)) return null;
  const ref = table.referenceKg;
  const scale = dotsCoefficient(ref, sex) / dotsCoefficient(bwLb * KG, sex);
  return table[liftId].map(ratio => Math.round(ratio * ref * scale / KG));
}

// The level a lift reaches, and how far it is to the next one.
//   { index: 2, name: 'Intermediate', next: 'Advanced', toGo: 23, share: 0.6 }
export function level(liftId, liftLb, bwLb, sex) {
  const bars = levelBars(liftId, bwLb, sex);
  if (!bars || !(liftLb > 0)) return null;
  let index = 0;
  while (index < bars.length && liftLb >= bars[index]) index++;
  const from = index === 0 ? 0 : bars[index - 1];
  const to = bars[index];
  return {
    index,
    name: LEVELS[index],
    next: to ? LEVELS[index + 1] : null,
    toGo: to ? Math.ceil(to - liftLb) : 0,
    share: to ? Math.min(1, Math.max(0, (liftLb - from) / (to - from))) : 1,
    bars,
  };
}

export { LEVELS };
