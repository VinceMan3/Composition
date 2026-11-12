/*
  CARDIO
  Safe to edit. One kind of cardio per line. To add one, copy a line, paste
  it below, and change the words between the quotes. Give it its own id
  (lowercase letters and dashes) and never change an id once you have logged it.

  fields  are the boxes you fill in: 'rounds', 'minutes', 'miles' or 'meters'
  boxing  true marks it in purple and counts it toward the boxing stickers
*/
export const CARDIO = [
  { id: 'heavy-bag', name: 'Heavy Bag', fields: ['rounds', 'minutes'], boxing: true },
  { id: 'speed-bag', name: 'Speed Bag', fields: ['rounds', 'minutes'], boxing: true },
  { id: 'shadowboxing', name: 'Shadowboxing', fields: ['rounds', 'minutes'], boxing: true },
  { id: 'mitts', name: 'Mitt Work', fields: ['rounds', 'minutes'], boxing: true },
  { id: 'sparring', name: 'Sparring', fields: ['rounds', 'minutes'], boxing: true },
  { id: 'jump-rope', name: 'Jump Rope', fields: ['minutes'] },
  { id: 'running', name: 'Running', fields: ['miles', 'minutes'] },
  { id: 'cycling', name: 'Cycling', fields: ['miles', 'minutes'] },
  { id: 'rowing', name: 'Rowing', fields: ['meters', 'minutes'] },
  { id: 'walking', name: 'Walking', fields: ['miles', 'minutes'] },
  { id: 'stairs', name: 'Stairs', fields: ['minutes'] },
  { id: 'other-cardio', name: 'Other Cardio', fields: ['minutes'] },
];

// The word printed beside each box.
export const CARDIO_UNITS = {
  rounds: 'rounds',
  minutes: 'min',
  miles: 'mi',
  meters: 'm',
};
