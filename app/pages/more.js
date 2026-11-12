// Contents: sound, and keeping a backup. Later steps add the rest of the
// notebook's sections here.

import { h, put, pageHead } from '../ui.js';
import { clock } from '../rest.js';

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

  // ---- how long a rest runs ----
  const restValue = h('span', { class: 'stepper-value' }, clock(store.get().settings.restSeconds));
  function setRest(change) {
    store.update(d => { d.settings.restSeconds = Math.min(600, Math.max(15, d.settings.restSeconds + change)); });
    restValue.textContent = clock(store.get().settings.restSeconds);
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
