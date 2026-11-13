"""Makes the paper and cover textures. Both tile without seams."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
rng = np.random.default_rng(7)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, 'art/')

def band_noise(n, lo, hi):
    """Noise limited to a band of detail sizes; built in frequency space, so it wraps."""
    f = np.fft.fft2(rng.standard_normal((n, n)))
    fy = np.fft.fftfreq(n)[:, None]; fx = np.fft.fftfreq(n)[None, :]
    r = np.hypot(fx, fy) * n
    f *= np.exp(-(r / hi) ** 2) * (1 - np.exp(-(r / lo) ** 2))
    x = np.real(np.fft.ifft2(f)); x -= x.mean(); return x / (np.abs(x).max() + 1e-9)

def wrapped_strokes(n, count, length, width, value, curl=0.25):
    """Short curved lines drawn on a 3x3 canvas so they wrap at the edges."""
    big = Image.new('L', (n * 3, n * 3), 0); d = ImageDraw.Draw(big)
    for _ in range(count):
        x, y = rng.uniform(n, 2 * n, 2); a = rng.uniform(0, np.pi); L = rng.uniform(*length)
        pts = []
        for t in np.linspace(0, 1, 8):
            a2 = a + curl * np.sin(t * 3 + x)
            pts.append((x + np.cos(a2) * L * t, y + np.sin(a2) * L * t))
        v = int(rng.uniform(*value))
        for dx in (-n, 0, n):
            for dy in (-n, 0, n):
                d.line([(px + dx, py + dy) for px, py in pts], fill=v, width=width)
    return np.asarray(big.crop((n, n, 2 * n, 2 * n)), dtype=float) / 255

# ---- paper: near white, to be multiplied over the page color ----
n = 420
grain = band_noise(n, 30, 150) * 0.045          # fine tooth
cloud = band_noise(n, 1.5, 6) * 0.05            # slow mottling
pulp = band_noise(n, 8, 30) * 0.03              # mid clumps
fibers_dark = np.asarray(Image.fromarray((wrapped_strokes(n, 260, (6, 22), 1, (60, 150)) * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.5)), dtype=float) / 255
fibers_light = np.asarray(Image.fromarray((wrapped_strokes(n, 200, (5, 18), 1, (60, 140)) * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.6)), dtype=float) / 255
specks = (rng.random((n, n)) > 0.9993).astype(float)
specks = np.asarray(Image.fromarray((specks * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.7)), dtype=float) / 255
paper = 0.968 + grain * 0.8 + cloud * 0.55 + pulp * 0.8 - fibers_dark * 0.085 + fibers_light * 0.05 - specks * 0.4
warm = np.stack([paper, paper * 0.992, paper * 0.972], -1)   # shadows lean brown
Image.fromarray((np.clip(warm, 0, 1) * 255).astype('uint8')).save(OUT + 'paper.webp', quality=96, method=6)

# ---- cover wear: see-through scuffs and speckle for the cardstock ----
n = 400
tooth = band_noise(n, 40, 200)
rub = np.clip(band_noise(n, 1.2, 4) - 0.25, 0, 1)             # rubbed patches
scratch = np.asarray(Image.fromarray((wrapped_strokes(n, 13, (25, 110), 1, (70, 170), curl=0.05) * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.6)), dtype=float) / 255
light = np.clip(tooth, 0, 1) * 0.16 + rub * 0.20 + scratch * 0.34
dark = np.clip(-tooth, 0, 1) * 0.14 + np.clip(band_noise(n, 3, 10) - 0.5, 0, 1) * 0.12
alpha = np.clip(np.maximum(light, dark), 0, 0.6)
is_light = light >= dark
rgb = np.where(is_light[..., None], np.array([250, 252, 255.]), np.array([24, 44, 62.]))
Image.fromarray(np.dstack([rgb, alpha * 255]).astype('uint8'), 'RGBA').save(OUT + 'cover-wear.webp', quality=70, alpha_quality=45, method=6)
import os
for f in ('paper.webp', 'cover-wear.webp'): print(f, os.path.getsize(OUT + f) // 1024, 'KB')
