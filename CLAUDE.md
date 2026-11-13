# Working on Composition

Composition is Vince's training log, styled after his Papa Al's baby-blue
spiral composition notebook. It is headed for a public launch, mobile first.
Read `README.md` for how the app fits together and `tools/README.md` for the
checks.

## How Vince wants to work

- Ask before assuming. He wants real questions on anything that is his call
  (look, wording, what counts as earned), a few at a time, numbered.
- Plan before building on anything big. Get the plan approved first.
- No em dashes anywhere: app wording, docs, commit messages, replies. Use
  commas, colons or semicolons.
- Plain, friendly wording in the app and in code comments. He edits
  `content/` by hand, so keep it readable for a non-programmer.
- Stickers and awards should be hard to earn.

## Rules of the codebase

- Plain HTML, CSS and ES modules. No framework, no build step for the app.
- Every word the app shows lives in `content/wording.js`.
- Every color is a token in `content/colors.css`. The dim garage look is the
  `:root[data-look="garage"]` block there: gunmetal paper, maroon cover,
  maroon in place of baby blue, dark greys and black, hints of deep purple.
  New colors need a garage value too, and must stay readable on both papers.
- Everything is worked out in pounds; `app/units.js` converts for display.
  Past pages stay in the unit they were written in.
- Any new file in `art/` must be added to `ART` in `sw.js` (a check enforces it).
- Design for a 390 px wide phone first.
- Satisfying sound and motion matter: sounds are built in `app/sound.js`,
  inner pages turn fast (180 ms), the cover curls (300 ms).

## Workflow for each round

1. Branch from `main`, build, then run the checks (all must pass) on the app
   and on the preview build. Add checks for anything new.
2. Rebuild the preview (`python3 tools/build-preview.py`) and republish it to
   the existing Claude preview page so Vince can try it on his phone.
3. Push and open a pull request. Vince merges it himself.
4. GitHub Pages serves `main` at https://vinceman3.github.io/Composition/
   once he turns it on in Settings.
