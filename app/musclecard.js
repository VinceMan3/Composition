// A muscle's trading card, like the ones from an old pack. The front has a
// close-up from the drawing, the card number, the name, what it does and a
// "Did you know?". Flip it over for the back: sets this week, the day it was
// last trained, and the lifts that train it.
//   muscleCard({ ctx, partId, view, onLift, onClose })

import { h } from './ui.js';
import { PARTS, partById, groupById, liftsFor, training } from './muscles.js';
import { allLifts, lastTime, niceDate, dateKey, tidy } from './log.js';
import { partBox } from './mapart.js';

const NS = 'http://www.w3.org/2000/svg';
const W = 560, H = 860; // the drawing's size, in its own units

// The close-up: the part in the middle with a little of the body around it.
function closeUp(view, svg, partId, aspect) {
  const box = svg && partBox(svg, partId);
  const art = document.createElementNS(NS, 'svg');
  art.setAttribute('class', 'tc-closeup');
  art.setAttribute('aria-hidden', 'true');
  art.setAttribute('preserveAspectRatio', 'xMidYMid slice');
  if (box) {
    let ch = Math.max(box.height / 0.62, box.width / 0.62 / aspect, 130);
    let cw = ch * aspect;
    if (cw > W) { cw = W; ch = cw / aspect; }
    if (ch > H) { ch = H; cw = ch * aspect; }
    const x = Math.min(Math.max(box.x + box.width / 2 - cw / 2, 0), W - cw);
    const y = Math.min(Math.max(box.y + box.height / 2 - ch / 2, 0), H - ch);
    art.setAttribute('viewBox', `${x.toFixed(1)} ${y.toFixed(1)} ${cw.toFixed(1)} ${ch.toFixed(1)}`);
  } else {
    art.setAttribute('viewBox', `0 0 ${W} ${H}`);
  }
  const use = document.createElementNS(NS, 'use');
  use.setAttribute('href', `#mmfig-${view}`);
  art.append(use);
  return art;
}

export function muscleCard({ ctx, partId, view, svg, onLift, onClose }) {
  const { words, store, sound } = ctx;
  const w = words.map;
  const data = store.get();
  const part = partById.get(partId);
  const group = groupById.get(part.group);
  const number = String(PARTS.indexOf(part) + 1).padStart(2, '0');
  const t = training(data).get(partId);
  const lifts = allLifts(data);
  const { main, help } = liftsFor(partId, lifts);
  const logged = new Set(lifts.filter(l => lastTime(data, l.id)).map(l => l.id));
  // Lifts you have done come first, main lifts before helpers.
  const loggedFirst = list => [...list].sort((a, b) => Number(logged.has(b.id)) - Number(logged.has(a.id)));
  const rows = [...loggedFirst(main).map(l => [l, 'main']), ...loggedFirst(help).map(l => [l, 'helps'])];

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
  const front = h('div', { class: 'tc-face tc-front' },
    h('div', { class: 'tc-frame' },
      h('div', { class: 'tc-art' },
        closeUp(view, svg, partId, 0.72),
        h('p', { class: 'tc-team' }, group.name),
      ),
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
        ? rows.map(([lift, role]) => h('button', {
          class: 'tc-lift',
          type: 'button',
          onClick(e) { e.stopPropagation(); onLift(lift.id, flipped); },
        },
          h('span', { class: 'tc-lift-name' }, lift.name),
          logged.has(lift.id) && h('span', { class: 'tc-lift-mine', 'aria-label': w.logged, title: w.logged }, '✓'),
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
  return { el, flip, isFlipped: () => flipped };
}
