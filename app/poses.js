// Picks the pen sketch for the corner of a page: the pose for the muscle
// group the page works most, counted by sets. A page with no lifts yet goes
// by its title ("Leg day"). The drawings are listed in content/poses.js.

import { POSES, DEFAULT_POSE } from '../content/poses.js';
import { art } from './ui.js';
import { findLift } from './log.js';

// Sizes of each drawing, so the page does not jump while it loads.
const SIZES = {
  'sketch-front.webp': [640, 587],
  'sketch-back.webp': [640, 587],
  'sketch-arm.webp': [540, 605],
};

// Words in a title that point to a body part.
const TITLE_WORDS = [
  [/chest|push|bench/i, 'Chest'],
  [/back|pull|row/i, 'Back'],
  [/shoulder|delt|press/i, 'Shoulders'],
  [/arm|bicep|tricep|gun/i, 'Arms'],
  [/leg|squat|quad|ham|glute/i, 'Legs'],
  [/core|abs?\b/i, 'Core'],
];

export function poseFor(data, page) {
  const counts = {};
  for (const entry of (page && page.lifts) || []) {
    const group = findLift(data, entry.liftId).group;
    if (!POSES[group]) continue;
    counts[group] = (counts[group] || 0) + Math.max(1, entry.sets.length);
  }
  const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
  if (top) return POSES[top[0]];
  const hit = TITLE_WORDS.find(([pattern]) => pattern.test((page && page.title) || ''));
  return hit ? POSES[hit[1]] : DEFAULT_POSE;
}

// The drawing itself, ready to drop into a page.
export function poseSketch(data, page) {
  const file = poseFor(data, page);
  const [w, h] = SIZES[file] || [640, 600];
  return art(file, `sketch sketch-pose ${file.replace('.webp', '').replace('.png', '')}`, w, h);
}
