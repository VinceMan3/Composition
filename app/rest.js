// The rest timer. It lives in the strip above the tabs, so it keeps counting
// while you flip to other pages. It only starts when you press Rest.

import { h } from './ui.js';

let bar, timeEl, fillEl, labelEl, controls;
let sound, words;
let endsAt = 0;
let total = 0;
let ticker = 0;
let hideTimer = 0;
let wakeLock = null;

export function clock(seconds) {
  const s = Math.max(0, Math.ceil(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

export function initRest(el, ctx) {
  bar = el;
  sound = ctx.sound;
  words = ctx.words.rest;
  fillEl = h('div', { class: 'rest-fill' });
  labelEl = h('span', { class: 'rest-label' }, words.label);
  timeEl = h('span', { class: 'rest-time', role: 'timer', 'aria-live': 'off' }, '0:00');
  controls = h('div', { class: 'rest-controls' },
    h('button', { type: 'button', 'aria-label': 'Fifteen seconds less', onClick: () => nudge(-15) }, words.less),
    h('button', { type: 'button', 'aria-label': 'Fifteen seconds more', onClick: () => nudge(15) }, words.more),
    h('button', { type: 'button', class: 'rest-stop', onClick: stop }, words.stop),
  );
  bar.append(fillEl, labelEl, timeEl, controls);
}

export function isResting() {
  return endsAt > 0;
}

export function start(seconds) {
  clearTimeout(hideTimer);
  total = seconds;
  endsAt = Date.now() + seconds * 1000;
  bar.hidden = false;
  bar.classList.remove('is-over');
  labelEl.textContent = words.label;
  controls.hidden = false;
  clearInterval(ticker);
  ticker = setInterval(tick, 200);
  tick();
  keepAwake();
}

function nudge(seconds) {
  if (!endsAt) return;
  endsAt = Math.max(Date.now() + 1000, endsAt + seconds * 1000);
  total = Math.max(total + seconds, (endsAt - Date.now()) / 1000);
  tick();
}

export function stop() {
  clearInterval(ticker);
  clearTimeout(hideTimer);
  endsAt = 0;
  bar.hidden = true;
  letSleep();
}

function tick() {
  const left = (endsAt - Date.now()) / 1000;
  if (left <= 0) return finish();
  timeEl.textContent = clock(left);
  fillEl.style.transform = `scaleX(${Math.min(1, left / total)})`;
}

function finish() {
  clearInterval(ticker);
  endsAt = 0;
  timeEl.textContent = '0:00';
  fillEl.style.transform = 'scaleX(0)';
  labelEl.textContent = words.over;
  controls.hidden = true;
  bar.classList.add('is-over');
  sound.play('bell');
  letSleep();
  hideTimer = setTimeout(() => { bar.hidden = true; }, 5000);
}

// Keep the screen on while resting, where the phone allows it, so the bell
// can ring on time.
async function keepAwake() {
  try {
    if (navigator.wakeLock && !wakeLock) wakeLock = await navigator.wakeLock.request('screen');
  } catch {
    wakeLock = null;
  }
}

function letSleep() {
  try {
    if (wakeLock) wakeLock.release();
  } catch {
    // Nothing to do.
  }
  wakeLock = null;
}
