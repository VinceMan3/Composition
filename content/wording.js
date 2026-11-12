/*
  WORDING
  Safe to edit. Change the text between the quotes and save.
  Keep the quotes, commas and brackets exactly as they are.
  If your text needs an apostrophe, put a backslash before it: 'today\'s page'
*/
export const WORDS = {
  appName: 'Composition',
  tagline: 'Training log',

  // Counting words: one, then more than one
  count: {
    lift: ['lift', 'lifts'],
    set: ['set', 'sets'],
  },

  // The five tabs along the bottom
  tabs: {
    cover: 'Cover',
    today: 'Today',
    notebook: 'Notebook',
    stats: 'Stats',
    more: 'More',
  },

  cover: {
    verseLabel: 'Today\'s verse',
    startLabel: 'Inside this notebook',
    startTitle: 'Open to today',
    startNote: 'a fresh page is waiting',
    startButton: 'Open today\'s page',
    goingLabel: 'Page in progress',
    goingNote: 'so far',
    goingButton: 'Back to the page',
    doneLabel: 'Filed today',
    doneNote: 'in the notebook',
    doneButton: 'Start another page',
  },

  today: {
    // Before a page is started
    title: 'Today\'s page',
    note: 'nothing written yet',
    repeatLabel: 'Repeat a page',
    repeatGo: 'Repeat',
    startLabel: 'Start a page',
    repeatNote: 'Same lifts, with last time\'s numbers pencilled in.',
    blankLabel: 'Or start a fresh one',
    titlePlaceholder: 'Name the page',
    titleIdeas: ['Chest day', 'Back day', 'Leg day', 'Shoulders', 'Arms', 'Push', 'Pull'],
    blankButton: 'Start the page',
    untitled: 'Workout',

    // While writing the page
    titleLabel: 'Page title',
    empty: 'No lifts yet. Add the first one.',
    lastTime: 'last time',
    firstTime: 'first time in the notebook',
    addSet: '+ Set',
    removeSet: '− Set',
    removeLift: 'Remove',
    removeLiftConfirm: 'Tap again',
    rest: 'Rest',
    eachSide: 'each side',
    barOnly: 'just the bar',
    onA: 'on a',
    bar: 'bar',
    addLift: '+ Add a lift',
    file: 'File this page',
    fileConfirm: 'Tap again to file it',
    tear: 'Tear out this page',
    tearConfirm: 'Tap again to throw it away',
    needReps: 'Write the reps first.',
    needOneSet: 'Check off at least one set first.',
    leftOff: 'unchecked sets will be left off',
    torn: 'Page torn out.',
    cols: { weight: 'lb', added: '+ lb', reps: 'reps', seconds: 'sec', rpe: 'RPE' },
    same: 'same as last time',
    onLastTime: 'on last time',
  },

  add: {
    kicker: 'Add a lift',
    title: 'Pick a lift',
    back: 'Back to the page',
    searchPlaceholder: 'Search the lifts',
    all: 'All',
    onPage: 'on the page',
    yours: 'Your lifts',
    addOwn: 'Add as your own lift:',
    none: 'Nothing by that name.',
  },

  filed: {
    stamp: 'Filed',
    kicker: 'Page filed',
    totals: { lifts: 'Lifts', sets: 'Sets', volume: 'Pounds moved', minutes: 'Minutes' },
    recordLabel: 'New record',
    estMax: 'est. max',
    was: 'was',
    compareLabel: 'Against last time',
    best: 'best set',
    firstTime: 'first time',
    same: 'same',
    toCover: 'Back to the cover',
    toNotebook: 'Open the notebook',
  },

  rest: {
    label: 'Rest',
    less: '−15',
    more: '+15',
    stop: 'Done',
    over: 'Rest over. Back to work.',
  },

  notebook: {
    title: 'The notebook',
    note: 'every filed page lands here',
    empty: 'No pages filed yet.',
    filedLabel: 'Filed pages',
    comingLabel: 'Coming in step 3',
    coming: [
      'Open and fix an old page',
      'The lift library, and each lift\'s history',
    ],
  },

  stats: {
    title: 'Progress',
    note: 'plotted by hand',
    comingLabel: 'Coming in step 5',
    coming: [
      'The Big Three and your estimated maxes',
      'Records and ribbons',
      'Charts, the training calendar, Wilks and DOTS',
    ],
  },

  more: {
    title: 'Contents',
    note: 'the rest of the notebook',
    soundLabel: 'Sound',
    soundNote: 'Pencil, paper, stamp and bell',
    on: 'On',
    off: 'Off',
    tryLabel: 'Try the sounds',
    sounds: {
      tap: 'Tap',
      flip: 'Page',
      pencil: 'Pencil',
      stamp: 'Stamp',
      bell: 'Bell',
    },
    stampWord: 'Filed',
    restLabel: 'Rest timer',
    restNote: 'How long the timer runs when you start it',
    backupLabel: 'Backup',
    backupNote: 'Everything is saved on this device. A backup is a copy you can keep somewhere else.',
    backupButton: 'Make a backup',
    copyButton: 'Copy it',
    restoreLabel: 'Restore',
    restoreNote: 'Paste a backup below to bring it back. This replaces what is on this device.',
    restoreButton: 'Restore from this backup',
    restoreConfirm: 'Tap again to replace everything',
    restorePlaceholder: 'Paste a backup here',
    notSaving: 'This browser is blocking saved data, so changes last only until you close the page.',
    version: 'Step 2 · logging',
  },

  // Short messages that pop up at the bottom
  toasts: {
    soundOn: 'Sound is on.',
    soundOff: 'Sound is off.',
    copied: 'Backup copied.',
    copyFailed: 'Select the text and copy it by hand.',
    restored: 'Backup restored.',
    restoreBad: 'That doesn\'t look like a Composition backup.',
    restoreEmpty: 'Paste a backup first.',
  },
};
