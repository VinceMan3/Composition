// Where the app starts. This file wires the pieces together:
// wording and colors (content/), saving (store.js), sounds (sound.js),
// page turning (router.js), the rest timer (rest.js) and the pages (pages/).

import { WORDS } from '../content/wording.js';
import * as store from './store.js';
import * as sound from './sound.js';
import * as rest from './rest.js';
import { collect } from './awards.js';
import { toast, shortDate } from './ui.js';
import { startRouter } from './router.js';
import * as cover from './pages/cover.js';
import * as today from './pages/today.js';
import * as add from './pages/add.js';
import * as filed from './pages/filed.js';
import * as notebook from './pages/notebook.js';
import * as stats from './pages/stats.js';
import * as calc from './pages/calc.js';
import * as more from './pages/more.js';
import * as stickers from './pages/stickers.js';
import * as page from './pages/page.js';
import * as library from './pages/library.js';
import * as lift from './pages/lift.js';

const PAGES = { cover, today, add, filed, notebook, stats, calc, more, stickers, page, library, lift };

const app = document.getElementById('app');
const stack = document.getElementById('stack');

// Words in the frame around the pages.
document.getElementById('wordmark').textContent = WORDS.appName;
document.getElementById('strip-note').textContent = shortDate();
for (const tab of document.querySelectorAll('.tab')) {
  tab.querySelector('[data-tab-label]').textContent = WORDS.tabs[tab.dataset.tab];
}

sound.setMuted(!store.get().settings.sound);

// What every page is handed when it draws itself.
const ctx = {
  words: WORDS,
  store,
  sound,
  rest,
  toast,
  state: {}, // short-lived notes passed from one page to the next
  go(name) { location.hash = name; },
  refresh() { router.refresh(); },
};

rest.initRest(document.getElementById('rest'), ctx);

// Anything earned that was never handed out (say, after a restore) is
// handed out now, and slapped on the cover the next time it opens.
store.update(d => { ctx.state.newStickers = collect(d); });

const router = startRouter({
  stack,
  render: (name, el) => PAGES[name].render(el, ctx),
  // Some pages only make sense in the right moment; otherwise send people on.
  resolve(name) {
    const data = store.get();
    if (name === 'add' && !data.draft) return 'today';
    if (name === 'filed' && !data.pages.length) return 'today';
    if (name === 'page' && !data.pages.some(p => p.id === ctx.state.openPage)) return 'notebook';
    if (name === 'lift' && !ctx.state.openLift) return 'library';
    return name;
  },
  onShow(name, tabName) {
    app.dataset.page = name;
    document.title = name === 'cover' ? WORDS.appName : `${WORDS.tabs[tabName]} · ${WORDS.appName}`;
    for (const tab of document.querySelectorAll('.tab')) {
      if (tab.dataset.tab === tabName) tab.setAttribute('aria-current', 'page');
      else tab.removeAttribute('aria-current');
    }
  },
  onFlip(forward, quick) { sound.play(quick ? 'flick' : 'flip'); },
});

// Phones only allow sound after a touch.
document.addEventListener('pointerdown', sound.unlock, { passive: true });
document.addEventListener('keydown', sound.unlock);

// Every button gets a light tap sound, unless it makes its own sound
// (data-sound="none") or it is about to turn the page.
document.addEventListener('click', event => {
  const target = event.target.closest('button, a');
  if (!target || target.dataset.sound === 'none') return;
  const href = target.getAttribute('href');
  if (href && href.startsWith('#') && href.slice(1) !== router.current()) return;
  sound.play('tap');
});
