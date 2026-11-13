"""Draws the earned stickers as vintage badges and saves them as PNGs.
Run: python3 art/badges.py"""
import base64, math, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(REPO, 'art/')
FONTS = os.path.join(REPO, 'tools/node_modules/@fontsource')
def face(name, weight, path):
    data = base64.b64encode(open(os.path.join(FONTS, path), 'rb').read()).decode()
    return f"@font-face{{font-family:'{name}';font-weight:{weight};src:url(data:font/woff2;base64,{data}) format('woff2')}}"
CSS = face('Bowlby One', 400, 'bowlby-one/files/bowlby-one-latin-400-normal.woff2') + \
      face('Archivo Narrow', 700, 'archivo-narrow/files/archivo-narrow-latin-700-normal.woff2') + \
      face('Shrikhand', 400, 'shrikhand/files/shrikhand-latin-400-normal.woff2')

EDGE, NAVY, MAROON, MUSTARD, GREEN, PURPLE, BLUE, PAPER, INK, RED = '#F7F0DA', '#1D3B52', '#7A2233', '#E9B42C', '#2F5D3A', '#5B3F7A', '#86AFCA', '#F6EDCD', '#2B2420', '#C8452F'

def defs(uid):
    return f"""<defs>
    <pattern id="dots{uid}" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.5" fill="#000" opacity=".16"/></pattern>
    <path id="top{uid}" d="M 78 230 A 152 152 0 0 1 382 230"/>
    <path id="bot{uid}" d="M 62 230 A 168 168 0 0 0 398 230"/>
    <filter id="rough{uid}"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="{uid}"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 -9 6.6"/><feComposite in="SourceGraphic" operator="in"/></filter>
    </defs>"""

def big(text, y, size, fill, shadow, font='Bowlby One', spacing=0):
    a = f'font-family="{font}" font-size="{size}" text-anchor="middle" letter-spacing="{spacing}"'
    return f'<text x="{230 + size * .05}" y="{y + size * .05}" {a} fill="{shadow}">{text}</text><text x="230" y="{y}" {a} fill="{fill}">{text}</text>'

def arc(uid, which, text, size, fill, spacing=3):
    return f'<text font-family="Archivo Narrow" font-weight="700" font-size="{size}" letter-spacing="{spacing}" fill="{fill}" text-anchor="middle"><textPath href="#{which}{uid}" startOffset="50%">{text}</textPath></text>'

def star(cx, cy, r, fill):
    pts = ' '.join(f'{cx + (r if i % 2 == 0 else r * .42) * math.sin(i * math.pi / 5):.1f},{cy - (r if i % 2 == 0 else r * .42) * math.cos(i * math.pi / 5):.1f}' for i in range(10))
    return f'<polygon points="{pts}" fill="{fill}"/>'

def scallop(r, n, bump):
    pts = []
    for i in range(n * 2):
        a = i * math.pi / n; rr = r + (bump if i % 2 == 0 else 0)
        pts.append(f'{230 + rr * math.cos(a):.1f},{230 + rr * math.sin(a):.1f}')
    return ' '.join(pts)

def wrap(uid, body):
    return f'<svg id="b{uid}" xmlns="http://www.w3.org/2000/svg" width="460" height="460" viewBox="0 0 460 460">{defs(uid)}<g filter="url(#rough{uid})">{body}</g></svg>'

def seal(uid, ring, core, top, word, bottom, accent=MUSTARD, size=96):
    return wrap(uid, f"""
    <polygon points="{scallop(212, 22, 14)}" fill="{EDGE}" stroke="#CFC6A8" stroke-width="2" stroke-linejoin="round"/>
    <polygon points="{scallop(198, 22, 12)}" fill="{ring}"/>
    <circle cx="230" cy="230" r="178" fill="none" stroke="{accent}" stroke-width="4"/>
    <circle cx="230" cy="230" r="128" fill="{core}" stroke="{accent}" stroke-width="5"/>
    <circle cx="230" cy="230" r="128" fill="url(#dots{uid})"/>
    {arc(uid, 'top', top, 27, PAPER)}{arc(uid, 'bot', bottom, 27, PAPER)}
    {star(72, 230, 13, accent)}{star(388, 230, 13, accent)}
    {big(word, 230 + size * .35, size, accent, INK)}""")

def plate(uid, color, number, top, bottom):
    return wrap(uid, f"""
    <circle cx="230" cy="230" r="222" fill="{EDGE}" stroke="#CFC6A8" stroke-width="2"/>
    <circle cx="230" cy="230" r="208" fill="{color}"/>
    <circle cx="230" cy="230" r="208" fill="url(#dots{uid})"/>
    <circle cx="230" cy="230" r="196" fill="none" stroke="#000" stroke-opacity=".28" stroke-width="10"/>
    <circle cx="230" cy="230" r="184" fill="none" stroke="#fff" stroke-opacity=".3" stroke-width="3"/>
    <circle cx="230" cy="230" r="112" fill="{INK}" stroke="{PAPER}" stroke-width="5"/>
    <circle cx="230" cy="230" r="112" fill="url(#dots{uid})"/>
    {arc(uid, 'top', top, 30, PAPER, 4)}{arc(uid, 'bot', bottom, 30, PAPER, 4)}
    {star(66, 230, 12, PAPER)}{star(394, 230, 12, PAPER)}
    {big(number, 262, 92, MUSTARD, '#000')}""")

def ticket(uid, color, small, word, word2, accent=MUSTARD):
    notch = lambda x, y: f'<circle cx="{x}" cy="{y}" r="22" fill="#fff"/>'
    shape = '<path d="M40 110 H420 V208 A22 22 0 0 0 420 252 V350 H40 V252 A22 22 0 0 0 40 208 Z" {a}/>'
    return wrap(uid, f"""
    <g transform="rotate(-5 230 230)">
    {shape.format(a=f'fill="{EDGE}" stroke="{EDGE}" stroke-width="26" stroke-linejoin="round"')}
    {shape.format(a=f'fill="{color}"')}
    {shape.format(a=f'fill="url(#dots{uid})"')}
    <path d="M62 132 H398 V328 H62 Z" fill="none" stroke="{accent}" stroke-width="4" stroke-dasharray="2 9" stroke-linecap="round"/>
    <text x="230" y="170" font-family="Archivo Narrow" font-weight="700" font-size="27" letter-spacing="5" fill="{PAPER}" text-anchor="middle">{small}</text>
    {big(word, 250, 78, accent, INK)}
    {big(word2, 312, 50, PAPER, INK)}
    </g>""")

def shield(uid, color, top, word, word2):
    shape = 'M230 34 L402 84 V236 C402 330 330 398 230 430 C130 398 58 330 58 236 V84 Z'
    return wrap(uid, f"""
    <path d="{shape}" fill="{EDGE}" stroke="{EDGE}" stroke-width="24" stroke-linejoin="round"/>
    <path d="{shape}" fill="{color}"/>
    <path d="{shape}" fill="url(#dots{uid})"/>
    <path d="{shape}" fill="none" stroke="{MUSTARD}" stroke-width="5" transform="translate(23 23) scale(.9)"/>
    {star(230, 122, 44, MUSTARD)}
    <text x="230" y="206" font-family="Archivo Narrow" font-weight="700" font-size="26" letter-spacing="5" fill="{PAPER}" text-anchor="middle">{top}</text>
    {big(word, 266, 54, MUSTARD, INK)}
    {big(word2, 318, 44, PAPER, INK)}""")

def burst(uid, color, number, top, bottom):
    rays = ''.join(f'<path d="M230 230 L{230 + 190 * math.cos(a):.1f} {230 + 190 * math.sin(a):.1f} L{230 + 190 * math.cos(a + .131):.1f} {230 + 190 * math.sin(a + .131):.1f} Z" fill="#fff" opacity=".2"/>' for a in [i * .2618 for i in range(24)])
    return wrap(uid, f"""
    <polygon points="{scallop(208, 16, 18)}" fill="{EDGE}" stroke="#CFC6A8" stroke-width="2" stroke-linejoin="round"/>
    <polygon points="{scallop(194, 16, 16)}" fill="{color}"/>
    <clipPath id="c{uid}"><circle cx="230" cy="230" r="186"/></clipPath><g clip-path="url(#c{uid})">{rays}</g>
    <circle cx="230" cy="230" r="186" fill="url(#dots{uid})"/>
    <text x="230" y="130" font-family="Archivo Narrow" font-weight="700" font-size="30" letter-spacing="6" fill="{INK}" text-anchor="middle">{top}</text>
    {big(number, 290, 170, MAROON, PAPER)}
    <text x="230" y="352" font-family="Archivo Narrow" font-weight="700" font-size="30" letter-spacing="6" fill="{INK}" text-anchor="middle">{bottom}</text>""")

def sign(uid, word, word2, small):
    d = 'M230 28 L432 230 L230 432 L28 230 Z'
    return wrap(uid, f"""
    <path d="{d}" fill="{EDGE}" stroke="{EDGE}" stroke-width="26" stroke-linejoin="round"/>
    <path d="{d}" fill="{MUSTARD}" stroke="{MUSTARD}" stroke-width="8" stroke-linejoin="round"/>
    <path d="{d}" fill="url(#dots{uid})"/>
    <path d="{d}" fill="none" stroke="{INK}" stroke-width="7" stroke-linejoin="round" transform="translate(27.6 27.6) scale(.88)"/>
    {big(word, 222, 70, INK, PAPER)}
    {big(word2, 290, 70, INK, PAPER)}
    <text x="230" y="336" font-family="Archivo Narrow" font-weight="700" font-size="28" letter-spacing="5" fill="{INK}" text-anchor="middle">{small}</text>
    {star(230, 122, 20, INK)}""")

def glove(uid, small, word, word2):
    # A boxing glove, side on: the fist, the thumb, and the laced cuff.
    g = f"""<g transform="translate(120 44) scale(1.02)">
    <path d="M52 150 C20 120 22 60 62 34 C104 6 176 14 196 62 C210 96 200 132 176 152 L170 176 L62 176 Z" fill="{RED}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>
    <path d="M150 96 C176 86 200 104 196 132 C192 156 172 166 152 158" fill="{RED}" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>
    <path d="M70 62 C92 40 132 36 158 50" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="9" stroke-linecap="round"/>
    <path d="M58 176 H174 V214 H58 Z" fill="{PAPER}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>
    <path d="M84 184 L96 206 M106 184 L118 206 M128 184 L140 206" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>
    </g>"""
    return wrap(uid, f"""
    <circle cx="230" cy="230" r="222" fill="{EDGE}" stroke="#CFC6A8" stroke-width="2"/>
    <circle cx="230" cy="230" r="208" fill="{PURPLE}"/>
    <circle cx="230" cy="230" r="208" fill="url(#dots{uid})"/>
    <circle cx="230" cy="230" r="192" fill="none" stroke="{MUSTARD}" stroke-width="4"/>
    {g}
    {big(word, 338, 52, MUSTARD, INK)}
    <text x="230" y="382" font-family="Archivo Narrow" font-weight="700" font-size="27" letter-spacing="5" fill="{PAPER}" text-anchor="middle">{small}</text>""")

BADGES = {
    'badge-first-page': ticket(1, MAROON, 'ADMIT ONE LIFTER', 'FIRST', 'PAGE'),
    'badge-pages-10': burst(2, MUSTARD, '10', 'PAGES', 'FILED'),
    'badge-pages-50': burst(3, BLUE, '50', 'PAGES', 'FILED'),
    'badge-record': shield(4, NAVY, 'PERSONAL', 'RECORD', 'BREAKER'),
    'badge-bench-225': plate(5, RED, '225', 'TWO PLATE', 'BENCH'),
    'badge-squat-315': plate(6, '#2F6EA5', '315', 'THREE PLATE', 'SQUAT'),
    'badge-dead-405': plate(7, GREEN, '405', 'FOUR PLATE', 'DEADLIFT'),
    'badge-club-1000': seal(8, MAROON, NAVY, 'SQUAT · BENCH · DEADLIFT', '1000', 'POUND CLUB', size=82),
    'badge-week-3': ticket(9, GREEN, 'ONE WEEK', 'THREE', 'DAYS IN'),
    'badge-bag-5': glove(10, 'FIVE SESSIONS', 'BAG WORK', ''),
    'badge-road-10': sign(11, 'ROAD', 'WORK', '10 MILES'),
    'badge-club-1250': seal(12, NAVY, MAROON, 'SQUAT · BENCH · DEADLIFT', '1250', 'POUND CLUB', size=82),
    'badge-club-1500': seal(13, GREEN, NAVY, 'SQUAT · BENCH · DEADLIFT', '1500', 'POUND CLUB', size=82),
    'badge-million': seal(14, MAROON, NAVY, 'LIFETIME TOTAL', '1,000,000', 'POUNDS MOVED', size=44),
    'badge-bw-bench': shield(15, MAROON, 'BODYWEIGHT', '1.5X', 'BENCH'),
    'badge-bw-squat': shield(16, '#2F6EA5', 'BODYWEIGHT', '2X', 'SQUAT'),
    'badge-bw-dead': shield(17, GREEN, 'BODYWEIGHT', '2.5X', 'DEADLIFT'),
}

html = f'<!doctype html><style>{CSS} body{{margin:0;background:transparent}} svg{{display:block}}</style>' + ''.join(BADGES.values())
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    page = b.new_page(viewport={'width': 480, 'height': 480}, device_scale_factor=1)
    page.set_content(html); page.evaluate('document.fonts.ready'); page.wait_for_timeout(300)
    for i, name in enumerate(BADGES, 1):
        page.locator(f'#b{i}').screenshot(path='/tmp/' + name + '.png', omit_background=True)
    b.close()

from PIL import Image
names = list(BADGES)
sheet = Image.new('RGB', (230 * 6, 230 * 3), '#A9CBE0')
for i, n in enumerate(names):
    im = Image.open('/tmp/' + n + '.png').convert('RGBA')
    box = im.getbbox(); im = im.crop(box); im.save(OUT + n + '.webp', quality=84, alpha_quality=90, method=6)
    t = im.copy(); t.thumbnail((220, 220)); sheet.paste(t, (230 * (i % 6) + 5, 230 * (i // 6) + 5), t)
    print(n, im.size, os.path.getsize(OUT + n + '.webp') // 1024, 'KB')
sheet.save(os.path.join(REPO, 'tools/test/badges.png'))
