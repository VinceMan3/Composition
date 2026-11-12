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

## Change how fast pages turn

Open `styles/motion.css` and change the number on this line near the top:

    :root { --flip: 340ms; }

Bigger is slower. 1000ms is one second.

## If something breaks

Every change on GitHub is saved in the file's history. Open the file, click
"History", find the last version that worked, and restore it. Or tell Claude
what you changed and what happened.

