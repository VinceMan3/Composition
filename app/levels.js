// The strip that shows a lift's strength level: the level's name, a bar
// filling toward the next one, and how many pounds are left to get there.
// Shared by the Stats page and the calculator.

import { h } from './ui.js';
import { LEVELS } from './strength.js';

export function levelStrip(lv, w) {
  if (!lv) return null;
  return h('div', { class: 'level' },
    h('div', { class: 'level-row' },
      h('span', { class: `level-name level-${lv.index}` }, lv.name),
      h('span', { class: 'level-next' }, lv.next ? `${lv.toGo} lb ${w.toNext} ${lv.next}` : w.top),
    ),
    h('div', { class: 'level-track', 'aria-hidden': 'true' },
      LEVELS.slice(1).map((_, i) => h('span', { class: `level-step${i < lv.index ? ' is-full' : ''}` },
        i === lv.index ? h('span', { class: 'level-fill', style: `width:${Math.round(lv.share * 100)}%` }) : null)),
    ),
  );
}
