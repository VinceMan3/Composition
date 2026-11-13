// Sounds. Nothing is downloaded: each sound is built on the spot from tones
// and hiss, so the app stays small and works offline.
//
//   play('tap')     a light click for buttons
//   play('flip')    a page turning (the cover)
//   play('flick')   a quick turn between inner pages
//   play('pencil')  a check mark being scratched in
//   play('stamp')   the rubber stamp on a filed page
//   play('bell')    the boxing bell when rest is over
//   play('bells')   three bells: the last round is done
//   play('knock')   two knocks on wood: ten seconds left in the round

let ctx = null;
let out = null;
let hiss = null;
let muted = false;

export function setMuted(value) {
  muted = !!value;
}

export function isMuted() {
  return muted;
}

// Phones only allow sound after a touch, so main.js calls this on every touch.
export function unlock() {
  if (muted) return;
  audio();
}

function audio() {
  if (!ctx) {
    const Ctor = window.AudioContext || window.webkitAudioContext;
    if (!Ctor) return null;
    try {
      ctx = new Ctor();
    } catch {
      return null;
    }
    out = ctx.createGain();
    out.gain.value = 0.9;
    out.connect(ctx.destination);
    hiss = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate);
    const samples = hiss.getChannelData(0);
    for (let i = 0; i < samples.length; i++) samples[i] = Math.random() * 2 - 1;
  }
  if (ctx.state === 'suspended') ctx.resume().catch(() => {});
  return ctx;
}

function buzz(pattern) {
  try {
    // Phones refuse to buzz before the first tap on the page.
    const touched = !navigator.userActivation || navigator.userActivation.hasBeenActive;
    if (navigator.vibrate && touched) navigator.vibrate(pattern);
  } catch {
    // Not every phone can vibrate; that's fine.
  }
}

// A stretch of hiss, shaped by a filter and a volume curve.
// curve is a list of [seconds, volume] points.
function hissBurst(at, length, filter, curve) {
  const src = ctx.createBufferSource();
  src.buffer = hiss;
  const f = ctx.createBiquadFilter();
  f.type = filter.type;
  f.Q.value = filter.q ?? 1;
  f.frequency.setValueAtTime(filter.from, at);
  if (filter.to) f.frequency.exponentialRampToValueAtTime(filter.to, at + length);
  const g = ctx.createGain();
  g.gain.setValueAtTime(0.0001, at);
  for (const [t, v] of curve) g.gain.linearRampToValueAtTime(Math.max(v, 0.0001), at + t);
  g.gain.linearRampToValueAtTime(0.0001, at + length);
  src.connect(f).connect(g).connect(out);
  src.start(at, Math.random() * 1.2, length + 0.05);
  return g;
}

// A tone that can slide in pitch and fades away.
function tone(at, length, from, to, volume, type = 'sine') {
  const osc = ctx.createOscillator();
  osc.type = type;
  osc.frequency.setValueAtTime(from, at);
  if (to !== from) osc.frequency.exponentialRampToValueAtTime(to, at + length);
  const g = ctx.createGain();
  g.gain.setValueAtTime(0.0001, at);
  g.gain.linearRampToValueAtTime(volume, at + 0.004);
  g.gain.exponentialRampToValueAtTime(0.0001, at + length);
  osc.connect(g).connect(out);
  osc.start(at);
  osc.stop(at + length + 0.02);
}

const SOUNDS = {
  tap(t) {
    hissBurst(t, 0.018, { type: 'highpass', from: 2200 }, [[0.002, 0.22]]);
    tone(t, 0.04, 820, 480, 0.1, 'triangle');
  },

  flip(t) {
    // The sheet lifting, then sliding over the rings.
    hissBurst(t, 0.3, { type: 'bandpass', from: 700, to: 3600, q: 0.7 }, [[0.05, 0.3], [0.16, 0.16], [0.24, 0.24]]);
    hissBurst(t + 0.02, 0.26, { type: 'highpass', from: 5200 }, [[0.04, 0.06], [0.2, 0.05]]);
    // It settling.
    hissBurst(t + 0.3, 0.08, { type: 'lowpass', from: 520 }, [[0.006, 0.34]]);
  },

  flick(t) {
    // A quick turn: just the swish of the sheet, then a light settle.
    hissBurst(t, 0.15, { type: 'bandpass', from: 1100, to: 4200, q: 0.7 }, [[0.03, 0.24], [0.11, 0.14]]);
    hissBurst(t + 0.15, 0.05, { type: 'lowpass', from: 600 }, [[0.004, 0.2]]);
  },

  pencil(t) {
    // Short stroke down, long stroke up: a check mark.
    hissBurst(t, 0.07, { type: 'bandpass', from: 2300, to: 1900, q: 1.6 }, [[0.012, 0.3], [0.05, 0.2]]);
    hissBurst(t + 0.1, 0.17, { type: 'bandpass', from: 2000, to: 3500, q: 1.6 }, [[0.02, 0.34], [0.07, 0.2], [0.11, 0.3]]);
    buzz(8);
  },

  stamp(t) {
    tone(t, 0.2, 150, 44, 0.95);
    hissBurst(t, 0.06, { type: 'lowpass', from: 1100 }, [[0.004, 0.5]]);
    hissBurst(t + 0.075, 0.035, { type: 'bandpass', from: 1700, q: 1 }, [[0.004, 0.1]]);
    buzz(24);
  },

  bell(t) {
    // A struck steel bell: a few ringing tones that don't quite line up.
    const base = 587;
    const partials = [[1, 0.26, 2.1], [2.76, 0.17, 1.4], [5.4, 0.1, 0.8], [8.93, 0.05, 0.4]];
    for (const [ratio, volume, length] of partials) {
      tone(t, length, base * ratio, base * ratio, volume);
      tone(t, length * 0.9, base * ratio * 1.004, base * ratio * 1.004, volume * 0.5);
    }
    hissBurst(t, 0.03, { type: 'highpass', from: 3200 }, [[0.002, 0.3]]);
    buzz([40, 60, 40]);
  },

  bells(t) {
    for (const at of [0, 0.42, 0.84]) SOUNDS.bell(t + at);
  },

  knock(t) {
    // Two raps of a stick on the ring post.
    for (const at of [0, 0.16]) {
      tone(t + at, 0.09, 920, 610, 0.34, 'triangle');
      tone(t + at, 0.05, 1900, 1500, 0.08);
      hissBurst(t + at, 0.03, { type: 'bandpass', from: 2400, q: 1.4 }, [[0.002, 0.32]]);
    }
    buzz([12, 120, 12]);
  },
};

export function play(name) {
  if (muted || !SOUNDS[name]) return;
  const a = audio();
  if (!a) return;
  try {
    SOUNDS[name](a.currentTime + 0.005);
  } catch {
    // A sound failing should never break the app.
  }
}
