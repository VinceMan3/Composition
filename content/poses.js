/*
  POSES
  Safe to edit. Which pen sketch sits in the corner of a page, by the muscle
  group the page works most. Each body part names a drawing in the art folder.

  The poses still to be drawn are noted beside each line. When a new drawing
  arrives, put it in art/ and change the file name here.
*/
export const POSES = {
  Chest: 'sketch-front.webp',     // to draw: most muscular
  Back: 'sketch-back-hand.webp',  // back double biceps, drawn by hand in ballpoint
  Shoulders: 'sketch-front.webp', // to draw: front lat spread
  Arms: 'sketch-arm.webp',        // flexed arm
  Legs: 'sketch-front.webp',      // to draw: quad stomp
  Core: 'sketch-front.webp',      // to draw: abdominal and thigh
  Power: 'sketch-back-hand.webp', // to draw: side chest
};

// The sketch for a page with no lifts on it yet.
export const DEFAULT_POSE = 'sketch-front.webp';
