// The muscle map: the graphite figure, front or back. Tap a muscle and it
// turns red with a sheen, and its trading card slides up from the bottom.
// The figure slides up out of the card's way so the muscle stays in sight.
// "Turn around" (or a swipe sideways) shows the other side; "List" shows
// every muscle as a list instead.

import { h, count } from '../ui.js';
import { GROUPS, PARTS, partById } from '../muscles.js';
import { loadFigure, pick } from '../mapart.js';
import { muscleCard } from '../musclecard.js';

const calm = window.matchMedia('(prefers-reduced-motion: reduce)');
const shows = (part, view) => part.view === 'both' || part.view === view;

export function render(el, ctx) {
  const { words, sound } = ctx;
  const w = words.map;
  // Where things were left, so coming back from a lift page finds the same card.
  const kept = ctx.state.map || {};
  const state = { view: kept.view === 'back' ? 'back' : 'front', part: kept.part || '', flipped: !!kept.flipped, list: !!kept.list };
  const save = () => { ctx.state.map = { ...state }; };
  const figures = {};
  let card = null;
  let gone = false;

  // ----- the header -----
  const heading = h('h1', { class: 'heading map-heading' });
  const turnButton = h('button', { class: 'btn btn-line btn-small map-turn', type: 'button', 'data-sound': 'none', onClick: () => turn() },
    h('span', { 'aria-hidden': 'true' }, '↻ '), w.turn);
  const listButton = h('button', { class: 'btn btn-line btn-small map-list-btn', type: 'button', 'aria-pressed': 'false', onClick: () => showList(!state.list) });

  // ----- the figure -----
  const turner = h('div', { class: 'map-turner' });
  const fig = h('div', { class: 'map-fig' }, turner);
  const hint = h('p', { class: 'map-hint' }, w.hint);
  const listEl = h('div', { class: 'map-listview', hidden: true });
  const dock = h('div', { class: 'map-dock', 'aria-live': 'polite' });
  const stage = h('div', { class: 'map-stage' }, fig, hint, listEl, dock);

  function drawHeader() {
    heading.textContent = state.list ? w.listTitle : state.view === 'front' ? w.front : w.back;
    turnButton.hidden = state.list;
    listButton.textContent = state.list ? w.figure : w.listShort;
    listButton.setAttribute('aria-label', state.list ? w.figure : w.list);
    listButton.setAttribute('aria-pressed', String(state.list));
  }

  function current() {
    return figures[state.view];
  }

  function showView(view) {
    state.view = view;
    for (const [v, svg] of Object.entries(figures)) svg.classList.toggle('is-shown', v === view);
    drawHeader();
  }

  // Slide the figure so the picked muscle sits in the space above the card.
  function pan() {
    const svg = current();
    stage.style.setProperty('--dock-h', `${card ? dock.offsetHeight : 0}px`);
    if (!svg || !state.part || !card || state.list) {
      fig.style.transform = '';
      return;
    }
    const shapes = [...svg.querySelectorAll(`.mm-muscle[data-part="${state.part}"]`)];
    if (!shapes.length) return;
    const stageBox = stage.getBoundingClientRect();
    // Measured without any slide, so the numbers don't depend on the last one.
    const was = fig.style.transform;
    fig.style.transition = 'none';
    fig.style.transform = '';
    const boxes = shapes.map(s => s.getBoundingClientRect());
    fig.style.transform = was;
    void fig.offsetWidth;
    fig.style.transition = '';
    const top = Math.min(...boxes.map(b => b.top)) - stageBox.top;
    const bottom = Math.max(...boxes.map(b => b.bottom)) - stageBox.top;
    const open = stageBox.height - dock.offsetHeight; // the space above the card
    stage.style.setProperty('--dock-h', `${dock.offsetHeight}px`);
    let dy = 0;
    if (bottom > open - 12) {
      dy = open / 2 - (top + bottom) / 2;
      dy = Math.max(dy, 12 - top); // keep the top of the muscle on the page
    }
    fig.style.transform = dy ? `translateY(${Math.round(dy)}px)` : '';
  }

  // ----- the card -----
  function openCard(partId, { flipped = false, quiet = false } = {}) {
    const part = partById.get(partId);
    if (!part) return;
    if (!state.list && !shows(part, state.view)) showView(part.view);
    state.part = partId;
    state.flipped = flipped;
    for (const svg of Object.values(figures)) pick(svg, partId);
    const view = shows(part, state.view) ? state.view : part.view;
    card = muscleCard({
      ctx,
      partId,
      view,
      svg: figures[view],
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
    const wasOpen = dock.classList.contains('is-open');
    dock.replaceChildren(card.el);
    dock.classList.add('is-open');
    hint.hidden = true;
    for (const b of listEl.querySelectorAll('.map-part')) b.setAttribute('aria-pressed', String(b.dataset.part === partId));
    if (!quiet) sound.play('deal');
    if (wasOpen && !calm.matches) card.el.animate([{ transform: 'translateY(14px) rotate(-1.5deg)', opacity: 0.4 }, { transform: 'none', opacity: 1 }], { duration: 180, easing: 'ease-out' });
    pan();
    save();
  }

  function closeCard() {
    state.part = '';
    state.flipped = false;
    card = null;
    for (const svg of Object.values(figures)) pick(svg, '');
    dock.classList.remove('is-open');
    hint.hidden = state.list;
    for (const b of listEl.querySelectorAll('.map-part')) b.setAttribute('aria-pressed', 'false');
    fig.style.transform = '';
    save();
  }

  // ----- turning around -----
  function turn() {
    if (!figures.front || !figures.back) return;
    const next = state.view === 'front' ? 'back' : 'front';
    sound.play('flick');
    const part = state.part && partById.get(state.part);
    const swap = () => {
      showView(next);
      // A muscle on both sides stays picked; one that is not on this side is put away.
      if (part && shows(part, next)) openCard(part.id, { flipped: card && card.isFlipped(), quiet: true });
      else if (part) closeCard();
      save();
    };
    if (calm.matches) return swap();
    const half = { duration: 110, easing: 'ease-in', fill: 'forwards' };
    const away = turner.animate([{ transform: 'scaleX(1)' }, { transform: 'scaleX(0)' }], half);
    away.finished.then(() => {
      if (gone) return;
      swap();
      away.cancel();
      turner.animate([{ transform: 'scaleX(0)' }, { transform: 'scaleX(1)' }], { ...half, easing: 'ease-out' });
    });
  }

  // ----- tapping and swiping the figure -----
  let start = null;
  let swiped = false;
  fig.addEventListener('pointerdown', e => { start = { x: e.clientX, y: e.clientY }; swiped = false; });
  fig.addEventListener('pointerup', e => {
    if (!start) return;
    const dx = e.clientX - start.x, dy = e.clientY - start.y;
    start = null;
    if (Math.abs(dx) > 50 && Math.abs(dy) < 45) { swiped = true; turn(); }
  });
  fig.addEventListener('click', e => {
    if (swiped) { swiped = false; return; }
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

  Promise.all([loadFigure('front'), loadFigure('back')]).then(([front, back]) => {
    if (gone) return;
    figures.front = front;
    figures.back = back;
    turner.append(front, back);
    showView(state.view);
    if (state.part) openCard(state.part, { flipped: state.flipped, quiet: true });
    else for (const svg of [front, back]) pick(svg, '');
    stage.classList.add('is-ready');
  }).catch(() => {
    if (!gone) hint.textContent = words.map.loadFailed;
  });

  return {
    cleanUp() { gone = true; },
    onAttached() { if (state.part) requestAnimationFrame(pan); },
  };
}
