"""Step 1 checks. Run: python3 test/run.py [base_url] [out_dir]"""
import sys, os, json, time
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8770/index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), 'shots')
os.makedirs(OUT, exist_ok=True)
TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(TOOLS)
FONTS = os.path.join(TOOLS, 'node_modules/@fontsource')
FACES = [('Shrikhand', 400, 'shrikhand/files/shrikhand-latin-400-normal.woff2'),
         ('Bowlby One', 400, 'bowlby-one/files/bowlby-one-latin-400-normal.woff2'),
         ('Archivo Narrow', 600, 'archivo-narrow/files/archivo-narrow-latin-600-normal.woff2'),
         ('Archivo Narrow', 700, 'archivo-narrow/files/archivo-narrow-latin-700-normal.woff2'),
         ('Special Elite', 400, 'special-elite/files/special-elite-latin-400-normal.woff2'),
         ('Handlee', 400, 'handlee/files/handlee-latin-400-normal.woff2')]
CSS = ''.join(f"@font-face{{font-family:'{n}';font-weight:{w};src:url('/__fonts/{p}') format('woff2')}}" for n, w, p in FACES)

results = []
def check(name, ok, detail=''):
    results.append((name, bool(ok), detail))
    print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))

def wire(page, errors):
    page.route('https://fonts.googleapis.com/**', lambda r: r.fulfill(status=200, content_type='text/css', body=CSS))
    page.route('**/__fonts/**', lambda r: r.fulfill(status=200, content_type='font/woff2',
               body=open(os.path.join(FONTS, r.request.url.split('/__fonts/')[1]), 'rb').read()))
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('requestfailed', lambda r: errors.append('requestfailed ' + r.url))

def settle(page, name=None):
    # the address changes a beat after the click, so wait for the named page to be the only one
    if name is None:
        page.wait_for_timeout(80)
        name = page.evaluate("(location.hash.slice(1) || 'cover')")
        if name not in ['cover', 'today', 'notebook', 'stats', 'more']: name = 'cover'
    page.wait_for_function("n => document.querySelectorAll('.page').length === 1 && !document.querySelector('.shade') && document.querySelector('.page').dataset.page === n", arg=name, timeout=3000)

def overflow(page):
    return page.evaluate("""() => {
      const app = document.querySelector('.app').getBoundingClientRect();
      const bad = [];
      for (const el of document.querySelectorAll('.page *, .tabs *, .strip *')) {
        const r = el.getBoundingClientRect();
        if (!r.width) continue;
        if (r.right > app.right + 1 || r.left < app.left - 1) bad.push(el.className || el.tagName);
      }
      const pg = document.querySelector('.page');
      return {bad, hscroll: pg.scrollWidth > pg.clientWidth + 1, doc: document.documentElement.scrollWidth > innerWidth};
    }""")

