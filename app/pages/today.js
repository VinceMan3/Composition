// Today's page. Before a page is started it offers to repeat a past page or
// start a fresh one; after that it is the page you write your sets on.

import { h, put, count, icon, art, shortDate, pageHead, twoTap, noteField } from '../ui.js';
import * as log from '../log.js';
import { clock } from '../rest.js';
import { poseSketch } from '../poses.js';
import { collect } from '../awards.js';
import { CARDIO, CARDIO_UNITS } from '../../content/cardio.js';

export function render(el, ctx) {
  return ctx.store.get().draft ? writing(el, ctx) : starting(el, ctx);
}

// ---------- no page yet ----------

function starting(el, ctx) {
  const { words, store, sound } = ctx;
  const w = words.today;
  const past = log.pagesToRepeat(store.get());

  function begin(page) {
    store.update(d => { d.draft = page; });
    sound.play('pencil');
    ctx.refresh();
  }

  const titleBox = h('input', {
    class: 'write-in',
    type: 'text',
    maxlength: '40',
    placeholder: w.titlePlaceholder,
    'aria-label': w.titleLabel,
    enterkeyhint: 'go',
    autocomplete: 'off',
    onKeydown(e) { if (e.key === 'Enter') startBlank(); },
  });
  const startBlank = () => begin(log.newPage(titleBox.value.trim() || w.untitled));

  put(el,
    art('sketch-front.webp', 'sketch sketch-front', 640, 587),
    pageHead(shortDate(), w.title, w.note),

    past.length > 0 && h('div', { class: 'start' },
      h('p', { class: 'label' }, w.repeatLabel),
      h('p', { class: 'quiet' }, w.repeatNote),
      past.map(page => h('button', {
        class: 'repeat',
        type: 'button',
        'data-sound': 'none',
        onClick: () => begin(log.repeatPage(store.get(), page)),
      },
        h('span', { class: 'repeat-title' }, page.title),
        h('span', { class: 'repeat-go' }, w.repeatGo),
        h('span', { class: 'repeat-meta' }, `${log.niceDate(page.date)} · ${count(page.lifts.length, words.count.lift)}`),
      )),
    ),

    h('div', { class: 'start' },
      h('p', { class: 'label' }, past.length ? w.blankLabel : w.startLabel),
      titleBox,
      h('div', { class: 'chips' }, w.titleIdeas.map(idea =>
        h('button', { class: 'chip', type: 'button', 'data-sound': 'none', onClick: () => begin(log.newPage(idea)) }, idea))),
      h('button', { class: 'btn', type: 'button', 'data-sound': 'none', onClick: startBlank }, w.blankButton),
    ),
  );
}

// ---------- writing the page ----------

function writing(el, ctx) {
  const { words, store, sound, toast } = ctx;
  const w = words.today;
  const data = store.get();
  const page = data.draft;
  const unit = page.unit;
  const save = () => store.update(() => {}); // the page is changed in place, then saved

  let rows = [];      // rows[lift][set] = the pieces of that row on screen
  let blocks = [];    // one element per lift
  let active = firstOpen();

  function firstOpen(from = 0) {
    for (let li = from; li < page.lifts.length; li++) {
      const si = page.lifts[li].sets.findIndex(s => !s.done);
      if (si >= 0) return { li, si };
    }
    return from > 0 ? firstOpen(0) : null;
  }

  const liftOf = li => log.findLift(data, page.lifts[li].liftId);
  const prevOf = li => log.lastTime(data, page.lifts[li].liftId);
  const cleanNumber = text => text.replace(',', '.').replace(/[^0-9.]/g, '');

  // ----- the tools under the set you are on -----
  const weightWord = h('span', { class: 'stepper-word' }, unit);
  const repsWord = h('span', { class: 'stepper-word' }, w.cols.reps);
  const plateLine = h('div', { class: 'plates' });
  const stepButton = (label, name, field, sign) =>
    h('button', { type: 'button', 'aria-label': name, onClick: () => nudge(field, sign) }, label);
  const weightMinus = stepButton(`−${log.STEP[unit]}`, 'Less weight', 'w', -1);
  const weightPlus = stepButton(`+${log.STEP[unit]}`, 'More weight', 'w', 1);
  const repsMinus = stepButton('−1', 'Fewer reps', 'r', -1);
  const repsPlus = stepButton('+1', 'More reps', 'r', 1);
  const tools = h('div', { class: 'set-tools' },
    h('div', { class: 'stepper' }, weightMinus, weightWord, weightPlus),
    h('div', { class: 'stepper' }, repsMinus, repsWord, repsPlus),
    plateLine,
    h('button', {
      class: 'btn btn-small rest-btn',
      type: 'button',
      onClick: () => ctx.rest.start(store.get().settings.restSeconds),
    }, `${w.rest} ${clock(data.settings.restSeconds)}`),
  );

  function nudge(field, sign) {
    if (!active) return;
    const { li, si } = active;
    const entry = page.lifts[li];
    const set = entry.sets[si];
    const timed = liftOf(li).kind === 'timed';
    const step = field === 'w' ? log.STEP[unit] : timed ? 5 : 1;
    const start = set[field] !== '' ? log.num(set[field]) : log.num(log.ghost(entry, si, prevOf(li))[field]);
    set[field] = log.tidy(Math.max(0, start + sign * step));
    save();
    const input = field === 'w' ? rows[li][si].weight : rows[li][si].reps;
    input.value = set[field];
    input.classList.remove('is-bumped');
    void input.offsetWidth; // lets the little jump replay
    input.classList.add('is-bumped');
    afterEdit(li, si);
  }

  function showPlates() {
    plateLine.replaceChildren();
    if (!active) return;
    const { li, si } = active;
    const lift = liftOf(li);
    const timed = lift.kind === 'timed';
    weightWord.textContent = unit;
    repsWord.textContent = timed ? w.cols.seconds : w.cols.reps;
    repsMinus.textContent = timed ? '−5' : '−1';
    repsPlus.textContent = timed ? '+5' : '+1';
    if (!log.isBarbell(lift)) return;
    const entry = page.lifts[li];
    const total = entry.sets[si].w || log.ghost(entry, si, prevOf(li)).w;
    const load = log.plates(total, unit);
    if (!load) return;
    if (!load.list.length) {
      plateLine.append(`${w.barOnly}: ${load.bar} ${unit}`);
      return;
    }
    plateLine.append(w.eachSide, ...load.list.map(p => h('span', { class: 'plate' }, log.tidy(p))), `${w.onA} ${load.bar} ${unit} ${w.bar}`);
  }

  function placeTools() {
    for (const liftRows of rows) for (const r of liftRows) r.row.classList.remove('is-active');
    if (!active || !rows[active.li] || !rows[active.li][active.si]) {
      tools.remove();
      return;
    }
    const r = rows[active.li][active.si];
    r.row.classList.add('is-active');
    r.row.after(tools);
    showPlates();
  }

  function setActive(li, si) {
    if (active && active.li === li && active.si === si) return;
    active = { li, si };
    placeTools();
  }

  // ----- one set -----

  // The handwritten note under a finished set: how it compares with last time.
  function showNote(li, si) {
    const r = rows[li][si];
    const set = page.lifts[li].sets[si];
    const prev = prevOf(li);
    const then = prev && prev.sets[si];
    const result = set.done && then ? log.compare(set, then, unit, liftOf(li)) : null;
    r.note.hidden = !result;
    if (!result) return;
    r.note.textContent = result.dir ? `${result.text} ${w.onLastTime}` : w.same;
    r.note.className = `set-note ${result.dir > 0 ? 'up' : result.dir < 0 ? 'down' : 'hand'}`;
  }

  // The pencilled-in numbers for a lift, which shift as sets get written.
  function showGhosts(li) {
    const entry = page.lifts[li];
    const lift = liftOf(li);
    entry.sets.forEach((set, si) => {
      const g = log.ghost(entry, si, prevOf(li));
      rows[li][si].weight.placeholder = g.w || (lift.kind === 'bodyweight' ? 'BW' : '');
      rows[li][si].reps.placeholder = g.r;
    });
  }

  function afterEdit(li, si) {
    showGhosts(li);
    showNote(li, si);
    if (active && active.li === li) showPlates();
  }

  function toggle(li, si) {
    const entry = page.lifts[li];
    const set = entry.sets[si];
    const r = rows[li][si];
    if (set.done) {
      set.done = false;
      save();
      sound.play('tap');
    } else {
      // An empty box takes the pencilled-in number.
      const g = log.ghost(entry, si, prevOf(li));
      const repsNow = set.r === '' ? g.r : set.r;
      if (!log.num(repsNow)) {
        setActive(li, si);
        toast(w.needReps);
        r.reps.focus();
        return;
      }
      set.r = repsNow;
      if (set.w === '') set.w = g.w;
      set.done = true;
      save();
      r.weight.value = set.w;
      r.reps.value = set.r;
      sound.play('pencil');
    }
    r.check.setAttribute('aria-pressed', String(set.done));
    r.row.classList.toggle('is-done', set.done);
    afterEdit(li, si);
    if (set.done) {
      // Move on to the next open set: this lift first, then the rest.
      const next = entry.sets.findIndex((s, i) => i > si && !s.done);
      active = next >= 0 ? { li, si: next } : firstOpen(li + 1);
    } else {
      active = { li, si };
    }
    placeTools();
  }

  function setRow(li, si) {
    const set = page.lifts[li].sets[si];
    const lift = liftOf(li);
    const field = (key, label, mode, extra) => {
      const input = h('input', {
        type: 'text',
        inputmode: mode,
        autocomplete: 'off',
        class: extra,
        value: set[key],
        'aria-label': `${lift.name}, set ${si + 1}, ${label}`,
        onFocus: () => setActive(li, si),
        onInput() {
          const clean = cleanNumber(input.value);
          if (clean !== input.value) input.value = clean;
          set[key] = clean;
          save();
          afterEdit(li, si);
        },
      });
      return input;
    };
    const weight = field('w', unit, 'decimal');
    const reps = field('r', lift.kind === 'timed' ? 'seconds' : 'reps', 'numeric');
    const rpe = field('rpe', 'RPE', 'decimal', 'rpe');
    const check = h('button', {
      class: 'check',
      type: 'button',
      'aria-pressed': String(set.done),
      'aria-label': `${lift.name}, set ${si + 1} done`,
      'data-sound': 'none',
      onClick: () => toggle(li, si),
    }, icon('M5 13l4.5 4.5L19 7'));
    const note = h('p', { class: 'set-note', hidden: true });
    const row = h('div', { class: `set-row${set.done ? ' is-done' : ''}` },
      h('button', { class: 'set-n', type: 'button', 'aria-label': `Go to set ${si + 1}`, onClick: () => setActive(li, si) }, String(si + 1)),
      weight, reps, rpe, check, note,
    );
    return { row, weight, reps, rpe, check, note };
  }

  // ----- one lift -----

  // The standing note for a lift: cues, seat settings, anything worth
  // remembering. It belongs to the lift, so it shows on every page.
  function liftNote(lift) {
    return noteField({
      get: () => store.get().liftNotes[lift.id],
      set: text => store.updateSoon(d => {
        if (text.trim()) d.liftNotes[lift.id] = text;
        else delete d.liftNotes[lift.id];
      }),
      placeholder: w.notePlaceholder,
      addLabel: w.addNote,
      doneLabel: w.noteDone,
      label: `${lift.name}: ${w.noteLabel}`,
    });
  }

  function liftBlock(entry, li) {
    const lift = liftOf(li);
    const prev = prevOf(li);
    rows[li] = entry.sets.map((_, si) => setRow(li, si));

    const remove = twoTap(
      h('button', { class: 'lift-remove', type: 'button' }, w.removeLift),
      w.removeLiftConfirm,
      () => { page.lifts.splice(li, 1); save(); active = firstOpen(); draw(); },
    );
    const block = h('section', { class: 'lift' },
      h('div', { class: 'lift-head' },
        h('div', null,
          h('h2', { class: 'lift-name' }, lift.name),
          h('p', { class: 'lift-last' }, prev ? `${w.lastTime}: ${log.setsText(prev.sets, lift)}` : w.firstTime),
          liftNote(lift),
        ),
        remove,
      ),
      h('div', { class: 'set-cols', 'aria-hidden': 'true' },
        h('span'),
        h('span', null, lift.kind === 'bodyweight' ? w.cols.added : unit),
        h('span', null, lift.kind === 'timed' ? w.cols.seconds : w.cols.reps),
        h('span', null, w.cols.rpe),
        h('span'),
      ),
      rows[li].map(r => r.row),
      h('div', { class: 'lift-foot' },
        h('button', {
          class: 'btn btn-line btn-small',
          type: 'button',
          onClick() {
            entry.sets.push({ w: '', r: '', rpe: '', done: false });
            save();
            if (!active) active = { li, si: entry.sets.length - 1 };
            draw();
          },
        }, w.addSet),
        entry.sets.length > 1 && h('button', {
          class: 'btn btn-line btn-small',
          type: 'button',
          onClick() {
            entry.sets.pop();
            save();
            if (active && active.li === li && active.si >= entry.sets.length) active = firstOpen();
            draw();
          },
        }, w.removeSet),
      ),
      // A note about this lift today only ("left shoulder felt off").
      h('div', { class: 'day-note' }, noteField({
        get: () => entry.note,
        set: text => { if (text.trim()) entry.note = text; else delete entry.note; store.updateSoon(() => {}); },
        placeholder: w.dayNotePlaceholder,
        addLabel: w.addDayNote,
        doneLabel: w.noteDone,
        label: `${lift.name}: ${w.dayNoteLabel}`,
      })),
    );
    return block;
  }

  const listEl = h('div', { class: 'lifts bleed' });

  // ----- cardio: boxing, running and the rest -----
  page.cardio = page.cardio || [];
  const cardioEl = h('div', { class: 'lifts bleed' });

  function cardioBlock(entry, ci) {
    const kind = log.findCardio(entry.kindId);
    const boxes = kind.fields.map(name => {
      const input = h('input', {
        type: 'text',
        inputmode: 'decimal',
        autocomplete: 'off',
        value: entry.values[name] || '',
        'aria-label': `${kind.name}, ${name}`,
        onInput() {
          const clean = cleanNumber(input.value);
          if (clean !== input.value) input.value = clean;
          entry.values[name] = clean;
          save();
        },
      });
      return h('label', { class: 'cardio-box' }, input, h('span', null, CARDIO_UNITS[name]));
    });
    const check = h('button', {
      class: 'check',
      type: 'button',
      'aria-pressed': String(entry.done),
      'aria-label': `${kind.name} done`,
      'data-sound': 'none',
      onClick() {
        if (!entry.done && !log.hasNumbers(entry)) {
          toast(w.needCardio);
          boxes[0].querySelector('input').focus();
          return;
        }
        entry.done = !entry.done;
        save();
        sound.play(entry.done ? 'pencil' : 'tap');
        check.setAttribute('aria-pressed', String(entry.done));
        block.classList.toggle('is-done', entry.done);
      },
    }, icon('M5 13l4.5 4.5L19 7'));
    const remove = twoTap(
      h('button', { class: 'lift-remove', type: 'button' }, w.removeLift),
      w.removeLiftConfirm,
      () => { page.cardio.splice(ci, 1); save(); drawCardio(); },
    );
    const block = h('section', { class: `lift cardio${kind.boxing ? ' is-boxing' : ''}${entry.done ? ' is-done' : ''}` },
      h('div', { class: 'lift-head' }, h('div', null, h('h2', { class: 'lift-name' }, kind.name)), remove),
      h('div', { class: 'cardio-row' }, boxes, check),
      kind.boxing && h('div', { class: 'lift-foot' },
        h('button', {
          class: 'btn btn-small',
          type: 'button',
          onClick() {
            const s = store.get().settings;
            ctx.rest.startRounds({
              rounds: s.roundCount,
              work: s.roundSeconds,
              rest: s.breakSeconds,
              // Each finished round is written into this entry, even if the
              // page has been flipped away from.
              onRound(done, seconds) {
                entry.values.rounds = String(done);
                entry.values.minutes = log.tidy(Math.round(seconds / 6) / 10);
                store.update(() => {});
                window.dispatchEvent(new CustomEvent('composition:rounds'));
              },
            });
          },
        }, `${w.roundsButton} ${data.settings.roundCount} × ${clock(data.settings.roundSeconds)}`),
      ),
    );
    return block;
  }

  let cardioBlocks = [];
  function drawCardio() {
    cardioBlocks = page.cardio.map(cardioBlock);
    cardioEl.replaceChildren(...cardioBlocks);
    emptyNote.hidden = page.lifts.length + page.cardio.length > 0;
  }

  // The choices that open under "+ Add cardio".
  const cardioTray = h('div', { class: 'chips', hidden: true }, CARDIO.map(kind =>
    h('button', {
      class: `chip${kind.boxing ? ' is-boxing' : ''}`,
      type: 'button',
      'data-sound': 'none',
      onClick() {
        log.addCardio(page, kind.id);
        save();
        sound.play('pencil');
        cardioTray.hidden = true;
        drawCardio();
        cardioBlocks[cardioBlocks.length - 1].scrollIntoView({ block: 'center' });
      },
    }, kind.name)));

  function draw() {
    rows = [];
    blocks = page.lifts.map(liftBlock);
    listEl.replaceChildren(...blocks);
    emptyNote.hidden = page.lifts.length + page.cardio.length > 0;
    page.lifts.forEach((entry, li) => {
      showGhosts(li);
      entry.sets.forEach((_, si) => showNote(li, si));
    });
    placeTools();
  }

  // ----- the page around the lifts -----

  const title = h('input', {
    class: 'title-input',
    type: 'text',
    maxlength: '40',
    value: page.title,
    'aria-label': w.titleLabel,
    autocomplete: 'off',
    onInput() { page.title = title.value; save(); },
    onBlur() { if (!title.value.trim()) { title.value = page.title = w.untitled; save(); } },
  });
  const emptyNote = h('p', { class: 'hand', style: 'font-size:18px' }, w.empty);

  const doneCount = () => page.lifts.reduce((n, e) => n + e.sets.filter(s => s.done).length, 0) + page.cardio.filter(c => c.done).length;
  const openCount = () => page.lifts.reduce((n, e) => n + e.sets.filter(s => !s.done).length, 0) + page.cardio.filter(c => !c.done).length;
  function fileIt() {
    ctx.rest.stop();
    store.update(d => {
      const summary = log.fileDraft(d);
      summary.stickers = collect(d);
      ctx.state.newStickers = [...(ctx.state.newStickers || []), ...summary.stickers];
    });
    ctx.state.justFiled = true;
    ctx.go('filed');
  }
  const fileButton = h('button', { class: 'btn', type: 'button', 'data-sound': 'none' }, w.file);
  twoTap(fileButton, w.fileConfirm, fileIt, () => {
    if (!doneCount()) { sound.play('tap'); toast(w.needOneSet); return false; }
    const open = openCount();
    if (!open) { fileIt(); return false; }
    sound.play('tap');
    toast(`${open} ${w.leftOff}`);
    return true;
  });

  const tear = twoTap(h('button', { class: 'link-btn', type: 'button' }, w.tear), w.tearConfirm, () => {
    ctx.rest.stop();
    store.update(d => { d.draft = null; });
    toast(w.torn);
    ctx.refresh();
  });

  put(el,
    poseSketch(data, page),
    h('div', { class: 'head-block with-pose' },
      h('p', { class: 'kicker' }, shortDate()),
      title,
    ),
    emptyNote,
    listEl,
    cardioEl,
    h('div', { class: 'page-actions' },
      h('a', { class: 'btn btn-line', href: '#add' }, w.addLift),
      h('button', { class: 'btn btn-line btn-cardio', type: 'button', onClick() { cardioTray.hidden = !cardioTray.hidden; } }, w.addCardio),
      cardioTray,
      fileButton,
      tear,
    ),
  );
  draw();
  drawCardio();

  // Coming back from "add a lift": bring the new lift into view.
  const focusLift = ctx.state.focusLift;
  ctx.state.focusLift = null;

  // The round timer writes rounds into a boxing entry; show them as they land.
  const onRounds = () => drawCardio();
  window.addEventListener('composition:rounds', onRounds);

  return {
    cleanUp() { window.removeEventListener('composition:rounds', onRounds); },
    onAttached() {
      if (focusLift == null || !blocks[focusLift]) return;
      const scroller = el.parentElement;
      scroller.scrollTop = Math.max(0, blocks[focusLift].offsetTop - 12);
    },
  };
}
