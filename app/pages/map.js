// The muscle map: the graphite figure, front or back. Tap a muscle and it
// turns red with a sheen, and its trading card slides up from the bottom.
// The figure slides up out of the card's way so the muscle stays in sight.
// Pinch or double-tap to zoom in on small muscles, drag to look around.
// "Turn around" (or a swipe sideways) shows the other side; "List" shows
// every muscle as a list instead.

import { h, count } from '../ui.js';
import { GROUPS, PARTS, partById, groupById, partsFor, training } from '../muscles.js';
import { allLifts, lastTime } from '../log.js';
import { loadFigure, W, H } from '../mapart.js';
import { muscleCard } from '../musclecard.js';

const calm = window.matchMedia('(prefers-reduced-motion: reduce)');
const shows = (part, view) => part.view === 'both' || part.view === view;
const MAX_ZOOM = 4;

export function render(el, ctx) {
  const { words, sound, store } = ctx;
  const w = words.map;
  // Where things were left, so coming back from a lift page finds the same card.
  const kept = ctx.state.map || {};
  const state = { view: kept.view === 'back' ? 'back' : 'front', part: kept.part || '', flipped: !!kept.flipped, list: !!kept.list };
  const save = () => { ctx.state.map = { ...state }; };
  const figures = {};
  let card = null;
  let gone = false;

  // Worked out once for this visit: sets per part, and the lifts per part.
  const data = store.get();
  const lifts = allLifts(data);
  const mine = new Set(lifts.filter(l => lastTime(data, l.id)).map(l => l.id));
  const byPart = new Map(PARTS.map(p => [p.id, { main: [], help: [] }]));
  for (const lift of lifts) {
    const { works, helps } = partsFor(lift);
    for (const id of works) byPart.get(id).main.push(lift);
    for (const id of helps) byPart.get(id).help.push(lift);
  }
  const yoursFirst = list => [...list].sort((a, b) => Number(mine.has(b.id)) - Number(mine.has(a.id)));
  const info = {
    train: training(data),
    lifts: id => [
      ...yoursFirst(byPart.get(id).main).map(lift => ({ lift, role: 'main', mine: mine.has(lift.id) })),
      ...yoursFirst(byPart.get(id).help).map(lift => ({ lift, role: 'helps', mine: mine.has(lift.id) })),
    ],
  };

  // ----- the header -----
  const heading = h('h1', { class: 'heading map-heading' });
  const turnButton = h('button', { class: 'btn btn-line btn-small map-turn', type: 'button', 'data-sound': 'none', onClick: () => turn() },
    h('span', { 'aria-hidden': 'true' }, '↻ '), w.turn);
  const listButton = h('button', { class: 'btn btn-line btn-small map-list-btn', type: 'button', 'aria-pressed': 'false', onClick: () => showList(!state.list) });

  // ----- the figure -----
  const turner = h('div', { class: 'map-turner' });
  const fig = h('div', { class: 'map-fig' }, turner);
  const hint = h('p', { class: 'map-hint' }, w.hint);
  const zoomOut = h('button', { class: 'map-zoomout', type: 'button', hidden: true, 'aria-label': w.zoomOut, onClick: () => zoomTo(1) },
    h('span', { 'aria-hidden': 'true' }, '−'));
  const listEl = h('div', { class: 'map-listview', hidden: true });
  const tabs = h('div', { class: 'map-tabs', role: 'group' });
  const dock = h('div', { class: 'map-dock', 'aria-live': 'polite' });
  const stage = h('div', { class: 'map-stage' }, fig, hint, zoomOut, listEl, dock);

  function drawHeader() {
    heading.textContent = state.list ? w.listTitle : state.view === 'front' ? w.front : w.back;
    turnButton.hidden = state.list;
    listButton.textContent = state.list ? w.figure : w.listShort;
    listButton.setAttribute('aria-label', state.list ? w.figure : w.list);
    listButton.setAttribute('aria-pressed', String(state.list));
  }

  function showView(view) {
    state.view = view;
    for (const [v, f] of Object.entries(figures)) f.el.classList.toggle('is-shown', v === view);
    drawHeader();
  }

  // ----- where the figure sits: its size, the zoom, and the slide for the card -----
  const zoom = { s: 1, x: 0, y: 0 }; // scale, and shift in page pixels
  let lift = 0;                       // how far the figure is slid up for the card
  let box = { left: 0, top: 0, width: 0, height: 0 };

  // Sizes from the layout, not the screen: a page turning in is drawn
  // squeezed for a moment, and that must not shrink or stretch the figure.
  const stageSize = () => ({ width: stage.clientWidth, height: stage.clientHeight });

  function size() {
    const r = stageSize();
    if (!r.height) return;
    let hgt = r.height - 30, wid = hgt * W / H;
    if (wid > r.width) { wid = r.width; hgt = wid * H / W; }
    box = { left: (r.width - wid) / 2, top: 2, width: wid, height: hgt };
    for (const f of Object.values(figures)) {
      Object.assign(f.el.style, { left: `${box.left}px`, top: `${box.top}px`, width: `${wid}px`, height: `${hgt}px` });
    }
  }

  // Keep the zoomed figure from being dragged off the page.
  function clamp() {
    const r = stageSize();
    if (zoom.s <= 1) { zoom.s = 1; zoom.x = 0; zoom.y = 0; return; }
    const minX = r.width - (box.left + box.width) * zoom.s, maxX = -box.left * zoom.s;
    const minY = r.height - 60 - (box.top + box.height) * zoom.s, maxY = 40 - box.top * zoom.s;
    zoom.x = Math.min(Math.max(zoom.x, Math.min(minX, maxX)), Math.max(minX, maxX));
    zoom.y = Math.min(Math.max(zoom.y, Math.min(minY, maxY)), Math.max(minY, maxY));
  }

  function place() {
    fig.style.transform = `translate(${zoom.x}px, ${zoom.y + lift}px) scale(${zoom.s})`;
    zoomOut.hidden = state.list || zoom.s <= 1.01;
    stage.classList.toggle('is-zoomed', zoom.s > 1.01);
  }

  // Zoom so that the stage point (px, py) stays put.
  function zoomTo(s, px, py) {
    const r = stageSize();
    if (px === undefined) { px = r.width / 2; py = r.height / 2; }
    const next = Math.min(Math.max(s, 1), MAX_ZOOM);
    zoom.x = px - (px - zoom.x) * (next / zoom.s);
    zoom.y = py - (py - (zoom.y + lift)) * (next / zoom.s) - lift;
    zoom.s = next;
    clamp();
    place();
    if (card) pan();
  }

  // Slide the figure so the picked muscle sits in the space above the card.
  function pan() {
    stage.style.setProperty('--dock-h', `${card ? dock.offsetHeight : 0}px`);
    const f = figures[state.view];
    if (!f || !state.part || !card || state.list) {
      if (lift) { lift = 0; place(); }
      return;
    }
    const shapes = f.shapes(state.part);
    if (!shapes.length) return;
    const s = stage.getBoundingClientRect();
    const rects = shapes.map(e => e.getBoundingClientRect());
    // Where the muscle would be with no slide.
    const top = Math.min(...rects.map(b => b.top)) - s.top - lift;
    const bottom = Math.max(...rects.map(b => b.bottom)) - s.top - lift;
    const open = s.height - dock.offsetHeight; // the space above the card
    let dy = 0;
    if (bottom > open - 12 || top < 8) {
      dy = open / 2 - (top + bottom) / 2;
      dy = Math.max(dy, 12 - top);
    }
    lift = Math.round(dy);
    // Zoomed in, the muscle can also be off to one side: bring it into view.
    if (zoom.s > 1.01) {
      const left = Math.min(...rects.map(b => b.left)) - s.left;
      const right = Math.max(...rects.map(b => b.right)) - s.left;
      if (left < 8 || right > s.width - 8) {
        zoom.x += s.width / 2 - (left + right) / 2;
        clamp();
      }
    }
    place();
  }

  // ----- the card -----
  function drawTabs(part) {
    const parts = PARTS.filter(p => p.group === part.group);
    tabs.hidden = parts.length < 2;
    tabs.setAttribute('aria-label', w.partsOf.replace('{group}', groupById.get(part.group).name));
    tabs.replaceChildren(...(parts.length < 2 ? [] : parts.map(p => h('button', {
      class: 'map-tab',
      type: 'button',
      'data-part': p.id,
      'aria-pressed': String(p.id === part.id),
      onClick(e) { e.stopPropagation(); if (p.id !== state.part) openCard(p.id, { flipped: !!card && card.isFlipped() }); },
    }, p.name))));
  }

  // The muscle turns red at once; the card is built a frame later, so the
  // red shows the moment your finger lifts.
  let pending = 0;
  function openCard(partId, { flipped = false, quiet = false, now = false } = {}) {
    const part = partById.get(partId);
    if (!part) return;
    if (!state.list && !shows(part, state.view)) showView(part.view);
    state.part = partId;
    state.flipped = flipped;
    for (const f of Object.values(figures)) f.pick(partId);
    if (!quiet) sound.play('deal');
    for (const b of listEl.querySelectorAll('.map-part')) b.setAttribute('aria-pressed', String(b.dataset.part === partId));
    save();
    const ticket = ++pending;
    const build = () => { if (ticket === pending && !gone && state.part === partId) dealCard(part, flipped); };
    if (now || calm.matches) build();
    else requestAnimationFrame(() => setTimeout(build, 0));
  }

  function dealCard(part, flipped) {
    const partId = part.id;
    const view = shows(part, state.view) ? state.view : part.view;
    const wasOpen = dock.classList.contains('is-open');
    card = muscleCard({
      ctx,
      partId,
      fig: figures[view],
      info,
      onLift(liftId, isFlipped) {
        state.flipped = isFlipped;
        save();
        ctx.state.openLift = liftId;
        ctx.state.liftFrom = 'map';
        ctx.go('lift');
      },
      onClose: closeCard,
    });
    if (flipped) card.flip(true, true);
    drawTabs(part);
    dock.replaceChildren(tabs, card.el);
    dock.classList.add('is-open');
    card.layout();
    hint.hidden = true;
    if (wasOpen && !calm.matches) card.el.animate([{ transform: 'translateY(10px) rotate(-1.2deg)', opacity: 0.5 }, { transform: 'none', opacity: 1 }], { duration: 150, easing: 'ease-out' });
    pan();
    save();
  }

  function closeCard() {
    pending++;
    state.part = '';
    state.flipped = false;
    card = null;
    for (const f of Object.values(figures)) f.pick('');
    dock.classList.remove('is-open');
    hint.hidden = state.list;
    for (const b of listEl.querySelectorAll('.map-part')) b.setAttribute('aria-pressed', 'false');
    lift = 0;
    place();
    stage.style.setProperty('--dock-h', '0px');
    save();
  }

  // ----- turning around -----
  function turn() {
    if (!figures.front || !figures.back) return;
    const next = state.view === 'front' ? 'back' : 'front';
    sound.play('flick');
    const part = state.part && partById.get(state.part);
    const swap = () => {
      zoom.s = 1; zoom.x = 0; zoom.y = 0; lift = 0;
      place();
      showView(next);
      // A muscle on both sides stays picked; one that is not on this side is put away.
      if (part && shows(part, next)) openCard(part.id, { flipped: !!card && card.isFlipped(), quiet: true, now: true });
      else if (part) closeCard();
      save();
    };
    if (calm.matches) return swap();
    const half = { duration: 100, easing: 'ease-in', fill: 'forwards' };
    const away = turner.animate([{ transform: 'scaleX(1)' }, { transform: 'scaleX(0)' }], half);
    away.finished.then(() => {
      if (gone) return;
      swap();
      away.cancel();
      turner.animate([{ transform: 'scaleX(0)' }, { transform: 'scaleX(1)' }], { ...half, easing: 'ease-out' });
    });
  }

  // ----- touch: tap, double-tap, pinch, drag, swipe -----
  const pointers = new Map();
  let gesture = null;   // what the fingers are doing now
  let moved = false;    // a drag, pinch or swipe happened, so this is not a tap
  let lastTap = null;   // for double-tap

  const at = e => {
    const r = stage.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  };

  fig.addEventListener('pointerdown', e => {
    pointers.set(e.pointerId, at(e));
    if (pointers.size === 1) {
      moved = false;
      gesture = { kind: 'one', start: at(e), zx: zoom.x, zy: zoom.y };
    } else if (pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      gesture = { kind: 'pinch', d: Math.hypot(a.x - b.x, a.y - b.y) || 1, mid: { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }, s: zoom.s, zx: zoom.x, zy: zoom.y + lift };
      lift = 0;
      moved = true;
      stage.classList.add('is-gesturing');
    }
  });
  fig.addEventListener('pointermove', e => {
    if (!pointers.has(e.pointerId) || !gesture) return;
    pointers.set(e.pointerId, at(e));
    if (gesture.kind === 'pinch' && pointers.size >= 2) {
      const [a, b] = [...pointers.values()];
      const d = Math.hypot(a.x - b.x, a.y - b.y);
      const mid = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
      const s = Math.min(Math.max(gesture.s * d / gesture.d, 1), MAX_ZOOM);
      zoom.x = mid.x - (gesture.mid.x - gesture.zx) * (s / gesture.s);
      zoom.y = mid.y - (gesture.mid.y - gesture.zy) * (s / gesture.s);
      zoom.s = s;
      clamp();
      place();
    } else if (gesture.kind === 'one' && zoom.s > 1.01) {
      const p = at(e);
      const dx = p.x - gesture.start.x, dy = p.y - gesture.start.y;
      if (!moved && Math.hypot(dx, dy) < 6) return;
      moved = true;
      stage.classList.add('is-gesturing');
      zoom.x = gesture.zx + dx;
      zoom.y = gesture.zy + dy;
      clamp();
      place();
    }
  });
  fig.addEventListener('pointerup', e => {
    if (!pointers.has(e.pointerId)) return;
    const p = at(e);
    pointers.delete(e.pointerId);
    if (pointers.size) return;
    stage.classList.remove('is-gesturing');
    const g = gesture;
    gesture = null;
    if (!g || g.kind !== 'one' || moved) { if (card) pan(); return; }
    const dx = p.x - g.start.x, dy = p.y - g.start.y;
    // A swipe sideways turns around (when not zoomed in).
    if (zoom.s <= 1.01 && Math.abs(dx) > 50 && Math.abs(dy) < 45) { moved = true; turn(); return; }
    if (Math.hypot(dx, dy) > 10) { moved = true; return; }
    // A second tap on the same spot zooms in there, or back out. The first
    // tap has already picked the muscle, so nothing waits on the double tap.
    const now = performance.now();
    if (lastTap && now - lastTap.t < 320 && Math.hypot(p.x - lastTap.x, p.y - lastTap.y) < 30) {
      lastTap = null;
      moved = true;
      if (zoom.s > 1.01) zoomTo(1);
      else zoomTo(2.6, p.x, p.y);
      return;
    }
    lastTap = { t: now, x: p.x, y: p.y };
  });
  // iPhone's own pinch would zoom the whole page; the map handles pinches itself.
  for (const name of ['gesturestart', 'gesturechange']) stage.addEventListener(name, e => e.preventDefault());
  fig.addEventListener('pointercancel', e => {
    pointers.delete(e.pointerId);
    if (!pointers.size) { gesture = null; stage.classList.remove('is-gesturing'); }
  });

  fig.addEventListener('click', e => {
    if (moved) { moved = false; return; }
    const shape = e.target.closest && e.target.closest('.mm-muscle');
    if (shape) {
      if (shape.dataset.part !== state.part) openCard(shape.dataset.part);
    } else if (state.part) {
      closeCard();
    }
  });

  // ----- the list -----
  listEl.append(h('p', { class: 'map-list-hint' }, w.listHint), ...GROUPS.map(g => {
    const parts = PARTS.filter(p => p.group === g.id);
    return h('section', { class: 'map-group' },
      h('h2', { class: 'label map-group-name' }, g.name, parts.length > 1 && h('span', { class: 'map-group-count' }, ` · ${count(parts.length, w.parts)}`)),
      h('div', { class: 'map-parts' }, parts.map(p => h('button', {
        class: 'chip map-part',
        type: 'button',
        'data-sound': 'none',
        'data-part': p.id,
        'aria-pressed': 'false',
        onClick() { openCard(p.id); },
      }, p.name))),
    );
  }));

  function showList(on) {
    state.list = on;
    // Back to the figure: turn to the side the picked muscle is on.
    const part = state.part && partById.get(state.part);
    if (!on && part && !shows(part, state.view)) showView(part.view);
    listEl.hidden = !on;
    fig.classList.toggle('is-away', on);
    hint.hidden = on || !!state.part;
    drawHeader();
    place();
    if (state.part) pan();
    save();
  }

  // ----- putting it together -----
  el.append(
    h('div', { class: 'map-head' },
      h('p', { class: 'kicker map-kicker' }, w.kicker),
      heading,
      h('div', { class: 'map-buttons' }, turnButton, listButton),
    ),
    stage,
  );
  drawHeader();
  if (state.list) showList(true);

  const resize = new ResizeObserver(() => { size(); clamp(); place(); if (card) pan(); });

  Promise.all([loadFigure('front'), loadFigure('back')]).then(([front, back]) => {
    if (gone) return;
    figures.front = front;
    figures.back = back;
    turner.append(front.el, back.el);
    size();
    showView(state.view);
    if (state.part) openCard(state.part, { flipped: state.flipped, quiet: true, now: true });
    else for (const f of [front, back]) f.pick('');
    stage.classList.add('is-ready');
    // Deal one card out of sight once, so the first real tap is quick too.
    if (!state.part) setTimeout(() => {
      if (gone || card) return;
      const warm = muscleCard({ ctx, partId: 'chest-middle', fig: front, info, onLift() {}, onClose() {} });
      const spare = h('div', { class: 'map-dock map-warm', 'aria-hidden': 'true' }, warm.el);
      stage.append(spare);
      warm.layout();
      spare.remove();
    }, 250);
    resize.observe(stage);
  }).catch(() => {
    if (!gone) hint.textContent = w.loadFailed;
  });

  return {
    cleanUp() { gone = true; resize.disconnect(); },
    onAttached() { size(); if (card) requestAnimationFrame(() => { card.layout(); pan(); }); },
  };
}
