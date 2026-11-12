// Turning pages. The address ends in a page name (#cover, #today, ...); when
// it changes, the old page curls up over the rings (going forward) or the new
// page falls back down (going backward).

import { h } from './ui.js';
import { makeSheet } from './flip.js';

// Every page: which tab it belongs to, and where it sits in the notebook.
// A bigger number is further in, so going to it flips forward.
export const ROUTES = {
  cover: { tab: 'cover', at: 0 },
  today: { tab: 'today', at: 10 },
  add: { tab: 'today', at: 11 },
  filed: { tab: 'today', at: 12 },
  notebook: { tab: 'notebook', at: 20 },
  stats: { tab: 'stats', at: 30 },
  more: { tab: 'more', at: 40 },
  stickers: { tab: 'more', at: 41 },
};

const calm = window.matchMedia('(prefers-reduced-motion: reduce)');

export function startRouter({ stack, render, resolve, onShow, onFlip }) {
  let current = null;
  let currentEl = null;
  let finishFlip = null;

  function nameFromAddress() {
    const asked = location.hash.replace('#', '');
    let name = ROUTES[asked] ? asked : 'cover';
    const better = resolve ? resolve(name) : name;
    if (better !== name) {
      name = better;
      history.replaceState(null, '', `#${name}`);
    }
    return name;
  }

  function build(name) {
    const inner = h('div', { class: 'page-inner' });
    const el = h('section', { class: `page page-${name}`, 'data-page': name }, inner);
    // A page may hand back a clean-up function (to stop a timer, say), or
    // { cleanUp, onAttached } when it also needs a moment once it is on screen.
    const made = render(name, inner);
    el.cleanUp = typeof made === 'function' ? made : (made && made.cleanUp) || null;
    el.onAttached = (made && made.onAttached) || null;
    return el;
  }

  function discard(el) {
    if (el.cleanUp) el.cleanUp();
    el.remove();
  }

  function show() {
    const name = nameFromAddress();
    if (name === current) return;
    if (finishFlip) finishFlip(); // a flip still in the air lands at once

    const prev = currentEl;
    const forward = current ? ROUTES[name].at > ROUTES[current].at : true;
    const next = build(name);
    current = name;
    currentEl = next;
    onShow(name, ROUTES[name].tab);

    if (!prev) {
      stack.append(next);
      if (next.onAttached) next.onAttached();
      return;
    }

    if (calm.matches) {
      discard(prev);
      next.classList.add('is-fading-in');
      stack.append(next);
      if (next.onAttached) next.onAttached();
      return;
    }

    // Forward: a copy of the old page curls away, showing the new one beneath.
    // Backward: a copy of the new page falls onto the old one.
    stack.append(next);
    if (next.onAttached) next.onAttached();
    const shade = h('div', { class: `shade ${forward ? 'is-clearing' : 'is-falling'}` });
    const sheet = makeSheet(forward ? prev : next, forward ? 'up' : 'down');
    stack.append(shade, sheet.el);
    sheet.settle();
    if (forward) discard(prev);
    else next.classList.add('is-waiting');
    onFlip(forward);

    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      sheet.el.remove();
      shade.remove();
      if (!forward) {
        next.classList.remove('is-waiting');
        discard(prev);
      }
      if (finishFlip === finish) finishFlip = null;
    };
    sheet.top.addEventListener('animationend', e => { if (e.target === sheet.top) finish(); });
    const timer = setTimeout(finish, 800); // in case the animation never reports back
    finishFlip = finish;
  }

  // Redraw the page that is open, without a flip.
  function refresh() {
    if (!currentEl) return;
    if (finishFlip) finishFlip();
    const fresh = build(current);
    const scroll = currentEl.scrollTop;
    const old = currentEl;
    old.replaceWith(fresh);
    if (old.cleanUp) old.cleanUp();
    currentEl = fresh;
    fresh.scrollTop = scroll;
    if (fresh.onAttached) fresh.onAttached();
  }

  window.addEventListener('hashchange', show);
  show();

  return { refresh, current: () => current, page: () => currentEl };
}
