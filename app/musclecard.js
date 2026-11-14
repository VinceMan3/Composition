// A muscle's trading card, like the ones from an old pack. The front has a
// close-up from the drawing, the card number, the name, what it does and a
// "Did you know?". Flip it over for the back: sets this week, the day it was
// last trained, and the lifts that train it.
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

// Each card's writing size, once worked out, by part and card width.
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
  const flipButton = () => {
    const b = h('button', { class: 'tc-flip', type: 'button', 'data-sound': 'none', 'aria-label': w.flip, 'aria-pressed': 'false', onClick(e) { e.stopPropagation(); flip(); } },
      h('span', { 'aria-hidden': 'true' }, '↻ '), w.flipHint);
    flipButtons.push(b);
    return b;
  };

  // ----- the front -----
  const cu = closeUp(fig, partId, null);
  const artBox = h('div', { class: 'tc-art' }, cu.el, h('p', { class: 'tc-team' }, group.name));
  const front = h('div', { class: 'tc-face tc-front' },
    h('div', { class: 'tc-frame' },
      artBox,
      h('div', { class: 'tc-text' },
        h('div', { class: 'tc-plate' },
          h('span', { class: 'tc-no' }, `${w.cardNumber} ${number}`),
          h('h2', { class: 'tc-name' }, part.name),
        ),
        h('div', { class: 'tc-info' },
          h('p', { class: 'tc-does' }, part.does),
          h('p', { class: 'tc-dyk' }, w.didYouKnow),
          h('p', { class: 'tc-fact' }, part.fact),
          flipButton(),
        ),
      ),
    ),
  );

  // ----- the back -----
  const today = dateKey();
  const sets = t ? tidy(t.week) : '0';
  const last = !t || !t.last ? w.never : t.last === today ? w.today : niceDate(t.last);
  const back = h('div', { class: 'tc-face tc-back' },
    h('div', { class: 'tc-back-in' },
      h('div', { class: 'tc-back-head' },
        h('span', { class: 'tc-no' }, `${w.cardNumber} ${number}`),
        h('h2', { class: 'tc-back-name' }, part.name),
        h('span', { class: 'tc-back-team' }, group.name),
      ),
      h('div', { class: 'tc-stats' },
        h('div', { class: 'tc-stat' }, h('p', { class: 'tc-stat-n' }, sets), h('p', { class: 'tc-stat-label' }, w.setsWeek)),
        h('div', { class: 'tc-stat' }, h('p', { class: 'tc-stat-n is-date' }, last), h('p', { class: 'tc-stat-label' }, w.lastTrained)),
      ),
      h('p', { class: 'tc-lifts-label' }, w.liftsLabel),
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
      flipButton(),
    ),
  );

  const inner = h('div', { class: 'tc-inner' }, front, back);
  // Tapping anywhere on the card flips it too, except on the lifts.
  inner.addEventListener('click', e => { if (!e.target.closest('button')) flip(); });
  const el = h('div', { class: 'tc', role: 'region', 'aria-label': `${w.cardLabel}: ${part.name}, ${group.name}`, 'data-part': partId },
    inner,
    h('button', { class: 'tc-close', type: 'button', 'aria-label': w.close, onClick(e) { e.stopPropagation(); onClose(); } }, '×'),
  );
  flip(false, true);

  // Fit the close-up to the window's shape, and shrink the writing a little on
  // the few cards with more to say, so nothing is ever cut off.
  const info2 = front.querySelector('.tc-info');
  function layout() {
    const r = artBox.getBoundingClientRect();
    if (r.width && r.height) cu.place(cropFor(fig, partId, r.width / r.height));
    const key = `${partId}:${Math.round(r.width)}`;
    if (fitted.has(key)) { info2.style.fontSize = `${fitted.get(key)}px`; return; }
    let size = 15;
    info2.style.fontSize = `${size}px`;
    while (info2.scrollHeight > info2.clientHeight + 1 && size > 11) {
      size -= 0.5;
      info2.style.fontSize = `${size}px`;
    }
    if (r.width) fitted.set(key, size);
  }
  return { el, flip, layout, isFlipped: () => flipped };
}
