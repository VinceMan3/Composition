// Stickers: the four that come with the notebook, and the ones you earn by
// training. To add one: draw the art, put it in art/, add a line to STICKERS
// with an `earned` test, and it shows up in the sticker book by itself.
//
//   size  how wide it is on the cover, as a share of the cover's width
//   turn  how many degrees it is tilted
//   how   what the sticker book says before you have it

import { estMax, doneSets, doneCardio, findCardio, num, dateKey } from './log.js';

const IN_POUNDS = { lb: 1, kg: 2.20462 };

// The heaviest weight (in pounds) ever checked off for a lift.
function heaviest(data, liftId) {
  let best = 0;
  for (const page of data.pages) {
    for (const entry of page.lifts) {
      if (entry.liftId !== liftId) continue;
      for (const s of doneSets(entry)) if (num(s.r) >= 1) best = Math.max(best, num(s.w) * IN_POUNDS[page.unit || 'lb']);
    }
  }
  return best;
}

// The best estimated one-rep max (in pounds) for a lift.
function bestMax(data, liftId) {
  let best = 0;
  for (const page of data.pages) {
    for (const entry of page.lifts) {
      if (entry.liftId !== liftId) continue;
      for (const s of doneSets(entry)) best = Math.max(best, estMax(s.w, s.r) * IN_POUNDS[page.unit || 'lb']);
    }
  }
  return best;
}

function cardioEntries(data) {
  return data.pages.flatMap(page => doneCardio(page));
}

// Three pages inside any seven days.
function threeInAWeek(data) {
  const days = data.pages.map(p => Date.parse(p.date)).sort((a, b) => a - b);
  return days.some((day, i) => i >= 2 && day - days[i - 2] <= 6 * 86400000);
}

export const STICKERS = [
  { id: 'gloves', name: 'Hanging Gloves', art: 'sticker-gloves.png', size: 0.31, turn: -8 },
  { id: 'pose', name: 'Front Double Biceps', art: 'sticker-pose.png', size: 0.36, turn: 5 },
  { id: 'barbell', name: 'Loaded Barbell', art: 'sticker-barbell.png', size: 0.4, turn: -5 },
  { id: 'ribbons', name: 'Contest Ribbons', art: 'sticker-ribbons.png', size: 0.28, turn: 9 },

  { id: 'first-page', name: 'First Page', art: 'badge-first-page.webp', size: 0.32, turn: -7,
    how: 'File your first page.',
    earned: data => data.pages.length >= 1 },
  { id: 'record', name: 'Record Breaker', art: 'badge-record.webp', size: 0.27, turn: 6,
    how: 'Beat one of your own records.',
    earned: data => data.pages.some(p => p.summary && p.summary.records && p.summary.records.length) },
  { id: 'week-3', name: 'Three Days In', art: 'badge-week-3.webp', size: 0.32, turn: 5,
    how: 'File three pages inside one week.',
    earned: threeInAWeek },
  { id: 'pages-10', name: 'Ten Pages', art: 'badge-pages-10.webp', size: 0.28, turn: -4,
    how: 'File 10 pages.',
    earned: data => data.pages.length >= 10 },
  { id: 'pages-50', name: 'Fifty Pages', art: 'badge-pages-50.webp', size: 0.28, turn: 7,
    how: 'File 50 pages.',
    earned: data => data.pages.length >= 50 },
  { id: 'bench-225', name: 'Two Plate Bench', art: 'badge-bench-225.webp', size: 0.28, turn: -6,
    how: 'Bench press 225 lb.',
    earned: data => heaviest(data, 'bench-press') >= 225 },
  { id: 'squat-315', name: 'Three Plate Squat', art: 'badge-squat-315.webp', size: 0.28, turn: 4,
    how: 'Squat 315 lb.',
    earned: data => heaviest(data, 'squat') >= 315 },
  { id: 'dead-405', name: 'Four Plate Deadlift', art: 'badge-dead-405.webp', size: 0.28, turn: -3,
    how: 'Deadlift 405 lb.',
    earned: data => heaviest(data, 'deadlift') >= 405 },
  { id: 'club-1000', name: '1000 Pound Club', art: 'badge-club-1000.webp', size: 0.3, turn: -5,
    how: 'Squat, bench and deadlift maxes that add up to 1,000 lb.',
    earned: data => bestMax(data, 'squat') + bestMax(data, 'bench-press') + bestMax(data, 'deadlift') >= 1000 },
  { id: 'bag-5', name: 'Bag Work', art: 'badge-bag-5.webp', size: 0.28, turn: 8,
    how: 'Log five boxing sessions.',
    earned: data => cardioEntries(data).filter(c => findCardio(c.kindId).boxing).length >= 5 },
  { id: 'road-10', name: 'Road Work', art: 'badge-road-10.webp', size: 0.29, turn: 0,
    how: 'Run 10 miles in total.',
    earned: data => cardioEntries(data).filter(c => c.kindId === 'running').reduce((sum, c) => sum + num(c.values.miles), 0) >= 10 },
];

export function findSticker(id) {
  return STICKERS.find(s => s.id === id);
}

export function hasSticker(data, sticker) {
  return !sticker.earned || !!data.earned[sticker.id];
}

// Stickers showing on the cover right now.
export function onCover(data) {
  return STICKERS.filter(s => hasSticker(data, s) && !(data.stickers[s.id] && data.stickers[s.id].off));
}

// Hand out anything newly earned. Returns the ids of the new ones.
export function collect(data) {
  const fresh = [];
  for (const sticker of STICKERS) {
    if (!sticker.earned || data.earned[sticker.id]) continue;
    let ok = false;
    try { ok = sticker.earned(data); } catch { ok = false; }
    if (!ok) continue;
    data.earned[sticker.id] = dateKey();
    fresh.push(sticker.id);
  }
  return fresh;
}
