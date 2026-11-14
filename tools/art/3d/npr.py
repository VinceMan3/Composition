"""Turn the 3D renders (shade.png, ids.png) into a graphite pencil drawing.

Outputs (in the work folder):
  g_shade.png   soft tone, as darkness (white = paper, black = full graphite)
  g_ink.png     pencil lines and hatching, as darkness
  g_preview.png the two together on paper, for looking at
"""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image

WORK = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('OUT', '/home/claude/3d/work/')
rng = np.random.default_rng(7)
SOFT = os.environ.get('STYLE') == 'soft'
TAG = 's_' if SOFT else 'g_'

shade = np.asarray(Image.open(WORK + 'shade.png').convert('RGBA')).astype(np.float32) / 255
idimg = np.asarray(Image.open(WORK + 'ids.png')).astype(np.int64)
ids = (idimg[..., 0] << 16) | (idimg[..., 1] << 8) | idimg[..., 2]
ids[idimg[..., 3] == 0] = 0
A = shade[..., 3]
L = shade[..., :3].mean(axis=2)
H, W = L.shape
inside = A > 0.5
S = W / 1300.0   # every size below was tuned at 1300 pixels wide


def smooth(x, s, scaled=True):
    return cv2.GaussianBlur(x, (0, 0), s * (S if scaled else 1))


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ----- tone: how dark the graphite is, from the light -----
lo, hi = np.percentile(L[inside], [1, 99.5])
T = 1 - np.clip((L - lo) / (hi - lo), 0, 1)        # 0 lit, 1 deepest shadow
T = T ** 0.95
# grooves and creases: darker than their surroundings (the lines between
# the abs, under the pecs, between the heads of a muscle)
cavity = np.clip((smooth(L, 7) - L) * 9, 0, 1)
# the core shadow: the darkest band just where the light turns away, as
# pencil artists draw it (the shadow lightens again toward the far edge)
core = np.exp(-((T - 0.58) / 0.16) ** 2) * 0.22
T = np.clip(T * 1.0 + cavity * 0.8 + core, 0, 1)
T *= A
tone = smooth(T, 1.8 if SOFT else 1.2) * (0.94 if SOFT else 0.7)                        # the soft blended layer

# ----- hatching along each muscle -----
gx_, gy_ = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
SPACING = 5.2 * S   # pixels between strokes

def lowfreq(scale, amp):
    n = smooth(rng.standard_normal((H, W)).astype(np.float32), scale)
    return n * amp / (np.abs(n).max() + 1e-6)

def hatch_field(angle, spacing=SPACING):
    """Parallel pencil strokes at one angle: how close each pixel is to a
    stroke's middle (1) or between strokes (0), and how heavy that stroke is."""
    nx, ny = -np.sin(angle), np.cos(angle)          # across the strokes
    tx, ty = np.cos(angle), np.sin(angle)           # along the strokes
    u = (gx_ * nx + gy_ * ny) / spacing + lowfreq(60, 0.35)   # a slight wander
    idx = np.floor(u)
    frac = u - idx
    dist = np.abs(frac - 0.5) * 2                    # 0 at a stroke's middle
    along = gx_ * tx + gy_ * ty
    # each stroke has its own weight, and lifts off now and then
    seed = (idx * 12.9898) % 1000
    weight = 0.6 + 0.4 * np.abs(np.sin(seed * 78.233))
    lift = np.sin(along / ((38 + 30 * np.abs(np.sin(seed))) * S) + seed * 3.1)
    on = smoothstep(-0.75, -0.35, lift)
    return dist, weight * on

ANG = np.linspace(0, np.pi, 12, endpoint=False)
fields = [hatch_field(a) for a in ANG]

# each region's long direction, from the shape of its pixels
angle_idx = np.full((H, W), -1, np.int32)
for v in np.unique(ids):
    if v == 0:
        continue
    m = (ids == v).astype(np.uint8)
    mo = cv2.moments(m, True)
    if mo['m00'] < 30 * S * S:
        continue
    th = 0.5 * np.arctan2(2 * mo['mu11'], mo['mu20'] - mo['mu02'])
    angle_idx[m > 0] = int(round((th % np.pi) / np.pi * 12)) % 12

dist = np.ones((H, W), np.float32)
wgt = np.zeros((H, W), np.float32)
for i in range(12):
    sel = angle_idx == i
    dist[sel] = fields[i][0][sel]
    wgt[sel] = fields[i][1][sel]
Tm = smooth(T, 2.5)
# darker tone: the stroke gets wider
width = smoothstep(0.05, 0.95, Tm) * 0.85
hatch_ink = smoothstep(width + 0.12, width - 0.05, dist) * wgt * smoothstep(0.06, 0.3, Tm)
# the darkest places get a second layer across the first, one standard angle
cd, cw = hatch_field(np.pi * 0.25, SPACING * 1.15)
cwidth = smoothstep(0.55, 1.0, Tm) * 0.7
cross_ink = smoothstep(cwidth + 0.1, cwidth - 0.05, cd) * cw * smoothstep(0.55, 0.8, Tm)
hatch_ink = np.clip(hatch_ink * (0.32 if SOFT else 0.6) + cross_ink * (0.2 if SOFT else 0.45), 0, 1) * A
if SOFT:
    hatch_ink = smooth(hatch_ink, 0.8)

# ----- edges where muscles meet, and the outline -----
def wobble(img, amp=1.4, scale=40):
    amp *= S
    """Shift the picture by a slow random wander, like a hand."""
    fx = smooth(rng.standard_normal((H, W)).astype(np.float32), scale)
    fy = smooth(rng.standard_normal((H, W)).astype(np.float32), scale)
    fx *= amp / (np.abs(fx).max() + 1e-6)
    fy *= amp / (np.abs(fy).max() + 1e-6)
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    return cv2.remap(img, gx + fx, gy + fy, cv2.INTER_LINEAR)

edge = np.zeros((H, W), np.float32)
for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
    a = ids
    b = np.roll(np.roll(ids, dy, 0), dx, 1)
    edge = np.maximum(edge, (a != b).astype(np.float32))
outline = np.zeros((H, W), np.float32)
am = (A > 0.5).astype(np.uint8)
k = max(3, int(round(3 * S)) | 1)
outline = cv2.morphologyEx(am, cv2.MORPH_GRADIENT, np.ones((k, k), np.uint8)).astype(np.float32)
inner = edge * (1 - outline)
# dark in shadow, lost in the light
weight = 0.18 + 0.82 * smoothstep(0.05, 0.6, smooth(T, 3))
inner = cv2.dilate(inner, np.ones((max(1, int(round(S))),) * 2, np.uint8)) if S > 1.3 else inner
inner_ink = smooth(inner, 1.0 if SOFT else 0.7) * weight * (1.0 if SOFT else 1.4)
# the outline: firm, heavier on the shadow side (light from the upper left)
gx = cv2.Sobel(smooth(A, 2), cv2.CV_32F, 1, 0)
gy = cv2.Sobel(smooth(A, 2), cv2.CV_32F, 0, 1)
shadow_side = np.clip((-gx * 0.6 - gy * 0.8) / (np.hypot(gx, gy) + 1e-6), -1, 1)   # facing away from the light
out_w = 0.55 + 0.45 * (shadow_side * 0.5 + 0.5)
outline_ink = smooth(cv2.dilate(outline, np.ones((max(2, int(2 * S)),) * 2, np.uint8)), 0.8 if SOFT else 0.01) * out_w * (0.85 if SOFT else 1)
lines = np.clip(np.maximum(inner_ink, outline_ink), 0, 1)
lines = wobble(lines, 1.9 if SOFT else 1.4)

# small form lines from the surface itself (striations, tendons)
detail = cv2.Canny((L * 255).astype(np.uint8), 30, 70).astype(np.float32) / 255
detail = smooth(detail, 0.6) * 0.35 * smoothstep(0.1, 0.5, Tm) * A
ink = np.clip(np.maximum(lines, hatch_ink) + detail, 0, 1)

# construction lines on the head: a center line and the brow, eye and nose
# lines, curved round the egg, drawn light like an artist's first lay-in
names = json.load(open(WORK + 'ids.json'))
head_id = [int(k) for k, (n, _) in names.items() if n == 'Head']
if head_id:
    hm = (ids == head_id[0]).astype(np.uint8)
    ys, xs = np.nonzero(hm)
    if len(xs):
        from PIL import ImageDraw
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        cx, hw, hh = (x0 + x1) / 2, (x1 - x0) / 2, (y1 - y0)
        layer = Image.new('L', (W, H), 0)
        dr = ImageDraw.Draw(layer)
        def arc_line(fy, bulge, width, val):
            pts = []
            for i in range(41):
                u = -1 + i / 20
                x = cx + u * hw * 0.98
                y = y0 + hh * fy + bulge * hh * (1 - u * u)
                pts.append((x, y))
            dr.line(pts, fill=val, width=max(1, int(round(width * S))))
        # center line, bending a little like the egg's front
        pts = [(cx + 0.06 * hw * np.sin(np.pi * t), y0 + hh * (0.04 + 0.92 * t)) for t in np.linspace(0, 1, 41)]
        dr.line(pts, fill=150, width=max(1, int(round(2 * S))))
        if os.environ.get('VIEW', 'front') == 'front':
            arc_line(0.47, 0.035, 2, 150)   # brow
            arc_line(0.73, 0.03, 2, 110)    # nose
        cl = np.asarray(layer).astype(np.float32) / 255 * hm
        cl = wobble(smooth(cl, 0.6), 1.0, 30)
        ink = np.clip(np.maximum(ink, cl * 0.8), 0, 1)

# ----- paper grain: graphite sits on the tooth of the paper -----
grain = smooth(rng.random((H, W)).astype(np.float32), 1.1)
grain = (grain - grain.mean()) / grain.std()
# the tooth shows most in light and middle tones; deep shadow is filled in
tooth = 0.13 * (1 - smoothstep(0.55, 0.9, tone))
tone_g = np.clip(tone * (1 + tooth * grain), 0, 1)
ink_g = np.clip(ink * (1 + 0.1 * grain), 0, 1)

Image.fromarray((tone_g * 255).astype(np.uint8)).save(WORK + TAG + 'shade.png')
Image.fromarray((ink_g * 255).astype(np.uint8)).save(WORK + TAG + 'ink.png')

# preview on cream paper, graphite color
paper = np.array([0.93, 0.90, 0.82], np.float32)
graph = np.array([0.16, 0.16, 0.18], np.float32)
dark = 1 - (1 - tone_g) * (1 - ink_g * 0.9)
img = paper[None, None] * (1 - dark[..., None]) + graph[None, None] * dark[..., None]
Image.fromarray((img * 255).astype(np.uint8)).save(WORK + TAG + 'preview.png')
print('ok', H, W)
