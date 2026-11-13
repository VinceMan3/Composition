// The cover of the notebook: the name plate, today's verse, a small card that
// takes you to today's page, and the stickers, which you can drag around.

import { h, put, count, sticker, shortDate } from '../ui.js';
import { dateKey } from '../log.js';
import { onCover } from '../awards.js';
import { VERSES } from '../../content/verses.js';

// One verse a day, working down the list. It changes at midnight.
export function verseFor(date = new Date()) {
  const day = Math.floor(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / 86400000);
  return VERSES[day % VERSES.length];
}

// Where a sticker goes before anyone has moved it. Each spot is worked out
// from the layout: `gap` is the open stretch between the verse and the card.
// The first four hug the corners of the verse and the card; later ones fill in.
const SPOTS = [
  (W, gap, s) => ({ x: -0.02 * W, y: gap.top - s.h * 0.28 }),
  (W, gap, s) => ({ x: W * 0.33, y: gap.top + (gap.height - s.h) * 0.42 }),
  (W, gap, s) => ({ x: W * 0.02, y: gap.bottom - s.h * 0.9 }),
  (W, gap, s) => ({ x: W * 0.99 - s.w, y: gap.top - s.h * 0.2 }),
  (W, gap, s) => ({ x: W * 0.98 - s.w, y: gap.bottom - s.h * 0.95 }),
  (W, gap, s, label) => ({ x: W * 0.97 - s.w, y: label.bottom - s.h * 0.45 }),
  (W, gap, s, label) => ({ x: -0.07 * W, y: label.top - s.h * 0.38 }),
  (W, gap, s) => ({ x: W * 0.52 - s.w / 2, y: gap.bottom - s.h * 0.85 }),
  (W, gap, s) => ({ x: W * 0.16, y: gap.top + gap.height * 0.3 }),
  (W, gap, s) => ({ x: W * 0.62, y: gap.top + gap.height * 0.12 }),
  (W, gap, s) => ({ x: W * 0.44, y: gap.top + gap.height * 0.5 }),
];

export function render(el, ctx) {
  const { words, store, sound, toast } = ctx;
  const w = words.cover;
  const data = store.get();
  const verse = verseFor();

  // The card at the bottom follows what is going on today.
  let card;
  if (data.draft) {
    card = { label: w.goingLabel, title: data.draft.title, note: `${count(data.draft.lifts.length, words.count.lift)} ${w.goingNote}`, button: w.goingButton };
  } else {
    const last = data.pages[data.pages.length - 1];
    if (last && last.date === dateKey()) {
      card = { label: w.doneLabel, title: last.title, note: `${count(last.lifts.length, words.count.lift)} ${w.doneNote}`, button: w.doneButton };
    } else {
      card = { label: w.startLabel, title: w.startTitle, note: w.startNote, button: w.startButton };
    }
  }

  const label = h('div', { class: 'cover-label' },
    h('h1', { class: 'cover-name' }, words.appName),
    h('p', { class: 'cover-date' }, `${words.tagline} · ${shortDate()}`),
  );
  const verseCard = verse && h('figure', { class: 'verse' },
    h('p', { class: 'verse-label' }, w.verseLabel),
    h('blockquote', { class: `verse-text${verse.text.length > 170 ? ' is-long' : ''}` }, verse.text),
    h('figcaption', { class: 'verse-ref' }, verse.ref),
  );
  const gapEl = h('div', { class: 'sticker-gap' });
  const cardEl = h('div', { class: 'cover-card' },
    h('div', null,
      h('p', { class: 'label' }, card.label),
      h('h2', { class: 'cover-card-title' }, card.title),
      h('p', { class: 'hand' }, card.note),
    ),
    h('a', { class: 'btn btn-small', href: '#today' }, card.button),
  );

  // ----- the stickers -----
  const layer = h('div', { class: 'sticker-layer' });
  const fresh = ctx.state.newStickers || [];
  ctx.state.newStickers = [];
  const shown = onCover(data).map(def => {
    const node = sticker(def.art, '', 460, 460);
    node.setAttribute('role', 'img');
    node.setAttribute('aria-label', `${def.name} sticker`);
    node.querySelector('img').removeAttribute('width');
    node.querySelector('img').removeAttribute('height');
    return { def, node };
  });
  // Stack them in the order they were last touched.
  shown.sort((a, b) => ((data.stickers[a.def.id] || {}).z || 0) - ((data.stickers[b.def.id] || {}).z || 0));
  let topZ = 1;
  for (const s of shown) {
    s.node.style.zIndex = String(topZ++);
    layer.append(s.node);
  }

  function arrange() {
    const W = layer.clientWidth;
    const H = layer.clientHeight;
    if (!W) return;
    const top = n => n.offsetTop;
    const labelBox = { top: top(label), bottom: top(label) + label.offsetHeight };
    const gap = { top: top(gapEl), bottom: top(cardEl), height: top(cardEl) - top(gapEl) };
    let spot = 0;
    for (const { def, node } of shown) {
      const width = Math.min(def.size * W, def.size * 470);
      node.style.width = `${width}px`;
      const size = { w: width, h: node.offsetHeight || width };
      const saved = data.stickers[def.id];
      let pos;
      if (saved && typeof saved.x === 'number') {
        pos = { x: saved.x * W, y: saved.y * H };
      } else {
        pos = SPOTS[spot % SPOTS.length](W, gap, size, labelBox);
        spot += 1;
      }
      pos.x = Math.min(Math.max(pos.x, -size.w * 0.3), W - size.w * 0.7);
      pos.y = Math.min(Math.max(pos.y, 0), H - size.h * 0.6);
      node.style.left = `${pos.x}px`;
      node.style.top = `${pos.y}px`;
      node.style.setProperty('--turn', `${def.turn}deg`);
    }
  }

  // Dragging: press, move, let go. A press without a move is a tap.
  function makeMovable({ def, node }) {
    let grip = null;
    node.addEventListener('pointerdown', e => {
      if (e.button) return;
      node.setPointerCapture(e.pointerId);
      grip = { x: e.clientX, y: e.clientY, left: node.offsetLeft, top: node.offsetTop, moved: false };
      node.style.zIndex = String(topZ++); // on top while held, and after
    });
    node.addEventListener('pointermove', e => {
      if (!grip) return;
      const dx = e.clientX - grip.x;
      const dy = e.clientY - grip.y;
      if (!grip.moved && Math.hypot(dx, dy) < 6) return;
      grip.moved = true;
      node.classList.add('is-held');
      const W = layer.clientWidth;
      const H = layer.clientHeight;
      const x = Math.min(Math.max(grip.left + dx, -node.offsetWidth * 0.3), W - node.offsetWidth * 0.7);
      const y = Math.min(Math.max(grip.top + dy, 0), H - node.offsetHeight * 0.6);
      // Slide it as its own layer while held (no repainting, so phones leave
      // no smears behind); its real position is set once it is let go.
      grip.x2 = x;
      grip.y2 = y;
      node.style.translate = `${x - grip.left}px ${y - grip.top}px`;
    });
    const drop = () => {
      if (!grip) return;
      const moved = grip.moved;
      if (moved) {
        node.style.left = `${grip.x2}px`;
        node.style.top = `${grip.y2}px`;
      }
      node.style.translate = '';
      grip = null;
      node.classList.remove('is-held');
      const top = Math.max(0, ...Object.values(store.get().stickers).map(s => s.z || 0)) + 1;
      if (moved) {
        store.update(d => {
          d.stickers[def.id] = { ...d.stickers[def.id], x: node.offsetLeft / layer.clientWidth, y: node.offsetTop / layer.clientHeight, z: top };
        });
        sound.play('tap');
      } else {
        node.classList.remove('is-wiggling');
        void node.offsetWidth;
        node.classList.add('is-wiggling');
        sound.play('tap');
        toast(def.name);
      }
    };
    node.addEventListener('pointerup', drop);
    node.addEventListener('pointercancel', drop);
  }
  shown.forEach(makeMovable);

  put(el, label, verseCard, gapEl, cardEl, layer);

  const onResize = () => arrange();
  window.addEventListener('resize', onResize);
  let slap = 0;
  return {
    onAttached() {
      arrange();
      // Art that had not loaded yet has no height; arrange again when it does.
      for (const { node } of shown) {
        const img = node.querySelector('img');
        if (!img.complete) img.addEventListener('load', arrange, { once: true });
      }
      // A sticker earned since the cover was last open gets slapped on.
      const news = shown.filter(s => fresh.includes(s.def.id));
      if (news.length) {
        for (const s of news) s.node.style.visibility = 'hidden';
        slap = setTimeout(() => {
          for (const s of news) {
            s.node.style.visibility = '';
            s.node.classList.add('is-slapped');
          }
          sound.play('stamp');
        }, 420);
      }
    },
    cleanUp() {
      window.removeEventListener('resize', onResize);
      clearTimeout(slap);
    },
  };
}
