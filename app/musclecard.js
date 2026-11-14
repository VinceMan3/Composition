// A muscle's card, styled like an old baseball card. The front is all art:
// a close-up of the muscle from the drawing, a slanted name stripe, the team
// (its group) and a round badge with the card number. Flip it for the
// cardboard back: what it does, "Did you know?", sets this week and the day
// it was last trained, and a button that slides in the lifts that train it.
//   muscleCard({ ctx, partId, fig, info, onLift, onClose })
// fig is the drawing the close-up comes from (app/mapart.js); info is
// { train, lifts } worked out once by the map page: sets per part, and the
// lifts that train each part with the ones you have done marked.
// After the card is on the page, call layout() so the close-up and the
// writing fit the card.

import { h } from './ui.js';
import { PARTS, partById, groupById } from './muscles.js';
import { niceDate, dateKey, tidy } from './log.js';
import { closeUp, cropFor } from './mapart.js';

// Each card's sizes, once worked out, by part and card width.
const fitted = new Map();

export function muscleCard({ ctx, partId, fig, info, onLift, onClose }) {
  const { words, sound } = ctx;
  const w = words.map;
  const part = partById.get(partId);
  const group = groupById.get(part.group);
  const number = String(PARTS.indexOf(part) + 1).padStart(2, '0');
  const t = info.train.get(partId);
  const rows = info.lifts(partId); // [{ lift, role: 'main' | 'helps', mine }]

  let flipped = false;
  const flipButtons = [];
  function flip(on = !flipped, quiet = false) {
    flipped = on;
    inner.classList.toggle('is-flipped', flipped);
    front.setAttribute('aria-hidden', String(flipped));
    back.setAttribute('aria-hidden', String(!flipped));
    front.inert = flipped;
    back.inert = !flipped;
    for (const b of flipButtons) b.setAttribute('aria-pressed', String(flipped));
    if (!quiet) sound.play('cardflip');
  }
  const flipButton = cls => {
    const b = h('button', { class: `tc-flip ${cls}`, type: 'button', 'data-sound': 'none', 'aria-label': w.flip, 'aria-pressed': 'false', onClick(e) { e.stopPropagation(); flip(); } },
      h('span', { 'aria-hidden': 'true' }, '↻ '), w.flipHint);
    flipButtons.push(b);
    return b;
  };

  // ----- the front: the art, the stripe, the badge -----
  const cu = closeUp(fig, partId, null);
  const photo = h('div', { class: 'tc-photo' }, cu.el);
  const name = h('h2', { class: 'tc-name' }, part.name);
  const stripe = h('div', { class: 'tc-stripe' }, name);
  const front = h('div', { class: 'tc-face tc-front' },
    photo,
    h('div', { class: 'tc-badge', 'aria-hidden': 'true' }, h('span', { class: 'tc-badge-no' }, w.cardNumber), h('b', null, number)),
    h('p', { class: 'tc-team' }, group.name),
    stripe,
    flipButton('on-front'),
  );

  // ----- the back: cardboard, printed in one ink -----
  const today = dateKey();
  const sets = t ? tidy(t.week) : '0';
  const last = !t || !t.last ? w.never : t.last === today ? w.today : niceDate(t.last);
  const about = h('div', { class: 'tc-about' },
    h('p', { class: 'tc-does' }, part.does),
    h('p', { class: 'tc-dyk' }, w.didYouKnow),
    h('p', { class: 'tc-fact' }, part.fact),
  );
  const liftsPane = h('div', { class: 'tc-liftpane', hidden: true },
    h('div', { class: 'tc-lifts' }, rows.length
      ? rows.map(({ lift, role, mine }) => h('button', {
        class: 'tc-lift',
        type: 'button',
        onClick(e) { e.stopPropagation(); onLift(lift.id, flipped); },
      },
        h('span', { class: 'tc-lift-name' }, lift.name),
        mine && h('span', { class: 'tc-lift-mine', 'aria-label': w.logged, title: w.logged }, '✓'),
        h('span', { class: `tc-lift-role is-${role}` }, role === 'main' ? w.main : w.helps),
      ))
      : h('p', { class: 'tc-none' }, w.noLifts)),
  );
  const stats = h('div', { class: 'tc-stats' },
    h('div', { class: 'tc-stat' }, h('p', { class: 'tc-stat-n' }, sets), h('p', { class: 'tc-stat-label' }, w.setsWeek)),
    h('div', { class: 'tc-stat' }, h('p', { class: 'tc-stat-n is-date' }, last), h('p', { class: 'tc-stat-label' }, w.lastTrained)),
  );
  const toLifts = h('button', { class: 'tc-to-lifts', type: 'button', onClick(e) { e.stopPropagation(); showLifts(true); } },
    `${w.liftsLabel} · ${rows.length} `, h('span', { 'aria-hidden': 'true' }, '›'));
  const fromLifts = h('button', { class: 'tc-to-lifts is-back', type: 'button', hidden: true, onClick(e) { e.stopPropagation(); showLifts(false); } },
    h('span', { 'aria-hidden': 'true' }, '‹ '), w.backToCard);
  function showLifts(on) {
    liftsPane.hidden = !on;
    about.hidden = on;
    stats.hidden = on;
    toLifts.hidden = on;
    fromLifts.hidden = !on;
  }
  const back = h('div', { class: 'tc-face tc-back' },
    h('div', { class: 'tc-back-in' },
      h('div', { class: 'tc-back-head' },
        h('h2', { class: 'tc-back-name' }, part.name),
        h('span', { class: 'tc-back-team' }, `${w.cardNumber} ${number} · ${group.name}`),
      ),
      about,
      liftsPane,
      stats,
      h('div', { class: 'tc-back-foot' }, toLifts, fromLifts, flipButton('on-back')),
    ),
  );

  const inner = h('div', { class: 'tc-inner' }, front, back);
  // Tapping anywhere on the card flips it too, except on its buttons.
  inner.addEventListener('click', e => { if (!e.target.closest('button')) flip(); });
  const el = h('div', { class: 'tc', role: 'region', 'aria-label': `${w.cardLabel}: ${part.name}, ${group.name}`, 'data-part': partId },
    inner,
    h('button', { class: 'tc-close', type: 'button', 'aria-label': w.close, onClick(e) { e.stopPropagation(); onClose(); } }, '×'),
  );
  flip(false, true);

  // Fit the close-up to the window's shape, the name to its stripe, and the
  // back's writing to the cardboard, so nothing is ever cut off.
  function layout() {
    const r = photo.getBoundingClientRect();
    if (r.width && r.height) cu.place(cropFor(fig, partId, r.width / r.height, 0.42));
    const key = `${partId}:${Math.round(r.width)}`;
    const keep = fitted.get(key);
    if (keep) {
      name.style.fontSize = `${keep[0]}px`;
      about.style.fontSize = `${keep[1]}px`;
      return;
    }
    let n = 30;
    name.style.fontSize = `${n}px`;
    while (name.scrollWidth > stripe.clientWidth - 18 && n > 17) {
      n -= 1;
      name.style.fontSize = `${n}px`;
    }
    let a = 15;
    about.style.fontSize = `${a}px`;
    while (about.scrollHeight > about.clientHeight + 1 && a > 11) {
      a -= 0.5;
      about.style.fontSize = `${a}px`;
    }
    if (r.width) fitted.set(key, [n, a]);
  }
  return { el, flip, layout, isFlipped: () => flipped };
}
