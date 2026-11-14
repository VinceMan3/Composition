// The muscle map drawings, front and back, built for speed. Each view is a
// stack of layers (made by tools/art/mapimages.py):
//   0. the lit side of the body, a picture used as a stencil in --map-light
//      (only the dark garage paper shows it; on paper it is see-through)
//   1. the tap shapes (a small SVG): a picked muscle is filled red here
//   2. the soft shading, a picture used as a stencil in --map-shade
//   3. the pencil lines, a picture used as a stencil in --map-ink
//   4. the sheen on a picked muscle (the same small SVG's gloss)
// The red sits under the shading and lines, so the drawing shows through it.
// Each view is fetched and built once, then kept and reused.

export const W = 560, H = 860; // the drawing's size, in its own units

const NS = 'http://www.w3.org/2000/svg';
const kept = new Map();
const loading = new Map();
const svgText = new Map();

function layer(cls, view, kind) {
  const el = document.createElement('div');
  el.className = `mm-layer ${cls}`;
  // A full address: a link inside a CSS variable would otherwise be read
  // from the stylesheet's folder instead of the page's.
  el.style.setProperty('--mm-img', `url("${new URL(`art/muscle-${view}-${kind}.webp`, document.baseURI).href}")`);
  return el;
}

// Wait for the pictures so the figure appears whole, not in pieces.
function preload(view) {
  return Promise.all(['light', 'shade', 'ink'].map(kind => new Promise(resolve => {
    const img = new Image();
    img.onload = img.onerror = () => resolve();
    img.src = `art/muscle-${view}-${kind}.webp`;
  })));
}

function fetchSvg(view) {
  if (svgText.has(view)) return Promise.resolve(svgText.get(view));
  return fetch(`art/muscle-${view}-map.svg`)
    .then(r => {
      if (!r.ok) throw new Error(`muscle-${view}-map.svg: ${r.status}`);
      return r.text();
    })
    .then(text => { svgText.set(view, text); return text; });
}

function parse(text) {
  const holder = document.createElement('div');
  holder.innerHTML = text;
  const svg = holder.querySelector('svg');
  svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('focusable', 'false');
  return svg;
}

// Resolves to { el, view, pick, partBox } for 'front' or 'back'.
export function loadFigure(view) {
  if (kept.has(view)) return Promise.resolve(kept.get(view));
  if (!loading.has(view)) {
    loading.set(view, Promise.all([fetchSvg(view), preload(view)]).then(([text]) => {
      const taps = parse(text);
      taps.classList.add('mm-taps');
      taps.querySelector('.mm-gloss').remove();
      taps.querySelector('defs').remove();
      const sheen = parse(text);
      sheen.classList.add('mm-sheen');
      sheen.querySelector('.mm-regions').remove();

      const el = document.createElement('div');
      el.className = `mm-figure mm-${view}`;
      el.setAttribute('aria-hidden', 'true');
      el.append(layer('mm-light', view, 'light'), taps, layer('mm-shade', view, 'shade'), layer('mm-ink', view, 'ink'), sheen);

      let picked = [];
      const fig = {
        el,
        view,
        // Color one part red with its sheen; '' clears it.
        pick(partId) {
          for (const p of picked) {
            if (p.classList.contains('mm-muscle')) p.style.removeProperty('--mm-fill');
            else p.style.opacity = '';
          }
          picked = partId
            ? [...taps.querySelectorAll(`.mm-muscle[data-part="${partId}"]`), ...sheen.querySelectorAll(`.mm-gloss path[data-part="${partId}"]`)]
            : [];
          for (const p of picked) {
            if (p.classList.contains('mm-muscle')) p.style.setProperty('--mm-fill', 'var(--map-red)');
            else p.style.opacity = '1';
          }
        },
        // The box around a part in drawing units; a part on both sides of the
        // body gives the one on the viewer's left.
        partBox(partId) {
          const shapes = [...taps.querySelectorAll(`.mm-muscle[data-part="${partId}"]`)];
          if (!shapes.length) return null;
          const boxes = shapes.map(s => s.getBBox());
          const x0 = Math.min(...boxes.map(b => b.x)), x1 = Math.max(...boxes.map(b => b.x + b.width));
          const y0 = Math.min(...boxes.map(b => b.y)), y1 = Math.max(...boxes.map(b => b.y + b.height));
          // Parts that meet in the middle (chest, abs, traps) show both sides.
          if (x1 - x0 < W * 0.42) return { x: x0, y: y0, width: x1 - x0, height: y1 - y0 };
          // Otherwise the one on the viewer's left.
          const left = boxes.filter(b => b.x + b.width / 2 < W / 2);
          const pick = left.length ? left : boxes;
          const lx0 = Math.min(...pick.map(b => b.x)), lx1 = Math.max(...pick.map(b => b.x + b.width));
          const ly0 = Math.min(...pick.map(b => b.y)), ly1 = Math.max(...pick.map(b => b.y + b.height));
          return { x: lx0, y: ly0, width: lx1 - lx0, height: ly1 - ly0 };
        },
        shapes(partId) {
          return [...taps.querySelectorAll(`.mm-muscle[data-part="${partId}"]`)];
        },
        // A small copy of one part for a card's close-up: its red shape and sheen.
        partCopy(partId) {
          const svg = document.createElementNS(NS, 'svg');
          svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
          svg.setAttribute('class', 'mm-cu-red');
          for (const s of this.shapes(partId)) {
            const c = s.cloneNode(false);
            c.style.setProperty('--mm-fill', 'var(--map-red)');
            svg.append(c);
          }
          const top = sheen.cloneNode(false);
          top.setAttribute('class', 'mm-cu-sheen');
          top.append(sheen.querySelector('defs').cloneNode(true));
          const g = document.createElementNS(NS, 'g');
          g.setAttribute('class', 'mm-gloss');
          for (const s of sheen.querySelectorAll(`.mm-gloss path[data-part="${partId}"]`)) {
            const c = s.cloneNode(false);
            c.style.opacity = '1';
            g.append(c);
          }
          top.append(g);
          // The copied sheen gradient needs its own id so it never clashes.
          const grad = top.querySelector('[id]');
          if (grad) {
            const id = `${grad.id}-cu`;
            grad.id = id;
            for (const p of g.children) p.style.fill = `url(#${id})`;
          }
          return [svg, top];
        },
      };
      kept.set(view, fig);
      return fig;
    }).finally(() => loading.delete(view)));
  }
  return loading.get(view);
}

// A card's close-up: the same layers, cropped around one part.
// crop is { x, y, w, h } in drawing units.
export function closeUp(fig, partId, crop) {
  const box = document.createElement('div');
  box.className = 'mm-closeup';
  const inner = document.createElement('div');
  inner.className = 'mm-cu-in';
  inner.dataset.view = fig.view;
  const [red, sheen] = fig.partCopy(partId);
  inner.append(layer('mm-light', fig.view, 'light'), red, layer('mm-shade', fig.view, 'shade'), layer('mm-ink', fig.view, 'ink'), sheen);
  box.append(inner);
  const place = c => {
    inner.style.width = `${(W / c.w) * 100}%`;
    inner.style.height = `${(H / c.h) * 100}%`;
    inner.style.left = `${(-c.x / c.w) * 100}%`;
    inner.style.top = `${(-c.y / c.h) * 100}%`;
  };
  if (crop) place(crop);
  return { el: box, place };
}

// Work out a crop around a part for a window with this width-to-height shape.
// fill is how much of the window the part takes up.
export function cropFor(fig, partId, aspect, fill = 0.62) {
  const b = fig.partBox(partId);
  if (!b) return { x: 0, y: 0, w: W, h: H };
  let h = Math.max(b.height / fill, b.width / fill / aspect, 130);
  let w = h * aspect;
  if (w > W) { w = W; h = w / aspect; }
  if (h > H) { h = H; w = h * aspect; }
  const x = Math.min(Math.max(b.x + b.width / 2 - w / 2, 0), W - w);
  const y = Math.min(Math.max(b.y + b.height / 2 - h / 2, 0), H - h);
  return { x, y, w, h };
}
