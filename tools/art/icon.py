"""Draws the home-screen icon: the blue notebook cover with its rings and a
big C. Run: python3 art/icon.py"""
import base64, os
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(REPO, 'tools/node_modules/@fontsource/shrikhand/files/shrikhand-latin-400-normal.woff2')
font = base64.b64encode(open(F, 'rb').read()).decode()
OUT = os.path.join(REPO, 'art/icon/')
html = f"""<!doctype html><style>
@font-face {{ font-family: S; src: url(data:font/woff2;base64,{font}); }}
body {{ margin: 0; }}
.i {{ position: relative; width: 512px; height: 512px; overflow: hidden;
  background: radial-gradient(rgba(29,59,82,.18) 2px, transparent 3px) 0 0 / 14px 14px,
              repeating-conic-gradient(from 0deg at 50% 62%, #A9CBE0 0deg 10deg, #BBD8EA 10deg 20deg); }}
.i::after {{ content: ""; position: absolute; inset: 0; background: linear-gradient(130deg, rgba(255,255,255,.35), transparent 45%, rgba(20,44,66,.22)); }}
.rings {{ position: absolute; left: 0; right: 0; top: 0; height: 96px;
  background: repeating-linear-gradient(90deg, transparent 0 24px, #5F6C78 24px 34px, transparent 34px 64px) 6px 0 / 100% 58px no-repeat,
              radial-gradient(circle at 29px 66px, #4A3B2C 10px, transparent 11.5px) 0 0 / 64px 96px repeat-x; }}
.c {{ position: absolute; left: 0; right: 0; top: 98px; text-align: center; font: 330px/1 S; color: #7A2233; text-shadow: 12px 12px 0 #E9B42C; }}
</style><div class="i" id="i"><div class="rings"></div><div class="c">C</div></div>"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    page = b.new_page(viewport={'width': 512, 'height': 512})
    page.set_content(html); page.evaluate('document.fonts.ready'); page.wait_for_timeout(200)
    page.locator('#i').screenshot(path=OUT + 'icon-512.png')
    b.close()
from PIL import Image
big = Image.open(OUT + 'icon-512.png').convert('RGB')
for size in (192, 180):
    big.resize((size, size), Image.LANCZOS).save(OUT + f'icon-{size}.png', optimize=True)
big.save(OUT + 'icon-512.png', optimize=True)
print([ (f, os.path.getsize(OUT + f) // 1024) for f in sorted(os.listdir(OUT))])
