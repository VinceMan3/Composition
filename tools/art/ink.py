"""Lifts pen ink off a photo of ruled notebook paper.
Removes the blue rules and the paper, evens out the photo's lighting, and
saves just the strokes as a see-through image.

Run: python3 -I art/ink.py <photo> <out.webp> <left> <top> <right> <bottom>
(the crop box is in the photo's pixels)"""
import sys
import numpy as np
from PIL import Image, ImageFilter

src, out = sys.argv[1], sys.argv[2]
box = tuple(int(v) for v in sys.argv[3:7])
im = Image.open(src).convert('RGB').crop(box)
a = np.asarray(im, dtype=np.float32)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
lum = 0.3 * R + 0.59 * G + 0.11 * B

# The ruled lines are blue (blue above red); the paper and the ink both lean
# red. Anything bluish and not very dark is a line, widened a pixel to catch
# its soft edges.
rule = (B - R > -6) & (lum > 105)
rule = np.asarray(Image.fromarray((rule * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
rule &= lum > 95

# The paper's own brightness, which the photo lights unevenly: a heavy blur of
# the image with the ink and lines painted over by their surroundings.
paper = lum.copy()
dark = lum < np.percentile(lum, 60)
paper[dark | rule] = np.nan
fill = np.nanmedian(paper)
paper = np.where(np.isnan(paper), fill, paper)
small = Image.fromarray(paper.astype(np.uint8)).resize((im.width // 16, im.height // 16), Image.BILINEAR)
small = small.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(4))
paper = np.asarray(small.resize(im.size, Image.BILINEAR), dtype=np.float32)

# How much darker than the paper each spot is: that is the ink.
ink = np.clip((paper - lum) / np.maximum(paper, 1), 0, 1)
# Where a rule crossed the drawing, fill it from the shading just above and
# below; where it crossed bare paper that comes out as nothing.
up = np.roll(ink, -4, axis=0)
down = np.roll(ink, 4, axis=0)
fill_in = np.where(rule, np.minimum(up, down) * 0.95, 0)
fill_in[np.roll(rule, -4, axis=0) | np.roll(rule, 4, axis=0)] = 0
ink = np.where(rule, fill_in, ink)
ink = np.clip((ink - 0.11) / 0.52, 0, 1) ** 0.9   # a clean paper, full-strength strokes

# Ballpoint blue-black, and a soft edge so it sits on the page.
alpha = Image.fromarray((ink * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
color = Image.new('RGB', im.size, (34, 36, 78))
result = Image.merge('RGBA', (*color.split(), alpha))
box2 = alpha.point(lambda v: 255 if v > 40 else 0).getbbox()
result = result.crop(box2)
result.thumbnail((720, 720), Image.LANCZOS)
result.save(out, quality=86, alpha_quality=90, method=6)
print(out, result.size)
