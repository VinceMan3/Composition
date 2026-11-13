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
- `app/strength.js` is the Stats arithmetic: weigh-ins, best lifts, Wilks,
  DOTS and strength levels. `app/chart.js` draws the hand-plotted charts.
- `app/rest.js` is the rest timer above the tabs.
- `app/units.js` turns pounds into kilograms and back; everything is worked
  out in pounds.
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
- `weighins`: bodyweight in pounds by day
- `maxes`: one-rep maxes logged straight in, with their unit and day
- `liftNotes`: a standing note for each lift

## The live app

GitHub hosts the app for free from the `main` branch. Once hosting is on
(repository Settings, then Pages, then "Deploy from a branch", `main`, `/`),
it lives at https://vinceman3.github.io/Composition/ and updates a minute or
two after each merge. On a phone, open it and choose "Add to Home Screen".

It works offline: `sw.js` keeps a copy of the app on the phone and refreshes
it in the background, so a new version shows on the launch after it is
merged. Every file in `art/` must be listed in `ART` at the top of `sw.js`
(a test checks this).

## Running it on your own computer

Browsers will not load the app by double-clicking `index.html`; it needs a
small local server. With Python installed, open a terminal in this folder and
run:

    python3 -m http.server 8000

Then visit http://localhost:8000 in a browser.

## Checks

`tools/` holds the browser checks, the preview builder and the scripts that
drew the art. See `tools/README.md`.

## Build steps so far

1. Foundation: the notebook frame, five tabs, page flips, sounds, saving, backup. (done)
2. Logging: today's page, add a lift, cardio, rest timer, filing a page, the daily verse,
   movable stickers and the first earned stickers. (done)
3. Looking back: open and fix filed pages, the lift library, one lift's history,
   lift notes, this week, the boxing round timer. (done)
4. Art: a pen sketch pose for every muscle group, for the corners of the pages.
5. Stats: the Big Three with strength levels, total, Wilks and DOTS, a score
   calculator, charts, weigh-ins, the training calendar, records. (done)
6. Polish: lb and kg, the dim garage look, logging maxes directly, the Big Three
   redesign, a home-screen icon, working offline. (done)
7. New sections: muscle map first, then programs, food log, lessons, meet day.
8. Launch: accounts and sync, privacy page, app stores.

## Ideas for later

- A learn section: anatomy and physiology trivia and quizzes.
- Games for rest breaks, like a retro boxing game.
- Trainer mode: one notebook per client, with plans for each.
- A news page: app updates and new features, plus news, events and
  discoveries from bodybuilding and powerlifting.
