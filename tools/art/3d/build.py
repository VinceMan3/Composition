"""Turn the final 3D renders into the muscle map files the app uses.

For each view (front, back), reads from FINAL/<view>/:
  ids.png, ids_deep.png, ids.json   which model piece is at each pixel
                                    (deep: with the sheets over the abs,
                                    rhomboids and outer quad hidden)
  s_shade.png, s_ink.png            the graphite layers from npr.py
and writes to the app's art/ folder:
  muscle-<view>-shade.webp   soft shading stencil (1120 x 1720)
  muscle-<view>-ink.webp     pencil lines stencil (2240 x 3440)
  muscle-<view>-map.svg      the tap shapes and the sheen, one shape per
                             piece of each of the 46 parts
Usage: python3 build.py FINAL_DIR APP_REPO
"""
import json
import os
import re
import sys

import cv2
import numpy as np
from PIL import Image

FINAL, REPO = sys.argv[1], sys.argv[2]
W, H = 560, 860   # the drawing's units in the app

# Model muscle names (without .l / .r) for each of our parts.
PART = {
    'chest-upper': ['Clavicular head of pectoralis major muscle'],
    'chest-middle': ['Sternocostal head of pectoralis major muscle'],
    'chest-lower': ['(Abdominal part of pectoralis major muscle)'],
    'front-delts': ['Clavicular part of deltoid muscle'],
    'side-delts': ['Acromial part of deltoid muscle'],
    'rear-delts': ['Scapular spinal part of deltoid muscle'],
    'biceps-long': ['Long head of biceps brachii'],
    'biceps-short': ['Short head of biceps brachii'],
    'brachialis': ['Brachialis muscle'],
    'triceps-long': ['Long head of triceps brachii'],
    'triceps-lateral': ['Lateral head of triceps brachii'],
    'triceps-medial': ['Medial head of triceps brachii', 'Anconeus muscle'],
    'brachioradialis': ['Brachioradialis muscle'],
    'wrist-flexors': ['Flexor carpi radialis', 'Palmaris longus muscle', 'Humeral head of flexor carpi ulnaris',
                      'Ulnar head of flexor carpi ulnaris', 'Superficial head of pronator teres', 'Deep head of pronator teres',
                      'Humero-ulnar head of flexor digitorum superficialis', 'Radial head of flexor digitorum superficialis',
                      'Flexor digitorum profundus', 'Flexor pollicis longus'],
    'wrist-extensors': ['Extensor carpi radialis longus', 'Extensor carpi radialis brevis', 'Extensor digitorum',
                        'Extensor digiti minimi', 'Humeral head of extensor carpi ulnaris', 'Ulnar head of extensor carpi ulnaris',
                        'Abductor pollicis longus', 'Extensor pollicis brevis', 'Extensor pollicis longus', 'Extensor indicis'],
    # The model's names for the top and bottom of the trapezius come out
    # swapped (its "descending" piece sits low on the back), so these follow
    # where each piece really is.
    'traps-upper': ['Ascending part of trapezius muscle'],
    'traps-middle': ['Transverse part of trapezius muscle'],
    'traps-lower': ['Descending part of trapezius muscle'],
    'rhomboids': ['Rhomboid major muscle', 'Rhomboid minor muscle'],
    'infraspinatus': ['Infraspinatus muscle'],
    'teres-minor': ['Teres minor muscle'],
    'teres-major': ['Teres major muscle'],
    'lats': ['Latissimus dorsi muscle'],
    'lower-back': ['Iliocostalis lumborum muscle', 'Iliocostalis thoracis muscle', 'Longissimus thoracis muscle',
                   'Spinalis thoracis muscle', 'Multifidus lumborum muscle', 'Multifidus thoracis muscle'],
    'abs': ['Rectus abdominis muscle', 'Linea alba', 'Pyramidalis muscle'],
    'external-oblique': ['External abdominal oblique muscle'],
    'serratus': ['Serratus anterior muscle'],
    'glute-max': ['Gluteus maximus muscle'],
    'glute-med': ['Gluteus medius muscle'],
    'rectus-femoris': ['Rectus femoris muscle'],
    'vastus-lateralis': ['Vastus lateralis muscle'],
    'vastus-medialis': ['Vastus medialis muscle'],
    'sartorius': ['Sartorius muscle'],
    'tfl': ['Tensor fasciae latae'],
    'hip-flexors': ['Iliacus muscle', 'Psoas major'],
    'biceps-femoris': ['Long head of biceps femoris', 'Short head of biceps femoris'],
    'semitendinosus': ['Semitendinosus muscle'],
    'semimembranosus': ['Semimembranosus muscle'],
    'adductor-longus': ['Adductor longus', 'Adductor brevis'],
    'adductor-magnus': ['Adductor magnus', '(Adductor minimus)'],
    'gracilis': ['Gracilis muscle'],
    'pectineus': ['Pectineus muscle'],
    'gastroc-medial': ['Medial head of gastrocnemius'],
    'gastroc-lateral': ['Lateral head of gastrocnemius'],
    'soleus': ['Soleus muscle'],
    'tibialis-anterior': ['Tibialis anterior muscle'],
}
ORDER = list(PART)
BY_NAME = {n: p for p, ns in PART.items() for n in ns}

# the part each group belongs to, from content/muscles.js
mj = open(os.path.join(REPO, 'content', 'muscles.js')).read()
GROUP = dict(re.findall(r"\{ id: '([a-z-]+)', group: '([a-z-]+)'", mj))
assert set(GROUP) == set(PART), set(GROUP) ^ set(PART)


def base(n):
    return n.rsplit('.', 1)[0] if n.rsplit('.', 1)[-1] in ('l', 'r') else n


def load_ids(path):
    a = np.asarray(Image.open(path)).astype(np.int64)
    v = (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]
    v[a[..., 3] == 0] = 0
    return v


def label(view):
    d = os.path.join(FINAL, view)
    names = json.load(open(os.path.join(d, 'ids.json')))
    lut = {int(k): base(n) for k, (n, _) in names.items()}
    full, deep = load_ids(os.path.join(d, 'ids.png')), load_ids(os.path.join(d, 'ids_deep.png'))
    def to_part(ids):
        out = np.zeros(ids.shape, np.int16)
        for k, n in lut.items():
            if n in BY_NAME:
                out[ids == k] = ORDER.index(BY_NAME[n]) + 1
        return out
    pf, pd = to_part(full), to_part(deep)
    fullname = np.vectorize(lambda k: lut.get(int(k), ''), otypes=[object])
    # only the see-through sheets need their names
    sheet = np.zeros(full.shape, np.int8)
    for k, n in lut.items():
        if n in ('External abdominal oblique muscle', 'Internal abdominal oblique muscle', 'Transversus abdominis muscle'):
            sheet[full == k] = 1
        elif 'part of trapezius muscle' in n:
            sheet[full == k] = 2
        elif n == 'Iliotibial tract':
            sheet[full == k] = 3
    for code, wanted in ((1, 'abs'), (2, 'rhomboids'), (3, 'vastus-lateralis'), (3, 'tfl')):
        idx = ORDER.index(wanted) + 1
        sel = (sheet == code) & (pd == idx)
        pf[sel] = idx
    # Tendons run on into the hands and feet: keep forearm parts above the
    # wrist and lower-leg parts above the ankle.
    hh, ww = pf.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    def pts(prefix):
        ks = [k for k, n in lut.items() if n.startswith(prefix)]
        return np.isin(full, ks) | np.isin(deep, ks)
    for side_left in (True, False):
        half = (xx < ww / 2) if side_left else (xx >= ww / 2)
        hum = pts('Humerus') & half
        rad = (pts('Radius') | pts('Ulna')) & half
        if hum.any() and rad.any():
            hy, hx = np.nonzero(hum)
            top = np.argmin(hy)
            sx_, sy_ = hx[top], hy[top]
            ry, rx = np.nonzero(rad)
            reach = np.hypot(rx - sx_, ry - sy_).max()
            far = np.hypot(xx - sx_, yy - sy_) > reach + 4
            for part in ('brachioradialis', 'wrist-flexors', 'wrist-extensors'):
                pf[(pf == ORDER.index(part) + 1) & far & half] = 0
        tib = (pts('Tibia') | pts('Fibula')) & half
        if tib.any():
            ankle = np.nonzero(tib)[0].max()
            for part in ('tibialis-anterior', 'gastroc-medial', 'gastroc-lateral', 'soleus'):
                pf[(pf == ORDER.index(part) + 1) & (yy > ankle - 6) & half] = 0
    np.save(os.path.join(d, 'parts.npy'), pf)
    return pf


def shapes(lab, view, other):
    """other: the other view's part labels, to tell a real part from a sliver."""
    h, w = lab.shape
    unit = (w / W) * (h / H)
    MIN_PX = 25 * unit   # about 25 square units in the drawing
    sx, sy = W / w, H / h
    paths = []
    present = set()
    for i, part in enumerate(ORDER, start=1):
        m = (lab == i).astype(np.uint8)
        if not m.any():
            continue
        # mostly seen from the other side: leave this view's slivers out
        if m.sum() < 0.08 * (other == i).sum():
            continue
        # tidy: close small gaps, drop crumbs
        k = np.ones((5, 5), np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, cc, stats, cent = cv2.connectedComponentsWithStats(m, 8)
        comps = []
        for c in range(1, n):
            comps.append((stats[c, cv2.CC_STAT_AREA], c, cent[c][0] < w / 2))
        if not comps:
            continue
        keep = []
        for side in (True, False):
            sc = [x for x in comps if x[2] == side]
            if not sc:
                continue
            biggest = max(a for a, _, _ in sc)
            # drop crumbs: a sliver of a part from the other side is no tap target
            keep += [c for a, c, _ in sc if a >= max(biggest * 0.15, MIN_PX)]
        for c in keep:
            cm = (cc == c).astype(np.uint8)
            cs, hier = cv2.findContours(cm, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
            d = []
            for ct in cs:
                if cv2.contourArea(ct) < 60:
                    continue
                ap = cv2.approxPolyDP(ct, 1.6, True).reshape(-1, 2)
                if len(ap) < 3:
                    continue
                d.append('M' + ' '.join(f'{x * sx:.1f} {y * sy:.1f}' for x, y in ap) + 'Z')
            if d:
                paths.append((part, ''.join(d)))
                present.add(part)
    return paths, present


def write_svg(paths, view):
    regions = ''.join(f'<path class="mm-muscle" data-group="{GROUP[p]}" data-part="{p}" fill-rule="evenodd" d="{d}"/>' for p, d in paths)
    gloss = ''.join(f'<path data-group="{GROUP[p]}" data-part="{p}" fill-rule="evenodd" d="{d}"/>' for p, d in paths)
    grad = (f'<radialGradient id="mm-{view}-gl" cx=".34" cy=".3" r=".62"><stop offset="0" stop-color="#fff" stop-opacity=".75"/>'
            '<stop offset=".18" stop-color="#fff" stop-opacity=".42"/><stop offset=".5" stop-color="#fff" stop-opacity=".1"/>'
            '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>')
    style = ('<style>.mm-muscle{fill:var(--mm-fill,transparent)}.mm-gloss{pointer-events:none}'
             f'.mm-gloss path{{fill:url(#mm-{view}-gl);opacity:0}}</style>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" class="mm mm-{view}">{style}'
            f'<defs>{grad}</defs><g class="mm-regions">{regions}</g><g class="mm-gloss">{gloss}</g></svg>')


def stencil(path, size, out):
    dark = Image.open(path).convert('L').resize(size, Image.LANCZOS)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    img.putalpha(dark)
    img.save(out, 'WEBP', quality=80, alpha_quality=85, method=6)
    return os.path.getsize(out) // 1024


views = {}
labels = {v: label(v) for v in ('front', 'back')}
for view in ('front', 'back'):
    lab = labels[view]
    paths, present = shapes(lab, view, labels['back' if view == 'front' else 'front'])
    views[view] = present
    art = os.path.join(REPO, 'art')
    svg = write_svg(paths, view)
    open(os.path.join(art, f'muscle-{view}-map.svg'), 'w').write(svg)
    d = os.path.join(FINAL, view)
    a = stencil(os.path.join(d, 's_shade.png'), (1120, 1720), os.path.join(art, f'muscle-{view}-shade.webp'))
    # the lit side of the body, for the dark garage paper (chalk on a blackboard)
    A = np.asarray(Image.open(os.path.join(d, 'shade.png')).convert('RGBA')).astype(np.float32)[..., 3] / 255
    tone = np.asarray(Image.open(os.path.join(d, 's_shade.png')).convert('L')).astype(np.float32) / 255
    light = np.clip(A * (1 - tone * 1.15), 0, 1) ** 1.3
    Image.fromarray((light * 255).astype(np.uint8)).save(os.path.join(d, 's_light.png'))
    stencil(os.path.join(d, 's_light.png'), (1120, 1720), os.path.join(art, f'muscle-{view}-light.webp'))
    b = stencil(os.path.join(d, 's_ink.png'), (2240, 3440), os.path.join(art, f'muscle-{view}-ink.webp'))
    print(f'{view}: {len(paths)} shapes, {len(present)} parts, svg {len(svg) // 1024} KB, shade {a} KB, ink {b} KB')

both = views['front'] & views['back']
print('VIEWS', json.dumps({p: ('both' if p in both else 'front' if p in views['front'] else 'back' if p in views['back'] else 'none') for p in ORDER}))
