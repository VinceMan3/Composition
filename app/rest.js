// The timer in the strip above the tabs. It keeps counting while you flip to
// other pages, and it only starts when you press a button.
//
// It has two jobs:
//   start(seconds)        rest between sets; one bell when it is over
//   startRounds(options)  boxing rounds: a bell to start and end each round,
//                         a wooden knock ten seconds before the end, a break
//                         between rounds, and three bells after the last one.
//
// startRounds takes { rounds, work, rest, onRound }. onRound(done, seconds) is
// called each time a round ends, with how many are done and the seconds worked,
// so the page can write them in.

import { h } from './ui.js';

let bar, timeEl, fillEl, labelEl, controls;
let sound, words;
let mode = null; // 'rest' or 'rounds'
let endsAt = 0;
let total = 0;
let ticker = 0;
let hideTimer = 0;
let wakeLock = null;

// Rounds
let plan = null;      // { rounds, work, rest, onRound }
let round = 1;
let phase = 'work';   // 'work' or 'break'
let knocked = false;  // the ten-second knock for this round
let worked = 0;       // seconds of finished rounds

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

export function isRunning() {
  return endsAt > 0;
}

function begin(seconds, label) {
  clearTimeout(hideTimer);
  total = seconds;
  endsAt = Date.now() + seconds * 1000;
  bar.hidden = false;
  bar.classList.remove('is-over');
  bar.classList.toggle('is-rounds', mode === 'rounds');
  bar.classList.toggle('is-break', mode === 'rounds' && phase === 'break');
  labelEl.textContent = label;
  controls.hidden = false;
  clearInterval(ticker);
  ticker = setInterval(tick, 200);
  tick();
  keepAwake();
}

export function start(seconds) {
  mode = 'rest';
  plan = null;
  begin(seconds, words.label);
}

const roundLabel = () => `${words.round} ${round} ${words.of} ${plan.rounds}`;

export function startRounds({ rounds = 3, work = 180, rest = 60, onRound = null } = {}) {
  mode = 'rounds';
  plan = { rounds, work, rest, onRound };
  round = 1;
  phase = 'work';
  knocked = false;
  worked = 0;
  sound.play('bell');
  begin(work, roundLabel());
}

function nudge(seconds) {
  if (!endsAt) return;
  endsAt = Math.max(Date.now() + 1000, endsAt + seconds * 1000);
  total = Math.max(total + seconds, (endsAt - Date.now()) / 1000);
  if (phase === 'work' && (endsAt - Date.now()) / 1000 > 10.5) knocked = false;
  tick();
}

export function stop() {
  clearInterval(ticker);
  clearTimeout(hideTimer);
  mode = null;
  plan = null;
  endsAt = 0;
  bar.hidden = true;
  bar.classList.remove('is-over', 'is-rounds', 'is-break');
  letSleep();
}

function tick() {
  const left = (endsAt - Date.now()) / 1000;
  if (left <= 0) return finish();
  if (mode === 'rounds' && phase === 'work' && !knocked && left <= 10 && plan.work >= 30) {
    knocked = true;
    sound.play('knock');
  }
  timeEl.textContent = clock(left);
  fillEl.style.transform = `scaleX(${Math.min(1, left / total)})`;
}

// A flash of the bar.
function flash() {
  bar.classList.remove('is-over');
  void bar.offsetWidth;
  bar.classList.add('is-over');
}

// The timer has run out and stays on screen with a message for a few seconds.
function wrapUp(message) {
  clearInterval(ticker);
  mode = null;
  plan = null;
  endsAt = 0;
  timeEl.textContent = '0:00';
  fillEl.style.transform = 'scaleX(0)';
  labelEl.textContent = message;
  controls.hidden = true;
  bar.classList.remove('is-break');
  flash();
  letSleep();
  hideTimer = setTimeout(() => { bar.hidden = true; bar.classList.remove('is-rounds'); }, 6000);
}

function finish() {
  if (mode === 'rounds') return nextPhase();
  sound.play('bell');
  wrapUp(words.over);
}

function nextPhase() {
  if (phase === 'work') {
    worked += total;
    if (plan.onRound) {
      try { plan.onRound(round, worked); } catch { /* the page may be gone */ }
    }
    if (round >= plan.rounds) {
      sound.play('bells');
      wrapUp(`${plan.rounds} ${plan.rounds === 1 ? words.roundDone : words.roundsDone}`);
      return;
    }
    sound.play('bell');
    phase = 'break';
    begin(plan.rest, `${words.breakWord} · ${words.round} ${round + 1} ${words.next}`);
    flash();
    return;
  }
  round += 1;
  phase = 'work';
  knocked = false;
  sound.play('bell');
  begin(plan.work, roundLabel());
  flash();
}

// Keep the screen on while the timer runs, where the phone allows it, so the
// bell can ring on time.
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
