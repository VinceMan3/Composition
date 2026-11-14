"""Turn the muscle map drawings into the fast pieces the app shows.

The drawings (tools/art/drawings/muscle-front.svg and muscle-back.svg, made
by musclemap.py) are too heavy to redraw on a phone every time a muscle is
tapped. So the app shows them as pictures, in layers:

  art/muscle-<view>-shade.webp  the soft graphite shading
  art/muscle-<view>-ink.webp    the pencil lines and hatching
  art/muscle-<view>-map.svg     just the tap shapes and the sheen (small)

The two pictures are black with see-through parts, used as stencils: the app
paints them with the look's colors (--map-shade and --map-ink), so the same
files work on paper and in the garage. A picked muscle's red goes under the
shading, so the drawing shows through it.

Run after musclemap.py:  python3 tools/art/mapimages.py
Needs playwright and Pillow (the checks already use them).
"""

import io
import os
import re
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ART = os.path.join(ROOT, 'art')
W, H = 560, 860                 # the drawing's size, in its own units
SCALE = {'ink': 4, 'shade': 2}  # lines need sharp pixels for zooming in; shading is soft

LAYERS = {
    'shade': '.mm-tone, .mm-edge, .mm-crease',
    'ink': '.mm-ink',
}

CHROME = '/usr/bin/google-chrome'


def render_layer(page, svg_text, layer, scale):
    css = f"""
      html, body {{ margin: 0; background: transparent; }}
      svg {{ display: block; width: {W * scale}px; height: {H * scale}px;
             --map-ink: #000; --map-shade: #000; --map-tone: 1; }}
      svg > g {{ display: none; }}
      svg > g:is({LAYERS[layer]}) {{ display: inline; }}
    """
    page.set_viewport_size({'width': W * scale, 'height': H * scale})
    page.set_content(f'<style>{css}</style>{svg_text}')
    page.wait_for_timeout(200)
    png = page.locator('svg').screenshot(omit_background=True)
    img = Image.open(io.BytesIO(png)).convert('RGBA')
    # Keep only how dark each pixel is, as see-through black.
    alpha = img.getchannel('A')
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    out.putalpha(alpha)
    return out


def map_svg(svg_text, view):
    """The small SVG: tap shapes, the sheen, and only the defs the sheen needs."""
    head = re.match(r'<svg[^>]*>', svg_text).group(0)
    regions = re.search(r'<g class="mm-regions".*?</g>', svg_text, re.S).group(0)
    gloss = re.search(r'<g class="mm-gloss".*?</g>', svg_text, re.S).group(0)
    grads = ''.join(re.findall(r'<(?:radialGradient|linearGradient)[^>]*id="mm-%s-gl".*?</(?:radialGradient|linearGradient)>' % view, svg_text, re.S))
    style = ('<style>.mm-muscle{fill:var(--mm-fill,transparent)}'
             '.mm-gloss{pointer-events:none}'
             '.mm-gloss path{fill:url(#mm-%s-gl);opacity:0}</style>' % view)
    return f'{head}{style}<defs>{grads}</defs>{regions}{gloss}</svg>'


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        page = browser.new_page(device_scale_factor=1)
        for view in ('front', 'back'):
            svg_text = open(os.path.join(ROOT, 'tools', 'art', 'drawings', f'muscle-{view}.svg')).read()
            for layer, scale in SCALE.items():
                img = render_layer(page, svg_text, layer, scale)
                path = os.path.join(ART, f'muscle-{view}-{layer}.webp')
                img.save(path, 'WEBP', quality=82, alpha_quality=88, method=6)
                print(f'{path}: {img.size[0]}x{img.size[1]}, {os.path.getsize(path) // 1024} KB')
            small = map_svg(svg_text, view)
            path = os.path.join(ART, f'muscle-{view}-map.svg')
            open(path, 'w').write(small)
            print(f'{path}: {len(small) // 1024} KB')
        browser.close()


if __name__ == '__main__':
    sys.exit(main())
