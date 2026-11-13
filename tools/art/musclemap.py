"""
Draws the muscle map: a front and a back view of a lifter, in navy ballpoint,
with every muscle group as its own shape so the app can light it up.

Run from the repository root:

    python3 tools/art/musclemap.py

It writes art/muscle-back.svg (and art/muscle-front.svg once the front is
drawn). The drawing is built from point lists below, not traced pixels, so it
stays sharp and small.

How the figure is laid out
--------------------------
- Proportions follow the usual eight-heads canon. One head is 100 units:
  the top of the head is y 16, the chin about y 116, the crotch about y 442
  and the soles about y 825.
- Points are written for the figure's LEFT half as (dx, y): dx is the
  distance out from the midline. The right half is the mirror image, so the
  two sides always match.
- Arms hang about 28 degrees out from the body, forearms about 34, palms
  facing forward (the anatomical position). Arm points are written in the
  arm's own frame: u runs down the bone, v is out to the side (+) or in
  toward the body (-). That keeps each muscle's start and end on the bone.
- Muscle borders, start points and end points follow Gray's Anatomy (20th
  edition, 1918, public domain): Fig. 409 for the back and shoulder,
  Fig. 434 for the glutes and back of the thigh, and the arm and leg plates.
  Muscle bellies are drawn fuller than Gray's lean figure for a lifter's
  build; where muscles start and end does not move.
- Hatching follows each muscle's real fiber direction: every hatch line runs
  from where the muscle starts toward where it ends.
"""

import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W, H = 560, 860          # drawing size
CX = W / 2               # the midline
LIGHT = (-0.55, -0.83)   # light comes from the upper left


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def frame(ox, oy, deg):
    """A limb frame: origin (ox, oy) in (dx, y), pointing deg out from straight down."""
    a = math.radians(deg)
    d = (math.sin(a), math.cos(a))        # down the bone
    s = (math.cos(a), -math.sin(a))       # out to the side
    def f(u, v):
        return (round(ox + d[0] * u + s[0] * v, 1), round(oy + d[1] * u + s[1] * v, 1))
    return f


ARM = frame(92, 170, 28)        # from the head of the humerus
FORE = frame(160, 298, 34)      # from the elbow
HAND = frame(226, 396, 30)      # from the wrist


def P(*items):
    """A run of points: a mix of (dx, y) tuples and lists of them."""
    out = []
    for it in items:
        out.extend(it if isinstance(it, list) else [it])
    return out


def R(p):
    return list(reversed(p))


# ---------------------------------------------------------------------------
# BACK VIEW: borders shared between muscles (figure's left half)
# ---------------------------------------------------------------------------

AX = (94, 226)                  # the armpit, seen from behind
ACR = (102, 154)                # tip of the acromion
ACR_ANGLE = (97, 159)           # angle of the acromion, where the rear delt starts
SPINE_ROOT = (43, 196)          # root of the scapular spine
T12 = (0, 302)                  # lowest point of the trapezius
DELT_TIP = ARM(90, 13)          # deltoid tuberosity on the humerus
ELB_OUT = ARM(124, 27)          # lateral supracondylar ridge
EPI_IN = ARM(141, -25)          # medial epicondyle
PSIS = (18, 364)                # the dimple over the back of the hip bone

B = {
    # Trapezius: from the back of the skull, down the side of the neck, out
    # over the shoulder to the acromion.
    'trap_top': [(0, 99), (11, 99.5), (21, 102), (27, 110), (32, 120), (41, 129),
                 (56, 137), (74, 143), (90, 148), ACR],
    # Spine of the scapula. The trapezius ends on its upper lip, the rear
    # delt starts from its lower lip.
    'spine': [ACR, ACR_ANGLE, (84, 167), (70, 175), (57, 184), (48, 190), SPINE_ROOT],
    # Lower trapezius, from the root of the spine to its point at T12.
    'trap_low': [SPINE_ROOT, (42, 210), (37, 230), (29, 252), (19, 274), (9, 291), T12],

    # Deltoid, over the cap of the shoulder down to its tuberosity.
    'delt_out': [ACR, ARM(-9, 20), ARM(2, 33), ARM(20, 39), ARM(42, 38), ARM(62, 31),
                 ARM(77, 22), DELT_TIP],
    # Line between the rear delt and the side delt.
    'delt_split': [ACR_ANGLE, ARM(8, 24), ARM(34, 28), ARM(62, 22), DELT_TIP],
    # Lower edge of the rear delt.
    'rdelt_low': [(57, 184), (65, 197), (78, 207), (94, 213), ARM(40, -6), ARM(56, 2),
                  ARM(74, 8), DELT_TIP],

    # Upper arm: inside and outside edges.
    'arm_in': [AX, ARM(58, -28), ARM(82, -31), ARM(106, -29), ARM(126, -26), EPI_IN],
    'arm_out': [DELT_TIP, ARM(80, 28), ARM(98, 31), ARM(114, 29), ELB_OUT],
    # Bottom of the triceps, around the olecranon, then up the outside of
    # the arm where brachioradialis starts on the supracondylar ridge.
    'tri_low': [EPI_IN, FORE(-6, -16), FORE(2, -6), FORE(1, 8), ARM(136, 18), ELB_OUT],

    # Forearm, seen from behind with the palm forward: the extensors.
    'fore_out': [ELB_OUT, FORE(2, 31), FORE(18, 35), FORE(40, 32), FORE(68, 23),
                 FORE(96, 16), FORE(118, 14)],
    'fore_in': [EPI_IN, FORE(8, -26), FORE(28, -29), FORE(56, -24), FORE(88, -16),
                FORE(118, -13)],
    'wrist': [FORE(118, 14), FORE(120, 0), FORE(118, -13)],

    # Lats: top edge, from under the lower trapezius over the bottom corner
    # of the scapula to the armpit.
    'lat_top': [(29, 252), (42, 250), (56, 247), (70, 242), (84, 234), AX],
    # Side of the torso.
    'side_hi': [AX, (99, 240), (101, 256), (99, 272), (95, 288)],
    'side_lo': [(95, 288), (90, 304), (87, 320), (86, 334), (87, 346)],
    # Front edge of the lat, where the external oblique shows at the flank.
    'lat_front': [(95, 288), (88, 306), (82, 326), (78, 346)],
    # Iliac crest, outer part.
    'crest': [(87, 346), (82, 349), (78, 346), (66, 347), (54, 348)],
    # Where the lat's muscle turns into the flat sheet over the lower back.
    'lat_med': [(54, 348), (46, 334), (36, 314), (26, 292), (19, 274)],
    # Back of the hip bone and top of the sacrum.
    'sacrum': [(54, 348), (40, 356), (28, 361), PSIS, (8, 367), (0, 368)],

    # Hip and glutes.
    'hip': [(87, 346), (90, 358), (92, 372), (93, 388), (93, 398)],
    'gmax_top': [PSIS, (34, 368), (52, 374), (68, 381), (82, 389), (93, 398)],
    'gmax_out': [(93, 398), (94, 410), (92, 424), (86, 436), (76, 445)],
    'gfold': [(76, 445), (62, 452), (46, 455), (30, 453), (20, 449), (12, 444), (6, 438)],
    'cleft': [(6, 438), (4, 420), (3, 400), (2, 380), (0, 368)],

    # Thigh.
    'thigh_out': [(92, 424), (93, 440), (93, 460), (92, 484), (90, 510), (86, 538),
                  (80, 565), (73, 590), (66, 610), (62, 624)],
    'thigh_in': [(6, 438), (8, 450), (9, 470), (10, 496), (12, 526), (15, 556),
                 (19, 585), (23, 607), (26, 624)],
    # Hamstrings: outer edge (biceps femoris against vastus lateralis and the
    # iliotibial band), inner edge (semitendinosus against adductor magnus
    # and gracilis).
    'ham_top': [(20, 449), (30, 453), (46, 455), (62, 452)],
    'ham_out': [(62, 452), (69, 476), (73, 504), (73, 534), (70, 564), (64, 592), (57, 624)],
    'ham_in': [(20, 449), (25, 476), (28, 506), (29, 538), (28, 568), (27, 595), (26, 624)],
    # Behind the knee: hamstring tendons above, the two calf heads below.
    'fossa_hi': [(57, 624), (51, 614), (43, 606), (35, 613), (26, 624)],
    'fossa_lo': [(57, 624), (48, 630), (41, 636), (34, 630), (26, 624)],

    # Lower leg.
    'calf_out': [(62, 624), (64, 640), (68, 660), (70, 678), (69, 696), (65, 716),
                 (59, 738), (55, 752), (52, 762)],
    'calf_in': [(26, 624), (24, 636), (18, 652), (13, 670), (11, 690), (13, 708), (18, 728),
                (24, 748), (27, 762), (28, 772)],
    'calf_low': [(52, 762), (47, 758), (41, 756), (35, 760), (28, 772)],
}


def back_regions():
    """Every muscle group as closed shapes, figure's left half."""
    b = B
    trap = P(b['trap_top'], b['spine'][1:], b['trap_low'][1:])
    rdelt = P(R(b['spine'][1:5]), b['delt_split'][1:], R(b['rdelt_low'])[1:-1])
    sdelt = P(b['delt_out'][:-1], R(b['delt_split']))
    upper = P((57, 184), (48, 190), b['trap_low'][:4], b['lat_top'][1:], (94, 218),
              R(b['rdelt_low'][:4]))
    tri = P(R(b['rdelt_low'])[:5], (94, 218), b['arm_in'], b['tri_low'][1:-1],
            R(b['arm_out'])[:-1])
    fore = P(b['tri_low'], b['fore_out'][1:], b['wrist'][1:], R(b['fore_in'])[1:-1])
    lats = P(b['lat_top'], b['side_hi'][1:], b['lat_front'][1:], b['crest'][3:],
             b['lat_med'][1:], (24, 262))
    obl = P(b['side_lo'], b['crest'][1:3], R(b['lat_front'])[1:-1])
    lower = P(T12, (9, 291), R(b['lat_med']), b['sacrum'][1:-1], (0, 368))
    gmed = P((54, 348), (66, 347), (78, 346), (82, 349), b['hip'], R(b['gmax_top'])[1:-1],
             PSIS, (28, 361), (40, 356))
    gmax = P(R(b['sacrum'][3:]), b['gmax_top'][1:], b['gmax_out'][1:], b['gfold'][1:],
             b['cleft'][1:-1])
    ham = P(b['ham_top'], b['ham_out'][1:], b['fossa_hi'][1:], R(b['ham_in'])[1:-1])
    add = P(R(b['gfold'][-3:]), b['ham_in'][1:], R(b['thigh_in'])[1:-1])
    quad = P((62, 452), (76, 445), (86, 436), b['thigh_out'], R(b['ham_out'])[:-1])
    calf = P(b['thigh_out'][-1:], b['fossa_lo'], b['calf_in'][1:], R(b['calf_low'])[1:],
             R(b['calf_out'])[1:-1])
    return [
        ('traps', [trap]),
        ('rear-delts', [rdelt]),
        ('side-delts', [sdelt]),
        ('upper-back', [upper]),
        ('triceps', [tri]),
        ('forearms', [fore]),
        ('lats', [lats]),
        ('obliques', [obl]),
        ('lower-back', [lower]),
        ('glutes', [gmed, gmax]),
        ('hamstrings', [ham]),
        ('adductors', [add]),
        ('quads', [quad]),
        ('calves', [calf]),
    ]


def back_details():
    """Lighter lines inside the groups: separate muscles, heads and tendons."""
    return [
        # Trapezius: the flat tendon diamond over C7 to T3, and the tendon
        # where the lower fibers turn onto the root of the scapular spine.
        [(0, 134), (6, 142), (9, 154), (6, 166), (0, 174)],
        [(43, 199), (47, 204), (52, 207)],
        # Upper back: infraspinatus over teres minor over teres major, and
        # rhomboid major's lower edge in the triangle of auscultation.
        [(45, 214), (60, 214), (76, 214), (92, 214)],
        [(44, 236), (60, 233), (76, 229), (93, 222)],
        [(30, 246), (35, 252), (40, 255)],
        # Rear delt and side delt: the middle bundles.
        [(76, 172), ARM(30, 4), ARM(60, 10)],
        [ARM(0, 28), ARM(36, 31), ARM(70, 20)],
        # Triceps: long head and lateral head meeting the common tendon.
        [ARM(62, -8), ARM(86, -6), ARM(104, -4)],
        [ARM(104, -16), ARM(97, -5), ARM(104, 12), ARM(124, 14)],
        [ARM(104, -16), ARM(122, -15), ARM(137, -9)],
        # Forearm: olecranon, the back edge of the ulna (flexor carpi
        # ulnaris on one side, extensor carpi ulnaris on the other),
        # brachioradialis and the radial wrist extensors, extensor digitorum,
        # and the two thumb muscles that cross the lower third.
        [FORE(-4, -10), FORE(6, -11), FORE(10, -4)],
        [FORE(10, -7), FORE(40, -11), FORE(80, -10), FORE(116, -8)],
        [FORE(4, 19), FORE(40, 18), FORE(76, 13), FORE(108, 9)],
        [FORE(6, 7), FORE(40, 5), FORE(80, 2), FORE(114, 0)],
        [FORE(62, 5), FORE(84, 11), FORE(104, 14)],
        [FORE(68, -2), FORE(90, 5), FORE(110, 10)],
        # Lower back: the long column of the spinal erectors beside the spine.
        [(9, 296), (13, 314), (19, 334), (22, 350), (19, 360)],
        # Iliotibial band down the outside of the thigh.
        [(93, 436), (86, 470), (79, 515), (71, 565), (63, 614)],
        # Hamstrings: biceps femoris against semitendinosus, and
        # semimembranosus showing on the inner side lower down.
        [(38, 460), (40, 500), (42, 540), (43, 575), (44, 598)],
        [(29, 540), (32, 566), (34, 590), (35, 606)],
        [(54, 520), (56, 560), (56, 592)],
        # Calves: the split between the two heads of gastrocnemius, the
        # lower edges of both heads, and the Achilles tendon.
        [(41, 636), (40, 662), (41, 690), (42, 704)],
        [(15, 714), (26, 727), (38, 731)],
        [(66, 700), (56, 712), (45, 718)],
        [(38, 731), (39, 755)],
        [(45, 718), (44, 754)],
    ]


def back_outline():
    """Lines that are not muscle groups: head, ears, hands, ankles and heels."""
    head = [(37 * math.cos(math.radians(a)), 62 - 46 * math.sin(math.radians(a)))
            for a in range(-40, 221, 6)]
    head = [p for p in head if not (p[1] > 96 and abs(p[0]) < 30)]
    return {
        'head': head,
        'neck': [[(29, 92), (27.5, 102), (27, 110)]],
        # the spinous processes, C7 down to L5, as small marks on the midline
        'spine': [[(0, y), (1.2, y + 3), (0, y + 6)] for y in range(140, 360, 13)],
        'ear': [(35, 56), (41, 58), (43, 68), (41, 81), (36, 87)],
        'hand': [HAND(0, 13), HAND(10, 17), HAND(24, 23), HAND(37, 24), HAND(39, 18),
                 HAND(31, 13), HAND(42, 14), HAND(58, 13), HAND(70, 10), HAND(73, 5),
                 HAND(75, 0), HAND(72, -5), HAND(69, -8), HAND(64, -12), HAND(56, -14),
                 HAND(40, -15), HAND(18, -15), HAND(0, -13)],
        'fingers': [[HAND(46, 6), HAND(68, 6)], [HAND(46, -1), HAND(71, -2)],
                    [HAND(44, -8), HAND(66, -9)]],
        'feet': [[(52, 762), (50, 775), (49, 786), (51, 795), (52, 806), (48, 818), (40, 824),
                  (32, 820), (28, 806), (30, 792), (29, 782), (28, 772)],
                 [(49, 784), (53, 790), (51, 797)], [(30, 786), (27, 792), (29, 798)],
                 [(34, 812), (40, 815), (46, 812)]],
    }


def back_fibers():
    """Fiber direction for hatching: (start, end) pairs, neighbours interpolated."""
    return {
        'traps': [((0, 100), (20, 104)), ((0, 112), (32, 122)), ((0, 126), (56, 138)),
                  ((0, 142), (88, 150)), ((0, 158), (100, 157)), ((0, 178), (88, 167)),
                  ((0, 205), (64, 180)), ((0, 235), (48, 191)), ((0, 265), (44, 196)),
                  ((0, 298), (42, 200))],
        'rear-delts': [((58, 184), ARM(84, 6)), ((72, 177), ARM(84, 9)),
                       ((86, 167), ARM(86, 12)), ((96, 160), ARM(88, 14))],
        'side-delts': [((99, 157), ARM(88, 14)), (ARM(-6, 20), ARM(88, 15)),
                       (ARM(4, 31), ARM(88, 16)), (ARM(22, 36), ARM(88, 17))],
        'upper-back': [((44, 200), (92, 212)), ((41, 214), (93, 218)),
                       ((38, 228), (93, 222)), ((32, 244), (94, 225))],
        'triceps': [(ARM(45, -24), ARM(124, -12)), (ARM(60, -14), ARM(126, -5)),
                    (ARM(80, 18), ARM(126, 5)), (ARM(92, 27), ARM(126, 12))],
        'forearms': [(FORE(0, 28), FORE(118, 12)), (FORE(0, 15), FORE(116, 4)),
                     (FORE(0, 2), FORE(116, -4)), (FORE(6, -24), FORE(116, -12))],
        'lats': [((28, 254), (94, 226)), ((22, 268), (95, 230)), ((30, 300), (97, 238)),
                 ((44, 334), (99, 248)), ((58, 348), (99, 258)), ((76, 346), (97, 272))],
        'obliques': [((86, 296), (80, 344)), ((92, 300), (84, 346))],
        'lower-back': [((4, 364), (6, 300)), ((14, 364), (16, 290)), ((28, 360), (28, 300))],
        'glutes': [((24, 366), (90, 428)), ((8, 376), (84, 438)), ((4, 404), (74, 447)),
                   ((5, 426), (56, 453)), ((58, 350), (92, 394)), ((82, 349), (93, 388))],
        'hamstrings': [((22, 456), (26, 620)), ((36, 459), (44, 598)), ((52, 459), (54, 604)),
                       ((64, 457), (57, 622))],
        'adductors': [((8, 448), (22, 604)), ((18, 452), (26, 600))],
        'quads': [((70, 450), (62, 616)), ((90, 436), (64, 610))],
        'calves': [((26, 628), (30, 730)), ((36, 636), (40, 732)), ((46, 636), (45, 720)),
                   ((58, 628), (48, 716)), ((18, 690), (34, 760)), ((65, 690), (48, 760))],
    }


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def to_xy(p, side):
    dx, y = p
    return (CX - dx if side == 'L' else CX + dx, y)


def dedupe(p):
    out = []
    for q in p:
        if not out or math.hypot(out[-1][0] - q[0], out[-1][1] - q[1]) > 0.3:
            out.append(q)
    if len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < 0.3:
        out.pop()
    return out


def smooth(points, closed=False):
    """Catmull-Rom through the points, written as SVG cubic Beziers."""
    Pn = points
    n = len(Pn)

    def corner(i):
        # A point where the line turns sharply (where two muscles meet at an
        # angle) stays a corner instead of being rounded into a spike.
        if not closed and (i == 0 or i == n - 1):
            return False
        a, b, c = Pn[(i - 1) % n], Pn[i], Pn[(i + 1) % n]
        v1 = (b[0] - a[0], b[1] - a[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        if l1 == 0 or l2 == 0:
            return True
        cos = (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)
        return cos < math.cos(math.radians(62))

    sharp = [corner(i) for i in range(n)]
    out = ['M%.1f %.1f' % Pn[0]]
    for i in range(n if closed else n - 1):
        p0 = Pn[(i - 1) % n] if (closed or i > 0) else Pn[i]
        p1, p2 = Pn[i], Pn[(i + 1) % n]
        p3 = Pn[(i + 2) % n] if (closed or i + 2 < n) else p2
        if sharp[i]:
            p0 = p1
        if sharp[(i + 1) % n]:
            p3 = p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.append('C%.1f %.1f %.1f %.1f %.1f %.1f' % (*c1, *c2, *p2))
    if closed:
        out.append('Z')
    return ''.join(out)


def wobble(points, rng, amount=0.55):
    """A hand's wobble: nudge each point a little and add nudged midpoints."""
    out = []
    for i, (x, y) in enumerate(points):
        out.append((x + rng.uniform(-amount, amount), y + rng.uniform(-amount, amount)))
        if i < len(points) - 1:
            nx, ny = points[i + 1]
            if math.hypot(nx - x, ny - y) > 16:
                out.append(((x + nx) / 2 + rng.uniform(-amount, amount),
                            (y + ny) / 2 + rng.uniform(-amount, amount)))
    return out


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def centroid(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return (sum(xs) / len(xs), sum(ys) / len(ys)), max(max(xs) - min(xs), max(ys) - min(ys))


def hatch(pairs, rng, centre, size, per_gap=4):
    """Short pen strokes laid along the fibers. Each fiber line between
    neighbouring (start, end) pairs is walked from start to end; strokes are
    dense on the shadow side of the muscle and thin out toward the light."""
    lines = []
    for (s0, e0), (s1, e1) in zip(pairs, pairs[1:]):
        for k in range(per_gap):
            t = (k + rng.uniform(0.25, 0.75)) / per_gap
            lines.append((lerp(s0, s1, t), lerp(e0, e1, t)))
    out = []
    for s, e in lines:
        L = math.hypot(e[0] - s[0], e[1] - s[1])
        if L < 4:
            continue
        ux, uy = (e[0] - s[0]) / L, (e[1] - s[1]) / L
        nx, ny = -uy, ux
        bow = rng.uniform(-1.5, 1.5)
        pos = rng.uniform(0, 4)
        while pos < L:
            seg = rng.uniform(7, 15)
            t0, t1 = pos / L, min(L, pos + seg) / L
            mid = lerp(s, e, (t0 + t1) / 2)
            shade = ((mid[0] - centre[0]) * -LIGHT[0] + (mid[1] - centre[1]) * -LIGHT[1]) / size
            keep = 0.12 + 1.6 * (shade + 0.15)
            if rng.random() < keep:
                p = []
                for j in range(3):
                    t = t0 + (t1 - t0) * j / 2
                    q = lerp(s, e, t)
                    b = bow * math.sin(math.pi * t) + (0.6 if j == 1 else 0) * rng.uniform(-1, 1)
                    p.append((q[0] + nx * b, q[1] + ny * b))
                out.append(p)
            pos += seg + rng.uniform(1.5, 5) * (1.6 - min(1.0, max(0.0, shade + 0.5)))
    return out


def shadow_side(poly, rng, offset=0.7):
    """Pieces of a closed outline that face away from the light, nudged
    outward: a second pass of the pen that makes the shadow edges heavier."""
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
               for i in range(len(poly)))
    sign = 1 if area > 0 else -1
    runs, run = [], []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        # outward normal
        ox, oy = sign * dy / L, -sign * dx / L
        facing = ox * -LIGHT[0] + oy * -LIGHT[1]
        if facing > 0.35:
            if not run:
                run.append((a[0] + ox * offset, a[1] + oy * offset))
            run.append((b[0] + ox * offset, b[1] + oy * offset))
        elif run:
            runs.append(run)
            run = []
    if run:
        runs.append(run)
    return [r for r in runs if len(r) > 1]


def dense(poly, step=4):
    """The same closed outline with extra points, for finding shadow edges."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        k = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for j in range(k):
            out.append(lerp(a, b, j / k))
    return out


def polyline(p):
    return 'M' + ' '.join('%.1f %.1f' % q for q in p)


def build(view, regions, details, outline, fibers, seed):
    rng = random.Random(seed)
    defs, fills, ink, hatching, detail_ink, out_ink, heavy = [], [], [], [], [], [], []

    for gid, polys in regions:
        ds = []
        for side in ('L', 'R'):
            for poly in polys:
                p = dedupe([to_xy(q, side) for q in poly])
                ds.append(smooth(p, closed=True))
                # Each shape's outline is inked on its own, so a border two
                # muscles share gets two slightly different strokes: darker
                # where muscles meet, like a pen going over a line twice.
                w = wobble(p, rng)
                ink.append(smooth(w, closed=True))
                for run in shadow_side(dense(w), rng):
                    heavy.append(smooth(run))
                if gid in fibers:
                    c, size = centroid(p)
                    pairs = [(to_xy(s, side), to_xy(e, side)) for s, e in fibers[gid]]
                    for ln in hatch(pairs, rng, c, size):
                        hatching.append((gid, polyline(ln)))
        rid = 'mm-%s-%s' % (view, gid)
        fills.append('<path id="%s" class="mm-muscle" data-group="%s" d="%s"/>'
                     % (rid, gid, ''.join(ds)))
        defs.append('<clipPath id="%s-c"><use href="#%s"/></clipPath>' % (rid, rid))

    by_group = {}
    for gid, d in hatching:
        by_group.setdefault(gid, []).append(d)
    hatch_svg = ''.join('<path clip-path="url(#mm-%s-%s-c)" d="%s"/>' % (view, g, ''.join(ds))
                        for g, ds in by_group.items())

    for line in details:
        for side in ('L', 'R'):
            detail_ink.append(smooth(wobble([to_xy(q, side) for q in line], rng, 0.4)))

    def ink_line(points, closed=False):
        for side in ('L', 'R'):
            out_ink.append(smooth(wobble([to_xy(q, side) for q in points], rng), closed))

    out_ink.append(smooth(wobble([to_xy(q, 'L') for q in outline['head']], rng)))
    for key in ('neck', 'fingers', 'feet'):
        for line in outline[key]:
            ink_line(line)
    for line in outline.get('spine', []):
        detail_ink.append(smooth(wobble([to_xy(q, 'L') for q in line], rng, 0.3)))
    ink_line(outline['ear'])
    ink_line(outline['hand'])

    css = ('.mm-muscle{fill:var(--mm-fill,transparent)}'
           '.mm-ink{fill:none;stroke:var(--pen,#22347F);stroke-linecap:round;stroke-linejoin:round}'
           '.mm-line{stroke-width:1.5}.mm-heavy{stroke-width:1.2}.mm-out{stroke-width:2}'
           '.mm-detail{stroke-width:1;opacity:.85}.mm-hatch{stroke-width:.7;opacity:.7}')
    return ''.join([
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" class="mm mm-%s">' % (W, H, view),
        '<style>%s</style>' % css,
        '<g class="mm-regions">%s</g>' % ''.join(fills),
        '<defs>%s</defs>' % ''.join(defs),
        '<g class="mm-ink mm-hatch">%s</g>' % hatch_svg,
        '<g class="mm-ink mm-detail"><path d="%s"/></g>' % ''.join(detail_ink),
        '<g class="mm-ink mm-line"><path d="%s"/></g>' % ''.join(ink),
        '<g class="mm-ink mm-heavy"><path d="%s"/></g>' % ''.join(heavy),
        '<g class="mm-ink mm-out"><path d="%s"/></g>' % ''.join(out_ink),
        '</svg>',
    ])


def svg_back():
    return build('back', back_regions(), back_details(), back_outline(), back_fibers(), 409)


if __name__ == '__main__':
    out = ROOT / 'art' / 'muscle-back.svg'
    s = svg_back()
    out.write_text(s)
    print('wrote', out.relative_to(ROOT), len(s), 'bytes')
