// Saving. Everything the app remembers lives in one object, kept on this device.
// The format number lets old saves be upgraded instead of lost.
//
//   settings     sound, units, default rest length
//   pages        every filed workout page, oldest first
//   draft        the page being written today, or null
//   customLifts  lifts the person added themselves

const KEY = 'composition.app.v1';
const FORMAT = 1;

function blank() {
  return {
    version: FORMAT,
    settings: { sound: true, units: 'lb', restSeconds: 120 },
    pages: [],
    draft: null,
    customLifts: [],
  };
}

// Fill in anything missing so older or hand-edited saves still load.
function tidy(raw) {
  const base = blank();
  if (!raw || typeof raw !== 'object') return base;
  const settings = { ...base.settings, ...(raw.settings && typeof raw.settings === 'object' ? raw.settings : {}) };
  settings.restSeconds = Math.min(600, Math.max(15, Math.round(+settings.restSeconds) || 120));
  return {
    ...base,
    ...raw,
    version: FORMAT,
    settings,
    pages: Array.isArray(raw.pages) ? raw.pages.filter(p => p && Array.isArray(p.lifts)) : [],
    draft: raw.draft && Array.isArray(raw.draft.lifts) ? raw.draft : null,
    customLifts: Array.isArray(raw.customLifts) ? raw.customLifts.filter(l => l && l.id && l.name) : [],
  };
}

let persistent = true;
let data = load();

function load() {
  try {
    const text = localStorage.getItem(KEY);
    return text ? tidy(JSON.parse(text)) : blank();
  } catch {
    persistent = false;
    return blank();
  }
}

function save() {
  try {
    localStorage.setItem(KEY, JSON.stringify(data));
    persistent = true;
  } catch {
    persistent = false;
  }
}

// Check once at startup whether this browser lets us save at all.
try {
  localStorage.setItem(KEY + '.check', '1');
  localStorage.removeItem(KEY + '.check');
} catch {
  persistent = false;
}

export function get() {
  return data;
}

export function isSaving() {
  return persistent;
}

// Change the saved data: store.update(d => { d.settings.sound = false; })
export function update(change) {
  change(data);
  save();
}

// For typing: save shortly after the last keystroke instead of on every one.
let later = 0;
export function updateSoon(change) {
  change(data);
  clearTimeout(later);
  later = setTimeout(() => { later = 0; save(); }, 300);
}
// If the page closes with a save still waiting, do it now.
window.addEventListener('pagehide', () => {
  if (!later) return;
  clearTimeout(later);
  later = 0;
  save();
});

// A backup is plain text the person can keep anywhere.
export function exportText() {
  return JSON.stringify({ app: 'composition', format: FORMAT, savedAt: new Date().toISOString(), data });
}

// Returns the cleaned-up data if the text is a real backup, otherwise null.
export function readBackup(text) {
  try {
    const parsed = JSON.parse(String(text).trim());
    if (!parsed || parsed.app !== 'composition' || typeof parsed.data !== 'object' || !parsed.data) return null;
    if (typeof parsed.format !== 'number' || parsed.format > FORMAT) return null;
    return tidy(parsed.data);
  } catch {
    return null;
  }
}

export function importText(text) {
  const restored = readBackup(text);
  if (!restored) return false;
  data = restored;
  save();
  return true;
}
