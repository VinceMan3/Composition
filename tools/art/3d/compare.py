import json, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
W3 = '/home/claude/3d/work/'
PAPER = np.array([0.93, 0.90, 0.82], np.float32); GRAPH = np.array([0.165, 0.165, 0.18], np.float32); RED = np.array([0.79, 0.19, 0.17], np.float32)

ids_rgb = np.asarray(Image.open(W3 + 'ids.png')).astype(np.int64)
idmap = (ids_rgb[..., 0] << 16) | (ids_rgb[..., 1] << 8) | ids_rgb[..., 2]
names = json.load(open(W3 + 'ids.json'))
chest = [int(k) for k, (n, _) in names.items() if 'pectoralis major' in n]
mask = np.isin(idmap, chest).astype(np.float32)
mask = cv2.GaussianBlur(mask, (0, 0), 0.8)
L = np.asarray(Image.open(W3 + 'shade.png').convert('L')).astype(np.float32) / 255

def compose(tag):
    tone = np.asarray(Image.open(W3 + tag + 'shade.png')).astype(np.float32) / 255
    ink = np.asarray(Image.open(W3 + tag + 'ink.png')).astype(np.float32) / 255
    # the red takes the form's light and shadow, like a lit, rounded muscle
    lo, hi = np.percentile(L[mask > 0.5], [3, 97])
    Ln = np.clip((L - lo) / (hi - lo), 0, 1)
    red = RED[None, None] * (0.52 + 0.4 * Ln[..., None])
    m = mask[..., None]
    base = PAPER[None, None] * (1 - m) + red * m
    dark = 1 - (1 - tone * (0.85 - 0.35 * mask)) * (1 - ink * (0.9 - 0.25 * mask))
    img = base * (1 - dark[..., None]) + GRAPH[None, None] * dark[..., None]
    sheen = cv2.GaussianBlur(np.clip((Ln - 0.75) / 0.25, 0, 1), (0, 0), 9) * mask * 0.32
    img = img + sheen[..., None] * (1 - img)
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

# the current drawing, chest picked, same paper
svg = open('/home/claude/composition/tools/art/drawings/muscle-front.svg').read()
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    pg = b.new_page(viewport={'width': 1120, 'height': 1720})
    pg.set_content(f"""<style>body{{margin:0;background:rgb(237,230,209)}} html{{background:rgb(237,230,209);overflow:hidden}} body{{overflow:hidden}} svg{{width:1120px;height:1720px;display:block}}
      .mm-muscle[data-group=chest]{{--mm-fill:#C9302C}} .mm-gloss path[data-group=chest], .mm-gloss path[data-part^=chest]{{opacity:1!important}}</style>{svg}""")
    pg.wait_for_timeout(500)
    pg.screenshot(path=W3 + 'current.png')
    b.close()
cur = Image.open(W3 + 'current.png').convert('RGB').crop((0, 0, 1112, 1720))

def fit_fig(im, box, h):
    im = im.crop(box)
    return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)

def bbox_of(im, paper=tuple(int(round(c * 255)) for c in PAPER)):
    a = np.asarray(im.convert('RGB')).astype(int)
    d = np.abs(a - np.array(paper)).sum(2) > 40
    d[:, :4] = False; d[:, -4:] = False; d[:4] = False; d[-4:] = False
    ys, xs = np.nonzero(d)
    h, w = d.shape
    return max(xs.min() - 10, 0), max(ys.min() - 10, 0), min(xs.max() + 10, w), min(ys.max() + 10, h)

g = compose('g_'); s = compose('s_')
pairs = [('Now: drawn by code', cur), ('3D, engraving style', g), ('3D, soft graphite', s)]
FH = 1000
cols = []
for title, im in pairs:
    bx = bbox_of(im)
    full = fit_fig(im, bx, FH)
    # torso close-up: from the collarbones to the belt, at the same scale for each
    x0, y0, x1, y1 = bx
    hh = y1 - y0
    crop = im.crop((x0 + (x1 - x0) * 0.22, y0 + hh * 0.13, x1 - (x1 - x0) * 0.22, y0 + hh * 0.5))
    crop = crop.resize((560, int(crop.height * 560 / crop.width)), Image.LANCZOS)
    cols.append((title, full, crop))
CW = 640
H = 70 + FH + 30 + max(c[2].height for c in cols) + 30
out = Image.new('RGB', (CW * 3, H), tuple(int(round(c * 255)) for c in PAPER))
d = ImageDraw.Draw(out)
try:
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
except Exception:
    f = ImageFont.load_default()
for i, (title, full, crop) in enumerate(cols):
    x = i * CW
    d.text((x + 30, 22), title, fill=(40, 36, 32), font=f)
    out.paste(full, (x + (CW - full.width) // 2, 70))
    out.paste(crop, (x + (CW - crop.width) // 2, 70 + FH + 30))
    if i:
        d.line([(x, 10), (x, H - 10)], fill=(190, 180, 160), width=2)
out.save(W3 + 'compare.png')
out.resize((out.width // 2, out.height // 2), Image.LANCZOS).save(W3 + 'compare_small.png')
print(out.size)
