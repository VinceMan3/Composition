// Contents: sound, and keeping a backup. Later steps add the rest of the
// notebook's sections here.

import { h, put, pageHead } from '../ui.js';
import { clock } from '../rest.js';
import { STICKERS, hasSticker } from '../awards.js';

export function render(el, ctx) {
  const { words, store, sound, toast } = ctx;
  const w = words.more;
  let disarm = 0;

  // ---- sound on / off ----
  const soundOn = store.get().settings.sound;
  function setSound(on) {
    store.update(d => { d.settings.sound = on; });
    sound.setMuted(!on);
    onBtn.setAttribute('aria-pressed', String(on));
    offBtn.setAttribute('aria-pressed', String(!on));
    if (on) sound.play('tap');
    toast(on ? words.toasts.soundOn : words.toasts.soundOff);
  }
  const onBtn = h('button', { type: 'button', 'aria-pressed': String(soundOn), 'data-sound': 'none', onClick: () => setSound(true) }, w.on);
  const offBtn = h('button', { type: 'button', 'aria-pressed': String(!soundOn), 'data-sound': 'none', onClick: () => setSound(false) }, w.off);

  // ---- two-way choices: units, and the look ----
  // choice(label, note, key, [[value, word], [value, word]], after)
  function choice(label, note, key, options, after) {
    const buttons = options.map(([value, word]) => h('button', {
      type: 'button',
      'aria-pressed': String(store.get().settings[key] === value),
      onClick() {
        store.update(d => { d.settings[key] = value; });
        buttons.forEach((b, i) => b.setAttribute('aria-pressed', String(options[i][0] === value)));
        if (after) after(value);
      },
    }, word));
    return h('div', { class: 'row' },
      h('div', null, h('p', { class: 'label' }, label), h('p', { class: 'quiet' }, note)),
      h('div', { class: 'seg', role: 'group', 'aria-label': label }, buttons),
    );
  }
  const unitsRow = choice(w.unitsLabel, w.unitsNote, 'units', [['lb', 'lb'], ['kg', 'kg']]);
  const lookRow = choice(w.lookLabel, w.lookNote, 'look', [['paper', w.lookPaper], ['garage', w.lookGarage]], value => {
    document.documentElement.dataset.look = value;
  });

  // ---- how long a rest runs ----
  const restValue = h('span', { class: 'stepper-value' }, clock(store.get().settings.restSeconds));
  function setRest(change) {
    store.update(d => { d.settings.restSeconds = Math.min(600, Math.max(15, d.settings.restSeconds + change)); });
    restValue.textContent = clock(store.get().settings.restSeconds);
  }

  // ---- boxing round lengths ----
  function lengthStepper(key, min, max) {
    const value = h('span', { class: 'stepper-value' }, clock(store.get().settings[key]));
    const step = change => {
      store.update(d => { d.settings[key] = Math.min(max, Math.max(min, d.settings[key] + change)); });
      value.textContent = clock(store.get().settings[key]);
    };
    return h('div', { class: 'stepper' },
      h('button', { type: 'button', 'aria-label': 'Fifteen seconds shorter', onClick: () => step(-15) }, '−15'),
      value,
      h('button', { type: 'button', 'aria-label': 'Fifteen seconds longer', onClick: () => step(15) }, '+15'),
    );
  }

  function countStepper() {
    const value = h('span', { class: 'stepper-value' }, `${store.get().settings.roundCount}×`);
    const step = change => {
      store.update(d => { d.settings.roundCount = Math.min(15, Math.max(1, d.settings.roundCount + change)); });
      value.textContent = `${store.get().settings.roundCount}×`;
    };
    return h('div', { class: 'stepper' },
      h('button', { type: 'button', 'aria-label': 'One round fewer', onClick: () => step(-1) }, '−1'),
      value,
      h('button', { type: 'button', 'aria-label': 'One round more', onClick: () => step(1) }, '+1'),
    );
  }

  // ---- try the sounds ----
  const stamp = h('span', { class: 'stamp', hidden: true }, w.stampWord);
  function trySound(name) {
    sound.play(name);
    if (name !== 'stamp') return;
    stamp.hidden = false;
    stamp.classList.remove('is-stamping');
    void stamp.offsetWidth; // lets the stamp come down again
    stamp.classList.add('is-stamping');
  }
  const soundButtons = Object.entries(w.sounds).map(([name, label]) =>
    h('button', { class: 'btn btn-line btn-small', type: 'button', 'data-sound': 'none', onClick: () => trySound(name) }, label));

  // ---- backup ----
  const backupBox = h('textarea', { class: 'backup-box', readonly: true, hidden: true, 'aria-label': w.backupLabel });
  const copyBtn = h('button', {
    class: 'btn btn-line',
    type: 'button',
    hidden: true,
    onClick() {
      const fallback = () => { backupBox.focus(); backupBox.select(); toast(words.toasts.copyFailed); };
      if (!navigator.clipboard) return fallback();
      navigator.clipboard.writeText(backupBox.value).then(() => toast(words.toasts.copied), fallback);
    },
  }, w.copyButton);
  const makeBtn = h('button', {
    class: 'btn',
    type: 'button',
    onClick() {
      backupBox.value = store.exportText();
      backupBox.hidden = false;
      copyBtn.hidden = false;
    },
  }, w.backupButton);

  // ---- restore: two taps, because it replaces everything ----
  const restoreBox = h('textarea', { class: 'backup-box', placeholder: w.restorePlaceholder, 'aria-label': w.restoreLabel, spellcheck: 'false' });
  const restoreBtn = h('button', {
    class: 'btn btn-line',
    type: 'button',
    'data-sound': 'none',
    onClick() {
      const text = restoreBox.value;
      if (!text.trim()) { sound.play('tap'); return toast(words.toasts.restoreEmpty); }
      if (!store.readBackup(text)) { sound.play('tap'); return toast(words.toasts.restoreBad); }
      if (restoreBtn.dataset.armed !== 'yes') {
        sound.play('tap');
        restoreBtn.dataset.armed = 'yes';
        restoreBtn.textContent = w.restoreConfirm;
        clearTimeout(disarm);
        disarm = setTimeout(() => {
          restoreBtn.dataset.armed = '';
          restoreBtn.textContent = w.restoreButton;
        }, 5000);
        return;
      }
      store.importText(text);
      document.documentElement.dataset.look = store.get().settings.look;
      sound.setMuted(!store.get().settings.sound);
      sound.play('stamp');
      toast(words.toasts.restored);
      ctx.refresh();
    },
  }, w.restoreButton);

  put(el,
    pageHead(words.tabs.more, w.title, w.note),

    h('div', { class: 'panel' },
      h('div', { class: 'row' },
        h('div', null,
          h('p', { class: 'label' }, w.stickersLabel),
          h('p', { class: 'quiet' }, `${STICKERS.filter(s => hasSticker(store.get(), s)).length} ${words.stickers.of} ${STICKERS.length} ${w.stickersNote}`),
        ),
        h('a', { class: 'btn btn-small', href: '#stickers' }, w.stickersButton),
      ),
    ),

    h('div', { class: 'panel' }, unitsRow, lookRow),

    h('div', { class: 'panel' },
      h('div', { class: 'row' },
        h('div', null,
          h('p', { class: 'label' }, w.soundLabel),
          h('p', { class: 'quiet' }, w.soundNote),
        ),
        h('div', { class: 'seg', role: 'group', 'aria-label': w.soundLabel }, onBtn, offBtn),
      ),
      h('div', { class: 'row stamp-row' },
        h('p', { class: 'label' }, w.tryLabel),
        h('div', { class: 'stamp-zone', 'aria-hidden': 'true' }, stamp),
      ),
      h('div', { class: 'wrap' }, soundButtons),
    ),

    h('div', { class: 'panel' },
      h('div', { class: 'row' },
        h('div', null,
          h('p', { class: 'label' }, w.restLabel),
          h('p', { class: 'quiet' }, w.restNote),
        ),
        h('div', { class: 'stepper' },
          h('button', { type: 'button', 'aria-label': 'Fifteen seconds shorter', onClick: () => setRest(-15) }, '−15'),
          restValue,
          h('button', { type: 'button', 'aria-label': 'Fifteen seconds longer', onClick: () => setRest(15) }, '+15'),
        ),
      ),
    ),

    h('div', { class: 'panel' },
      h('div', null,
        h('p', { class: 'label' }, w.roundLabel),
        h('p', { class: 'quiet' }, w.roundNote),
      ),
      h('div', { class: 'row' }, h('span', { class: 'setting-name' }, w.roundCount), countStepper()),
      h('div', { class: 'row' }, h('span', { class: 'setting-name' }, w.roundLength), lengthStepper('roundSeconds', 30, 600)),
      h('div', { class: 'row' }, h('span', { class: 'setting-name' }, w.breakLength), lengthStepper('breakSeconds', 15, 300)),
    ),

    h('div', { class: 'panel' },
      h('p', { class: 'label' }, w.backupLabel),
      h('p', { class: 'quiet' }, w.backupNote),
      !store.isSaving() && h('p', { class: 'quiet warn' }, w.notSaving),
      makeBtn,
      backupBox,
      copyBtn,
    ),

    h('div', { class: 'panel' },
      h('p', { class: 'label' }, w.restoreLabel),
      h('p', { class: 'quiet' }, w.restoreNote),
      restoreBox,
      restoreBtn,
    ),

    h('p', { class: 'version' }, w.version),
  );

  return () => clearTimeout(disarm);
}
