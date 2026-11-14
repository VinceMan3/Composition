// The two muscle map drawings, front and back. They are put straight into the
// page (not shown as pictures) so each muscle can be tapped and colored.
// Each drawing is fetched and built once, then kept and reused, because they
// are big: building one again every time the tab opens would be slow.

const kept = new Map();
const loading = new Map();

// Resolves to the <svg> for 'front' or 'back'. Everything drawn sits in one
// group, id "mmfig-front" or "mmfig-back", so a trading card can show a
// close-up of the same drawing with <use>.
export function loadFigure(view) {
  if (kept.has(view)) return Promise.resolve(kept.get(view));
  if (!loading.has(view)) {
    loading.set(view, fetch(`art/muscle-${view}.svg`)
      .then(r => {
        if (!r.ok) throw new Error(`muscle-${view}.svg: ${r.status}`);
        return r.text();
      })
      .then(text => {
        const holder = document.createElement('div');
        holder.innerHTML = text;
        const svg = holder.querySelector('svg');
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.id = `mmfig-${view}`;
        for (const child of [...svg.childNodes]) {
          if (child.nodeName === 'defs' || child.nodeName === 'style') continue;
          group.append(child);
        }
        svg.append(group);
        svg.setAttribute('aria-hidden', 'true');
        svg.setAttribute('focusable', 'false');
        kept.set(view, svg);
        return svg;
      })
      .finally(() => loading.delete(view)));
  }
  return loading.get(view);
}

// Color one part red with its sheen, or clear every part when partId is empty.
export function pick(svg, partId) {
  for (const el of svg.querySelectorAll('.mm-muscle')) {
    if (el.dataset.part === partId) el.style.setProperty('--mm-fill', 'var(--map-red)');
    else el.style.removeProperty('--mm-fill');
  }
  for (const el of svg.querySelectorAll('.mm-gloss path')) {
    el.style.opacity = el.dataset.part === partId ? '1' : '';
  }
}

// The box around a part in the drawing's own units, for the card close-up.
// A part on both sides of the body uses the one on the viewer's left.
export function partBox(svg, partId) {
  const shapes = [...svg.querySelectorAll(`.mm-muscle[data-part="${partId}"]`)];
  if (!shapes.length) return null;
  const boxes = shapes.map(s => s.getBBox()).sort((a, b) => a.x - b.x);
  return boxes[0];
}
