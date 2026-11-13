# How to edit Composition yourself

Everything meant for you to change lives in the `content/` folder. You can
edit these files right on the GitHub website: open the file, click the pencil
icon, make the change, then click "Commit changes". The live app updates a
minute or two later.

## Change a color

Open `content/colors.css`. Each line is one color with a note saying where it
is used:

    --blue: #A9CBE0;          /* baby blue cover */

Change the code after the colon (keep the `#` and the semicolon). To find a
new code, search the web for "color picker".

## Change the dim garage colors

Below the main colors in `content/colors.css` is a second block,
`:root[data-look="garage"]`. Those are the same names with the colors used
when the dim garage look is switched on under More. In that look the names
keep their jobs, not their colors: `--blue` is the cover, which is maroon
there, and `--paper` is the page, which is gunmetal grey.

## Change wording

Open `content/wording.js`. Change only the text between the quotes:

    cardTitle: 'Open to today',

Three rules keep it working:

1. Keep the quotes at both ends and the comma after.
2. If your text has an apostrophe, put a backslash before it: `'today\'s page'`
3. Leave the names on the left (like `cardTitle`) alone.

The tab names along the bottom are in the `tabs` section near the top.

## Add or rename a lift

Open `content/lifts.js`. Each line is one lift:

    { id: 'bench-press', name: 'Bench Press', group: 'Chest', gear: 'Barbell', works: 'chest', helps: 'front delts, triceps' },

To add one, copy a line, paste it below, and change the words between the
quotes. Give it its own `id` (lowercase letters and dashes). You can rename a
lift any time by changing `name`, but never change an `id` after you have
logged that lift: your history is filed under it.

`gear: 'Barbell'` is what switches on the plate line under a set.

`works` and `helps` are the muscles it trains, and they decide what lights up
on the muscle map. Use names the map knows (they are listed in
`content/muscles.js`); a check fails if a name does not count toward any part.

## Change what the muscle map says

Open `content/muscles.js`. Each part of the map is one entry:

    { id: 'lats', group: 'lats', name: 'Lats', view: 'both',
      names: 'lats',
      does: "Pull your arm down and back toward your hip...",
      fact: "They're the broadest muscle in your body..." },

Change `name`, `does` and `fact` freely. These use double quotes, so
apostrophes need no backslash. `names` lists the lift-list muscle names that
count toward the part; to teach the map a new name, add it here (for example
`'chest, lower chest'`). Leave `id`, `group` and `view` alone: they match the
drawings.

`PICK` at the bottom is the list of muscles you can choose from when you write
in a lift of your own.

## Add a kind of cardio

Open `content/cardio.js`. Each line is one kind:

    { id: 'running', name: 'Running', fields: ['miles', 'minutes'] },

`fields` are the boxes to fill in: any of `'rounds'`, `'minutes'`, `'miles'`,
`'meters'`. Add `boxing: true` to mark it in purple and count it toward the
boxing stickers.

## Rename a sticker or change how it is earned

The stickers are listed in `app/awards.js`. The `name` and `how` text are safe
to change. The numbers in the `earned` line are the bar to clear: for example
`>= 225` on the two plate bench. Leave the rest of that line alone.

## Add a verse

Open `content/verses.js`. Each line is one verse:

    { ref: 'Philippians 4:13', text: 'I can do all things through Christ which strengtheneth me.' },

Copy a line, paste it anywhere in the list, and change the reference and the
text. The cover shows one a day, working down the list and starting over at
the end, so the more you add, the longer before one repeats.

## Change the page titles it suggests

In `content/wording.js`, find `titleIdeas` and edit the list:

    titleIdeas: ['Chest day', 'Back day', 'Leg day', 'Shoulders', 'Arms', 'Push', 'Pull'],

## Swap a sticker or sketch

The pictures are in `art/`. To replace one, upload a new picture with exactly
the same file name (for example `sticker-gloves.png`). Files with a
see-through background look best.

Adding a brand new drawing (not a swap)? Also add its name to the `ART`
list at the top of `sw.js`, so it is saved for offline use.

## Change the strength levels

Open `content/standards.js`. Each lift has five numbers: where Novice,
Intermediate, Advanced, Elite and World class begin, as a multiple of
bodyweight for a lifter at the reference bodyweight (176 lb for men, 132 lb
for women). The app scales them for every other bodyweight. Raise a number
to make that level harder to reach.

## Choose which pose goes with which muscle

Open `content/poses.js`. Each line pairs a body part with a drawing in `art/`:

    Chest: 'sketch-front.webp',     // to draw: most muscular

A page shows the pose for the body part it works most. When a new drawing
arrives, put it in `art/` and change the file name on its line.

## Change how fast pages turn

Open `styles/motion.css` and change the number on this line near the top:

    :root { --flip: 290ms; --flip-quick: 150ms; }

`--flip` is the cover; `--flip-quick` is every other page. Bigger is slower.
1000ms is one second.

## If something breaks

Every change on GitHub is saved in the file's history. Open the file, click
"History", find the last version that worked, and restore it. Or tell Claude
what you changed and what happened.

