# Composition

A training log that looks and feels like an old spiral notebook.

This is a plain web app: HTML, CSS and JavaScript, with nothing to install and
no build step. Put the folder on any web host and it runs.

## Where things live

| Folder | What is in it | Safe to edit by hand? |
| --- | --- | --- |
| `content/` | Colors, wording, the lift list, the cardio list and the daily verses | Yes. See `HOW-TO-EDIT.md` |
| `art/` | Stickers, sketches, paper texture | Yes, swap a picture for one with the same name |
| `styles/` | How things look: layout, type, the page flip | With care |
| `app/` | How things work: pages, saving, sound | With care |
| `index.html` | The frame: cover strip, rings, tabs | With care |

## How the app fits together

- `app/main.js` starts everything and hands each page what it needs.
- `app/router.js` turns pages. The address ends in a page name such as
  `#cover` or `#today`; the list of pages is `ROUTES` at the top of the file.
- `app/flip.js` builds the bending sheet for the page flip; the timing is in
  `styles/motion.css`.
- `app/pages/` has one file per page. Each exports `render(el, ctx)` and
  draws itself into `el`.
- `app/log.js` is the arithmetic behind a workout page: last time's numbers,
  estimated maxes, plates, records, filing. It never touches the screen.
- `app/awards.js` lists every sticker and the test that earns it.
- `app/rest.js` is the rest timer above the tabs.
- `app/store.js` saves to the device and makes backups.
- `app/sound.js` builds every sound from scratch; there are no sound files.
- `app/ui.js` has small helpers the pages share.

To add a page: add a file in `app/pages/`, list it in `PAGES` in
`app/main.js`, and add it to `ROUTES` in `app/router.js`.

## What gets saved

One object, kept in the browser on the device (see `app/store.js`):

- `settings`: sound, units, default rest length
- `draft`: the page being written today, or nothing
- `pages`: every filed page, oldest first
- `customLifts`: lifts the person added themselves
- `earned`: which stickers have been earned, and when
- `stickers`: where each sticker sits on the cover

## Running it on your own computer

Browsers will not load the app by double-clicking `index.html`; it needs a
small local server. With Python installed, open a terminal in this folder and
run:

    python3 -m http.server 8000

Then visit http://localhost:8000 in a browser.

## Build steps so far

1. Foundation: the notebook frame, five tabs, page flips, sounds, saving, backup. (done)
2. Logging: today's page, add a lift, cardio, rest timer, filing a page, the daily verse,
   movable stickers and the first earned stickers. (done)
3. Looking back: the notebook, lift library, one lift's history.
4. Cover: this week at a glance, more stickers and sketches.
5. Stats: the Big Three, records, charts, calendar, Wilks and DOTS.
6. Polish: settings, lb and kg, the dim garage look, desktop layout, install, offline.
7. New sections: programs, food log, muscle map, lessons, meet day.
8. Launch: accounts and sync, privacy page, app stores.
