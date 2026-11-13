// The muscle map's lookups: which parts of the map a lift trains, and which
// lifts train a part. The words and the name list live in content/muscles.js.

import { GROUPS, PARTS, PICK } from '../content/muscles.js';

export { GROUPS, PARTS, PICK };

export const groupById = new Map(GROUPS.map(g => [g.id, g]));
export const partById = new Map(PARTS.map(p => [p.id, p]));

// "Front delts, triceps" -> ['front delts', 'triceps']
export function splitNames(text) {
  return String(text || '').split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
}

// Each lift-list name and the parts it counts toward, in map order.
const byName = new Map();
for (const part of PARTS) {
  for (const name of splitNames(part.names)) {
    if (!byName.has(name)) byName.set(name, []);
    byName.get(name).push(part.id);
  }
}

// The parts one name counts toward; none if the name is unknown.
export function partsOfName(name) {
  return byName.get(String(name).trim().toLowerCase()) || [];
}

export function knowsName(name) {
  return byName.has(String(name).trim().toLowerCase());
}

// The parts a lift trains: works are its main muscles, helps its helpers.
// A part that is both counts as works.
export function partsFor(lift) {
  const works = [...new Set(splitNames(lift && lift.works).flatMap(partsOfName))];
  const helps = [...new Set(splitNames(lift && lift.helps).flatMap(partsOfName))].filter(id => !works.includes(id));
  return { works, helps };
}

// The lifts that train a part, main muscle first.
export function liftsFor(partId, lifts) {
  const main = [], help = [];
  for (const lift of lifts) {
    const { works, helps } = partsFor(lift);
    if (works.includes(partId)) main.push(lift);
    else if (helps.includes(partId)) help.push(lift);
  }
  return { main, help };
}

// Every name in these lifts that does not count toward any part.
export function unknownNames(lifts) {
  const out = new Set();
  for (const lift of lifts) {
    for (const name of [...splitNames(lift.works), ...splitNames(lift.helps)]) {
      if (!knowsName(name)) out.add(name);
    }
  }
  return [...out];
}
