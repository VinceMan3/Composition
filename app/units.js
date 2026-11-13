// Pounds or kilograms. Everything is worked out in pounds; this turns
// pounds into whichever unit is picked under More, and back.
// Pages keep the unit they were written in.

import { tidy, num } from './log.js';

export const LB_PER_KG = 2.20462262;

export function unitOf(data) {
  return data.settings.units === 'kg' ? 'kg' : 'lb';
}

// Pounds into the unit, rounded: whole pounds, or kilograms to the half.
export function fromLb(lb, unit) {
  if (unit === 'kg') return Math.round((num(lb) / LB_PER_KG) * 2) / 2;
  return Math.round(num(lb) * 10) / 10;
}

export function toLbFrom(value, unit) {
  return unit === 'kg' ? num(value) * LB_PER_KG : num(value);
}

// "245" in the picked unit, for showing.
export function show(lb, unit) {
  return tidy(fromLb(lb, unit));
}
