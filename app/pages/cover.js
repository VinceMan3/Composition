// The cover of the notebook: the name plate, today's verse, the stickers, and
// a card that takes you to today's page.

import { h, put, count, sticker, shortDate } from '../ui.js';
import { dateKey } from '../log.js';
import { VERSES } from '../../content/verses.js';

// One verse a day, working down the list. It changes at midnight.
export function verseFor(date = new Date()) {
  const day = Math.floor(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / 86400000);
  return VERSES[day % VERSES.length];
}

export function render(el, { words, store }) {
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

  put(el,
    h('div', { class: 'cover-label' },
      h('h1', { class: 'cover-name' }, words.appName),
      h('p', { class: 'cover-date' }, `${words.tagline} · ${shortDate()}`),
    ),
    verse && h('figure', { class: 'verse', style: 'margin-inline:0;margin-bottom:0' },
      h('p', { class: 'verse-label' }, w.verseLabel),
      h('blockquote', { class: `verse-text${verse.text.length > 170 ? ' is-long' : ''}`, style: 'margin:0' }, verse.text),
      h('figcaption', { class: 'verse-ref' }, verse.ref),
    ),
    h('div', { class: 'stickers', 'aria-hidden': 'true' },
      sticker('sticker-gloves.png', 'sticker-gloves', 460, 429),
      sticker('sticker-pose.png', 'sticker-pose', 460, 460),
      sticker('sticker-barbell.png', 'sticker-barbell', 520, 290),
      sticker('sticker-ribbons.png', 'sticker-ribbons', 460, 453),
    ),
    h('div', { class: 'cover-card' },
      h('p', { class: 'label' }, card.label),
      h('h2', { class: 'cover-card-title' }, card.title),
      h('p', { class: 'hand' }, card.note),
      h('a', { class: 'btn', href: '#today' }, card.button),
    ),
  );
}
