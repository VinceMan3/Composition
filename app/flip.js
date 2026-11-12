// The bending page. To make a page curl like thin paper instead of swinging
// like a board, we cut a copy of it into strips and hinge each strip to the
// one above. The top strip lifts; every hinge below it bends a little more.
// The timing lives in styles/motion.css.

import { h } from './ui.js';

const STRIPS = 7;

export function makeSheet(page, direction) {
  const height = page.clientHeight;
  const scrolled = page.scrollTop;
  const stripHeight = Math.ceil(height / STRIPS);
  const sheet = h('div', { class: `sheet sheet-${direction}`, 'aria-hidden': 'true' });
  sheet.inert = true;

  const copies = [];
  let parent = sheet;
  for (let i = 0; i < STRIPS; i++) {
    const copy = page.cloneNode(true);
    copy.className = `page page-${page.dataset.page} sheet-copy`;
    copy.style.top = `${-i * stripHeight}px`;
    copy.style.height = `${height}px`;
    copies.push(copy);

    const box = `height:${stripHeight + 1}px`;
    const strip = h('div', {
      class: i ? 'sheet-strip sheet-hinge' : 'sheet-strip',
      style: `top:${i ? stripHeight : 0}px; --k:${(i / (STRIPS - 1)).toFixed(2)}`,
    },
      h('div', { class: 'sheet-face', style: box }, copy),
      h('div', { class: 'sheet-back', style: box }),
    );
    parent.append(strip);
    parent = strip;
  }

  return {
    el: sheet,
    top: sheet.firstChild,
    // Call once the sheet is on the page, so each copy shows the right part.
    settle() { for (const copy of copies) copy.scrollTop = scrolled; },
  };
}
