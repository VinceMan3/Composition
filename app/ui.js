// Small helpers every page shares.

// Build an element: h('p', { class: 'quiet' }, 'Some text')
// Text is always added as text, so wording can never break the page.
export function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value == null || value === false) continue;
    if (key === 'class') el.className = value;
    else if (key.startsWith('on')) el.addEventListener(key.slice(2).toLowerCase(), value);
    else el.setAttribute(key, value === true ? '' : value);
  }
  for (const kid of kids.flat()) {
    if (kid == null || kid === false) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return el;
}

// Put pieces on a page, skipping any that are switched off:
//   put(el, heading, showList && list)
export function put(el, ...kids) {
  for (const kid of kids.flat()) {
    if (kid == null || kid === false) continue;
    el.append(kid);
  }
}

// "1 lift", "3 lifts". The pair comes from the wording file: ['lift', 'lifts']
export function count(n, pair) {
  return `${n} ${n === 1 ? pair[0] : pair[1]}`;
}

// A small line drawing: icon('M5 13l4 4L19 7')
export function icon(path, viewBox = '0 0 24 24') {
  const NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('viewBox', viewBox);
  svg.setAttribute('aria-hidden', 'true');
  const p = document.createElementNS(NS, 'path');
  p.setAttribute('d', path);
  svg.append(p);
  return svg;
}

// A drawing from the art folder. Decorative unless given a description.
export function art(file, className, width, height, alt = '') {
  return h('img', {
    class: className,
    src: `art/${file}`,
    width,
    height,
    alt,
    'aria-hidden': alt ? null : 'true',
    decoding: 'sync',
    draggable: 'false',
  });
}

// A sticker: the drawing plus a sheen that follows its outline.
export function sticker(file, className, width, height) {
  const shine = h('span', { class: 'sticker-shine' });
  shine.style.webkitMaskImage = `url(art/${file})`;
  shine.style.maskImage = `url(art/${file})`;
  return h('span', { class: `sticker ${className}` }, art(file, '', width, height), shine);
}

// For anything that can't be undone: the first tap changes the button's
// words and arms it, the second tap within a few seconds does the deed.
export function twoTap(button, confirmText, action, onArm) {
  const usual = button.textContent;
  let timer = 0;
  button.addEventListener('click', () => {
    if (button.dataset.armed === 'yes') {
      clearTimeout(timer);
      button.dataset.armed = '';
      button.textContent = usual;
      action();
      return;
    }
    if (onArm && onArm() === false) return;
    button.dataset.armed = 'yes';
    button.textContent = confirmText;
    timer = setTimeout(() => {
      button.dataset.armed = '';
      button.textContent = usual;
    }, 4000);
  });
  return button;
}

// "Wed · Nov 11"
export function shortDate(date = new Date()) {
  const day = date.toLocaleDateString('en-US', { weekday: 'short' });
  const rest = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  return `${day} · ${rest}`;
}

// The typewriter line, big heading and handwritten note at the top of a page.
export function pageHead(kicker, title, note) {
  return h('div', { class: 'head-block' },
    h('p', { class: 'kicker' }, kicker),
    h('h1', { class: 'heading' }, title),
    note && h('p', { class: 'hand' }, note),
  );
}

// The handwritten "coming soon" checklist.
export function comingList(label, items) {
  return h('div', { class: 'coming' },
    h('p', { class: 'label' }, label),
    h('ul', { class: 'todo' }, items.map(text => h('li', null, text))),
  );
}

let toastTimer = 0;
export function toast(message) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.hidden = true;
  el.textContent = message;
  void el.offsetWidth; // lets the pop-in replay
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 2400);
}
