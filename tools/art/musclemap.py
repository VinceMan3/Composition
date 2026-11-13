"""
Draws the muscle map: a front and a back view of a lifter, in graphite pencil,
with every muscle split into its parts so the app can light each one up.

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
- Style (Vince's guide): graphite on paper, edges found by the light rather
  than outlined, soft creases between the parts of a muscle, limbs shaded as
  cylinders, red glossy highlights added by the app.
- Each group is cut into its parts along the lines in SPLITS; the pieces
  never overlap. The checks in tools/test/run.py confirm every part is drawn,
  tappable and separate.
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


ARM = frame(84, 166, 30)        # from the head of the humerus
FORE = frame(157, 292.4, 36)    # from the elbow
HAND = frame(228.7, 391.1, 32)  # from the wrist


def P(*items):
    """A run of points: a mix of (dx, y) tuples and lists of them."""
    out = []
    for it in items:
        out.extend(it if isinstance(it, list) else [it])
    return out


def R(p):
    return list(reversed(p))


# ---------------------------------------------------------------------------
# The build: Classic Physique proportions, measured in head heights (100)
# ---------------------------------------------------------------------------
# Neck about 0.62 wide, shoulders (across the delts, arms down) about 2.35,
# waist about 1.2, hips about 1.5, with the quad sweep reaching out past the
# hips so the outline makes an X. Measured from Vince's reference photos of
# a Classic Physique competitor and checked against the eight-heads canon.

# ---------------------------------------------------------------------------
# BACK VIEW: borders shared between muscles (figure's left half)
# ---------------------------------------------------------------------------

ACR = (92, 152)                 # tip of the acromion
ACR_ANGLE = (88, 157)           # angle of the acromion, where the rear delt starts
SPINE_ROOT = (40, 193)          # root of the scapular spine
T12 = (0, 302)                  # lowest point of the trapezius
AX = (84.5, 219)                # the armpit, seen from behind
DELT_TIP = ARM(94, 21)          # deltoid tuberosity on the humerus
ELB_OUT = ARM(126, 27)          # lateral supracondylar ridge
EPI_IN = ARM(144, -25)          # medial epicondyle
PSIS = (15, 365)                # the dimple over the back of the hip bone

B = {
    # Trapezius: from the back of the skull, down the side of the neck, out
    # over the shoulder to the acromion.
    'trap_top': [(0, 99), (11, 99.5), (21, 102), (28, 108), (31, 116), (38, 124),
                 (50, 132), (64, 138), (78, 144), ACR],
    # Spine of the scapula. The trapezius ends on its upper lip, the rear
    # delt starts from its lower lip.
    'spine': [ACR, ACR_ANGLE, (77, 164), (65, 172), (54, 180), (46, 187), SPINE_ROOT],
    # Lower trapezius, from the root of the spine to its point at T12.
    'trap_low': [SPINE_ROOT, (39, 208), (35, 228), (28, 250), (19, 272), (9, 290), T12],

    # Deltoid, over the cap of the shoulder down to its tuberosity.
    'delt_out': [ACR, ARM(-9, 20), ARM(2, 33), ARM(20, 39), ARM(42, 38), ARM(62, 32),
                 ARM(78, 27), DELT_TIP],
    # Line between the rear delt and the side delt.
    'delt_split': [ACR_ANGLE, ARM(8, 24), ARM(34, 28), ARM(64, 25), DELT_TIP],
    # Lower edge of the rear delt.
    'rdelt_low': [(54, 180), (62, 193), (73, 203), (85, 209), ARM(44, -10), ARM(60, -2),
                  ARM(76, 8), DELT_TIP],

    # Upper arm: inside and outside edges.
    'arm_in': [AX, ARM(58, -28), ARM(82, -31), ARM(106, -29), ARM(128, -26), EPI_IN],
    'arm_out': [DELT_TIP, ARM(102, 28), ARM(114, 29), ELB_OUT],
    # Bottom of the triceps, around the olecranon, then up the outside of
    # the arm where brachioradialis starts on the supracondylar ridge.
    'tri_low': [EPI_IN, FORE(-6, -16), FORE(2, -6), FORE(1, 8), ARM(138, 18), ELB_OUT],

    # Forearm, seen from behind with the palm forward: the extensors.
    'fore_out': [ELB_OUT, FORE(2, 31), FORE(18, 35), FORE(40, 32), FORE(68, 23),
                 FORE(96, 16), FORE(120, 14)],
    'fore_in': [EPI_IN, FORE(8, -26), FORE(28, -29), FORE(56, -24), FORE(88, -16),
                FORE(120, -13)],
    'wrist': [FORE(120, 14), FORE(122, 0), FORE(120, -13)],

    # Lats: top edge, from under the lower trapezius over the bottom corner
    # of the scapula to the armpit.
    'lat_top': [(28, 250), (40, 248), (52, 245), (64, 239), (76, 230), AX],
    # Side of the torso: the lats sweep out, then in hard to a small waist.
    'side_hi': [AX, (90, 234), (91, 250), (89, 266), (84, 281), (77, 295)],
    'side_lo': [(77, 295), (69, 308), (63, 320), (60, 332), (61, 344), (64, 352)],
    # Front edge of the lat, where the external oblique shows at the flank.
    'lat_front': [(77, 295), (65, 311), (57, 327), (53, 342), (55, 352)],
    # Iliac crest, outer part.
    'crest': [(64, 352), (60, 355), (55, 352), (48, 353), (42, 354)],
    # Where the lat's muscle turns into the flat sheet over the lower back.
    'lat_med': [(42, 354), (36, 338), (29, 318), (23, 296), (19, 272)],
    # Back of the hip bone and top of the sacrum.
    'sacrum': [(42, 354), (32, 359), (22, 362), PSIS, (7, 367), (0, 368)],

    # Hip and glutes.
    'hip': [(64, 352), (69, 364), (73, 378), (76, 392), (77, 404)],
    'gmax_top': [PSIS, (28, 370), (42, 376), (56, 383), (68, 392), (77, 404)],
    'gmax_out': [(77, 404), (78, 416), (77, 428), (71, 439), (62, 447)],
    'gfold': [(62, 447), (56, 450), (50, 452), (38, 454), (26, 452), (17, 448), (10, 444),
              (5, 440)],
    'cleft': [(5, 440), (3, 420), (2, 400), (1, 380), (0, 368)],

    # Thigh: the outer quad sweeps out past the hip.
    'thigh_out': [(77, 428), (82, 444), (87, 462), (89, 482), (88, 504), (85, 528),
                  (80, 552), (74, 576), (68, 596), (63, 612), (61, 626)],
    'thigh_in': [(5, 440), (7, 452), (9, 470), (11, 494), (13, 520), (16, 548),
                 (19, 576), (22, 600), (24, 614), (26, 624)],
    # Hamstrings: outer edge (biceps femoris against vastus lateralis and the
    # iliotibial band), inner edge (semitendinosus against adductor magnus
    # and gracilis).
    'ham_top': [(17, 448), (26, 452), (38, 454), (50, 452), (56, 450)],
    'ham_out': [(56, 450), (64, 474), (69, 502), (70, 532), (67, 562), (62, 592), (57, 624)],
    'ham_in': [(17, 448), (22, 476), (26, 506), (28, 538), (27, 568), (26, 596), (26, 624)],
    # Behind the knee: hamstring tendons above, the two calf heads below.
    'fossa_hi': [(57, 624), (51, 614), (43, 606), (35, 613), (26, 624)],
    'fossa_lo': [(57, 624), (48, 630), (41, 636), (34, 630), (26, 624)],

    # Lower leg.
    'calf_out': [(61, 626), (63, 638), (67, 654), (70, 670), (69, 688), (64, 706),
                 (58, 724), (54, 740), (51, 754), (51, 762)],
    'calf_in': [(26, 624), (22, 638), (16, 654), (12, 672), (11, 690), (13, 708), (17, 724),
                (22, 740), (26, 756), (28, 772)],
    'calf_low': [(51, 762), (47, 758), (41, 756), (35, 760), (28, 772)],
}


def back_regions():
    """Every muscle group as closed shapes, figure's left half."""
    b = B
    trap = P(b['trap_top'], b['spine'][1:], b['trap_low'][1:])
    rdelt = P(R(b['spine'][1:5]), b['delt_split'][1:], R(b['rdelt_low'])[1:-1])
    sdelt = P(b['delt_out'][:-1], R(b['delt_split']))
    upper = P(b['spine'][4:6], b['trap_low'][:4], b['lat_top'][1:], (85, 214),
              R(b['rdelt_low'][:4]))
    tri = P(R(b['rdelt_low'])[:5], (85, 214), b['arm_in'], b['tri_low'][1:-1],
            R(b['arm_out'])[:-1])
    fore = P(b['tri_low'], b['fore_out'][1:], b['wrist'][1:], R(b['fore_in'])[1:-1])
    lats = P(b['lat_top'], b['side_hi'][1:], b['lat_front'][1:], b['crest'][3:],
             b['lat_med'][1:], (23.5, 261))
    obl = P(b['side_lo'], b['crest'][1:3], R(b['lat_front'])[1:-1])
    lower = P(T12, (9, 290), R(b['lat_med']), b['sacrum'][1:-1], (0, 368))
    gmed = P(R(b['crest'])[:-1], b['hip'], R(b['gmax_top'])[1:-1], PSIS,
             R(b['sacrum'][1:3]))
    gmax = P(R(b['sacrum'][3:]), b['gmax_top'][1:], b['gmax_out'][1:], b['gfold'][1:],
             b['cleft'][1:-1])
    ham = P(b['ham_top'], b['ham_out'][1:], b['fossa_hi'][1:], R(b['ham_in'])[1:-1])
    add = P(R(b['gfold'][-3:]), b['ham_in'][1:], R(b['thigh_in'])[1:-1])
    quad = P((56, 450), R(b['gmax_out'])[:2], b['thigh_out'], R(b['ham_out'])[:-1])
    # The hollow behind the knee belongs to the calf shape, so the only hard
    # line across the knee is the hamstring tendons; the tops of the two calf
    # heads are drawn as lighter lines.
    calf = P(b['thigh_out'][-1:], b['fossa_hi'], b['calf_in'][1:], R(b['calf_low'])[1:],
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
        [(40, 196), (44, 201), (49, 204)],
        # Upper back: infraspinatus over teres minor over teres major, and
        # rhomboid major's lower edge in the triangle of auscultation.
        # Rear delt and side delt: the middle bundles.
        [(70, 168), ARM(30, 0), ARM(62, 8)],
        [ARM(0, 28), ARM(36, 32), ARM(70, 20)],
        # Triceps: long head and lateral head meeting the common tendon.
        [ARM(84, 26), ARM(100, 17), ARM(113, 9), ARM(126, 5)],
        [ARM(94, -26), ARM(107, -15), ARM(118, -7), ARM(128, -2)],
        # Forearm: olecranon, the back edge of the ulna (flexor carpi
        # ulnaris on one side, extensor carpi ulnaris on the other),
        # brachioradialis and the radial wrist extensors, extensor digitorum,
        # and the two thumb muscles that cross the lower third.
        [FORE(-4, -10), FORE(6, -11), FORE(10, -4)],
        [FORE(6, 7), FORE(40, 5), FORE(80, 2), FORE(116, 0)],
        [FORE(64, 5), FORE(86, 11), FORE(106, 14)],
        [FORE(70, -2), FORE(92, 5), FORE(112, 10)],
        # Lower back: the long column of the spinal erectors beside the spine.
        [(9, 296), (13, 314), (18, 334), (20, 350), (17, 362)],
        # Iliotibial band down the outside of the thigh.
        [(76, 432), (82, 470), (79, 515), (71, 565), (63, 612)],
        # Hamstrings: biceps femoris against semitendinosus, the long and
        # short heads of biceps femoris, and semimembranosus on the inner side.
        [(52, 520), (55, 560), (55, 592)],
        # Calves: the split between the two heads of gastrocnemius, the
        # lower edges of both heads, and the Achilles tendon.
        [(55, 628), (48, 632), (41, 637)], [(28, 627), (34, 632), (41, 637)],
        [(38, 731), (39, 755)],
        [(45, 718), (44, 754)],
    ]


def back_fibers():
    """Fiber direction for hatching: (start, end) pairs, neighbours interpolated."""
    return {
        'traps': [((0, 100), (20, 103)), ((0, 112), (31, 117)), ((0, 126), (50, 133)),
                  ((0, 142), (78, 145)), ((0, 158), (90, 155)), ((0, 178), (77, 165)),
                  ((0, 205), (58, 178)), ((0, 235), (45, 190)), ((0, 265), (41, 194)),
                  ((0, 298), (39, 197))],
        'rear-delts': [((54, 181), ARM(86, 4)), ((66, 172), ARM(88, 8)),
                       ((78, 164), ARM(90, 11)), ((87, 158), ARM(92, 13))],
        'side-delts': [((90, 154), ARM(92, 13)), (ARM(-6, 20), ARM(92, 14)),
                       (ARM(4, 31), ARM(92, 15)), (ARM(22, 37), ARM(92, 16))],
        'upper-back': [((41, 198), (84, 208)), ((39, 212), (84, 213)),
                       ((36, 226), (84, 217)), ((30, 244), (84.5, 219))],
        'triceps': [(ARM(46, -24), ARM(126, -12)), (ARM(62, -14), ARM(128, -5)),
                    (ARM(82, 18), ARM(128, 5)), (ARM(94, 27), ARM(128, 12))],
        'forearms': [(FORE(0, 28), FORE(120, 12)), (FORE(0, 15), FORE(118, 4)),
                     (FORE(0, 2), FORE(118, -4)), (FORE(6, -24), FORE(118, -12))],
        'lats': [((27, 253), (84.5, 219)), ((21, 267), (86, 224)), ((27, 300), (89, 232)),
                 ((38, 334), (90, 244)), ((46, 353), (89, 256)), ((58, 352), (85, 270))],
        'obliques': [((72, 302), (60, 348)), ((68, 306), (57, 350))],
        'lower-back': [((4, 364), (6, 300)), ((14, 364), (15, 288)), ((26, 360), (26, 300))],
        'glutes': [((22, 368), (76, 430)), ((8, 376), (70, 440)), ((4, 404), (60, 448)),
                   ((4, 426), (44, 453)), ((46, 355), (76, 398)), ((62, 354), (77, 392))],
        'hamstrings': [((19, 452), (26, 620)), ((34, 455), (43, 602)), ((48, 454), (54, 606)),
                       ((56, 452), (57, 622))],
        'adductors': [((7, 446), (22, 604)), ((15, 450), (25, 600))],
        'quads': [((60, 450), (62, 616)), ((76, 432), (64, 610))],
        'calves': [((26, 628), (30, 730)), ((36, 634), (40, 732)), ((46, 634), (45, 720)),
                   ((58, 628), (48, 716)), ((15, 690), (34, 760)), ((66, 690), (48, 760))],
    }


# ---------------------------------------------------------------------------
# FRONT VIEW: the same outline as the back, so the figure matches when the
# page turns. Figure's left half again; the left half of the figure is drawn
# on the viewer's right in a front view, but the shapes are mirrored anyway.
# ---------------------------------------------------------------------------

STERNAL_NOTCH = (0, 148)
ASIS = (60, 368)                # the point of the hip bone at the front
PUBIC = (12, 416)               # pubic tubercle
PEC_INS = ARM(38, -12)          # where the pec's tendon goes under the delt

F = {
    'trap_top': B['trap_top'][4:],                 # the slope of the trapezius
    # Collarbone, sternal end to the acromion: an S curve.
    'clav': [(6, 150), (20, 152), (34, 150), (48, 146), (58, 147), (72, 147), (84, 149), ACR],
    # Front edge of the trapezius, down to the outer third of the collarbone.
    'trap_front': [(31, 116), (35, 130), (45, 142), (58, 147)],
    # Deltoid: outline as from behind; the line between front and side delt;
    # and the front delt's lower edge, from the deltopectoral groove to the
    # deltoid tuberosity.
    'delt_out': B['delt_out'],
    'delt_split': [(86, 150), ARM(6, 22), ARM(32, 25), ARM(64, 24), DELT_TIP],
    'dp_groove': [(58, 147), (62, 168), (71, 186), (81, 199), PEC_INS],
    'fdelt_low': [PEC_INS, ARM(52, -6), ARM(60, -2), ARM(76, 8), DELT_TIP],
    # Pec major: lower edge, from the armpit fold down and in to the sternum.
    'pec_low': [AX, (78, 230), (68, 242), (54, 250), (40, 253), (30, 252), (22, 250),
                (10, 243), (3, 236), (0, 236)],
    # Lat at the side, seen from the front, and the torso outline.
    'lat_front': [(77, 295), (80, 280), (83, 262), (84, 244), (82, 230), AX],
    'side_hi': B['side_hi'],
    'side_lo': B['side_lo'],
    # Rectus abdominis: the outer edge (linea semilunaris).
    'semilunar': [(30, 252), (31, 280), (30, 310), (27, 340), (22, 368), (17, 392),
                  (13, 408), PUBIC],
    # Inguinal line, the point of the hip down to the pubis.
    'inguinal': [ASIS, (50, 380), (40, 391), (30, 400), (20, 408), PUBIC],
    'hip': [(64, 352), (69, 364), (73, 378), (76, 392), (77, 404), (77, 428)],
    # Sartorius, the long strap from the point of the hip to the inside of
    # the knee. Its inner edge is where the adductors stop.
    'sart_in': [ASIS, (48, 394), (38, 424), (29, 456), (21, 488), (15, 512), (13, 520)],
    'sart_out': [ASIS, (53, 396), (45, 428), (37, 462), (29, 496), (23, 528), (20, 556),
                 (19, 576)],
    'thigh_out': B['thigh_out'][:9] + [(66, 603)],
    'thigh_in': B['thigh_in'],
    # Bottom of the quads around the kneecap.
    'quad_low': [(66, 603), (56, 601), (47, 603), (40, 606), (33, 608), (27, 614), (24, 614)],
    # Lower leg.
    'calf_out': B['calf_out'],
    'calf_in': B['calf_in'],
    # Inner edge of the tibia: the calf shows inside it.
    'tibia_in': [(25, 636), (31, 652), (30, 680), (29, 710), (28, 740), (24, 750)],
    # Outer calf, behind the fibular muscles.
    'calf_out_in': [(63, 638), (61, 650), (64, 666), (65, 682), (63, 700), (58, 718), (56, 728)],

    # Arms, palms forward: the biceps' inner edge (medial bicipital groove)
    # and the V at the front of the elbow, brachioradialis on the outside
    # and pronator teres on the inside, with the biceps tendon dipping in.
    'bi_med': [ARM(52, -6), ARM(70, -15), ARM(90, -19), ARM(110, -18), ARM(128, -14)],
    'arm_in': B['arm_in'],
    'arm_out': B['arm_out'],
    'elbow_v': [ELB_OUT, FORE(0, 14), FORE(12, 6), FORE(18, 0), FORE(10, -8), FORE(0, -16), EPI_IN],
    'fore_out': B['fore_out'],
    'fore_in': B['fore_in'],
    'wrist': B['wrist'],
}


def front_regions():
    f = F
    trap = P(f['trap_top'], R(f['clav'])[:4], R(f['trap_front'])[1:-1])
    fdelt = P(f['clav'][4:7], f['delt_split'], R(f['fdelt_low'])[1:], R(f['dp_groove'])[1:-1])
    sdelt = P(f['delt_out'][:-1], R(f['delt_split']))
    chest = P(f['clav'][:5], f['dp_groove'][1:], f['pec_low'], STERNAL_NOTCH)
    lats = P(f['side_hi'], f['lat_front'][1:-1])
    # obliques and serratus: under the pec, in front of the lat, beside the abs
    obl = P((30, 252), (40, 253), (54, 250), (68, 242), (78, 230), AX,
            R(f['lat_front'])[1:], f['side_lo'][1:], ASIS, f['inguinal'][1:],
            R(f['semilunar'])[1:-1])
    abs_ = P((0, 236), (3, 236), (10, 243), (22, 250), f['semilunar'], (6, 419), (0, 420))
    bi = P(f['fdelt_low'][1:], f['arm_out'][1:], f['elbow_v'][1:], ARM(128, -26),
           R(f['bi_med'])[:-1])
    tri = P(f['arm_in'][:5], R(f['bi_med']), PEC_INS)
    fore = P(f['elbow_v'], f['fore_in'][1:], R(f['wrist'])[1:], R(f['fore_out'])[1:-1])
    quad = P((64, 352), f['hip'][1:], f['thigh_out'][1:], f['quad_low'][1:],
             (22, 600), (19, 576), (16, 548), R(f['sart_in']))
    add = P(f['inguinal'], (5, 440), f['thigh_in'][1:5], R(f['sart_in'])[1:-1])
    calf_in = P(f['tibia_in'][:1], f['calf_in'][2:8], R(f['tibia_in'])[:-1])
    calf_out = P(f['calf_out'][1:7], R(f['calf_out_in']))
    return [
        ('traps', [trap]),
        ('front-delts', [fdelt]),
        ('side-delts', [sdelt]),
        ('chest', [chest]),
        ('lats', [lats]),
        ('obliques', [obl]),
        ('abs', [abs_]),
        ('biceps', [bi]),
        ('triceps', [tri]),
        ('forearms', [fore]),
        ('quads', [quad]),
        ('adductors', [add]),
        ('calves', [calf_in, calf_out]),
        # Tibialis anterior, beside the front edge of the shin bone.
        ('shins', [[(40, 650), (46, 646), (52, 646), (56, 680), (53, 720), (45, 760), (38, 774),
                    (35, 766), (37, 730), (39, 690)]]),
    ]


def front_details():
    return [
        # Neck: sternocleidomastoid, its sternal and collarbone heads.
        # Pec: the line between the collarbone head and the sternal head.
        # Delts: the middle bundles.
        [ARM(0, 27), ARM(34, 31), ARM(70, 24)],
        [(74, 152), ARM(30, 6), ARM(60, 10)],
        # Serratus: the fingers on the ribs between the lat and the oblique.
        [(84, 248), (76, 250), (68, 254)],
        [(83, 262), (74, 264), (64, 269)],
        [(81, 276), (72, 279), (62, 285)],
        [(78, 289), (70, 293), (60, 299)],
        # External oblique: where its muscle turns into flat tendon.
        [ASIS, (48, 358), (36, 348), (28, 340)],
        # Abs: the three tendinous lines across the rectus.
        # Biceps: its outer edge against brachialis, and the two heads.
        # Forearm: brachioradialis, flexor carpi radialis, the long finger
        # flexors and flexor carpi ulnaris, and pronator teres crossing.
        [FORE(20, -2), FORE(60, 2), FORE(116, 2)],
        [FORE(12, -8), FORE(60, -7), FORE(116, -4)],
        [FORE(4, -20), FORE(60, -17), FORE(116, -10)],
        [FORE(0, -16), FORE(26, -2), FORE(48, 10)],
        # Quads: rectus femoris down the middle, vastus lateralis outside,
        # the vastus medialis teardrop, tensor fasciae latae at the hip, and
        # the sartorius' outer edge.
        [(21, 548), (29, 562), (35, 582), (37, 600)],
        # Adductors: adductor longus, and pectineus beside it.
        # The shin bone's front edge and the kneecap's tendon.
        # Lower leg: the shin (tibialis anterior and the long toe extensor).
    ]


def front_fibers():
    return {
        'traps': [((31, 118), (58, 147)), ((38, 124), (76, 148)), ((52, 134), (90, 152))],
        'front-delts': [((62, 148), ARM(90, 14)), ((72, 148), ARM(92, 17)),
                        ((84, 150), ARM(94, 20))],
        'side-delts': [((90, 154), ARM(94, 21)), (ARM(-6, 20), ARM(94, 22)),
                       (ARM(4, 31), ARM(94, 23)), (ARM(22, 37), ARM(94, 24))],
        'chest': [((56, 148), (86, 197)), ((36, 151), (88, 199)), ((14, 151), (90, 201)),
                  ((2, 165), (91, 203)), ((2, 190), (91, 206)), ((2, 215), (89, 210)),
                  ((6, 238), (87, 214)), ((24, 250), (85, 218)), ((48, 251), (84.5, 219))],
        'lats': [((78, 295), (85, 224)), ((84, 290), (91, 240))],
        'obliques': [((84, 240), (34, 282)), ((84, 270), (31, 320)), ((76, 300), (28, 350)),
                     ((64, 330), (24, 384)), ((62, 360), (16, 414))],
        'abs': [((2, 238), (2, 430)), ((14, 245), (7, 430)), ((28, 252), (12, 426))],
        'biceps': [(ARM(54, -6), ARM(144, -4)), (ARM(70, -14), ARM(142, -6)),
                   (ARM(70, 8), ARM(144, 2)), (ARM(96, 26), ARM(140, 12))],
        'triceps': [(ARM(48, -22), ARM(126, -24)), (ARM(56, -29), ARM(126, -27))],
        'forearms': [(FORE(0, 26), FORE(120, 12)), (FORE(12, 6), FORE(118, 2)),
                     (FORE(0, -16), FORE(118, -6)), (FORE(6, -24), FORE(118, -12))],
        'quads': [((80, 430), (64, 600)), ((70, 400), (54, 600)), ((54, 380), (42, 604)),
                  ((40, 440), (32, 608)), ((20, 540), (26, 612))],
        'adductors': [((14, 418), (14, 520)), ((26, 404), (18, 500)), ((42, 390), (24, 480))],
        'calves': [((20, 650), (22, 740)), ((66, 660), (60, 720))],
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


def _segments(points, closed=False):
    """Catmull-Rom through the points as cubic Bezier segments (p1, c1, c2, p2).
    A point where the line turns sharply (where two muscles meet at an
    angle) stays a corner instead of being rounded into a spike."""
    Pn = points
    n = len(Pn)

    def corner(i):
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
    segs = []
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
        segs.append((p1, c1, c2, p2))
    return segs


def smooth(points, closed=False):
    """Catmull-Rom through the points, written as SVG cubic Beziers."""
    segs = _segments(points, closed)
    out = ['M%.1f %.1f' % points[0]]
    for p1, c1, c2, p2 in segs:
        out.append('C%.1f %.1f %.1f %.1f %.1f %.1f' % (*c1, *c2, *p2))
    if closed:
        out.append('Z')
    return ''.join(out)


def sample(points, closed=False, step=2.0):
    """The same curve as smooth(), as a dense list of points."""
    out = []
    for p1, c1, c2, p2 in _segments(points, closed):
        L = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        k = max(2, int(L / step))
        for j in range(k):
            t = j / k
            mt = 1 - t
            out.append((mt ** 3 * p1[0] + 3 * mt * mt * t * c1[0] + 3 * mt * t * t * c2[0] + t ** 3 * p2[0],
                        mt ** 3 * p1[1] + 3 * mt * mt * t * c1[1] + 3 * mt * t * t * c2[1] + t ** 3 * p2[1]))
    if not closed:
        out.append(points[-1])
    return out


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


def shade_axis(pc):
    """How a shape takes the light: its centre, the direction toward the
    light across it, and half its depth along that direction. A long shape
    turns like a cylinder (across its width); a round one straight away from
    the light."""
    rect = list(pc.minimum_rotated_rectangle.exterior.coords)[:4]
    e1 = (rect[1][0] - rect[0][0], rect[1][1] - rect[0][1])
    e2 = (rect[2][0] - rect[1][0], rect[2][1] - rect[1][1])
    l1, l2 = math.hypot(*e1), math.hypot(*e2)
    cx = sum(q[0] for q in rect) / 4
    cy = sum(q[1] for q in rect) / 4
    long_, short = (e1, l2) if l1 >= l2 else (e2, l1)
    longest = max(l1, l2)
    dirx, diry = LIGHT
    if longest > 1.4 * short and longest > 0:
        ax, ay = long_[0] / longest, long_[1] / longest
        along = LIGHT[0] * ax + LIGHT[1] * ay
        dirx, diry = LIGHT[0] - along * ax * 0.8, LIGHT[1] - along * ay * 0.8
        n = math.hypot(dirx, diry) or 1
        return cx, cy, dirx / n, diry / n, short * 0.58
    return cx, cy, dirx, diry, longest * 0.55


def hatch(pairs, rng, centre, size, per_gap=4, axis=None):
    """Short pen strokes laid along the fibers. Each fiber line between
    neighbouring (start, end) pairs is walked from start to end; strokes are
    dense on the shadow side of the muscle and thin out toward the light."""
    lines = []
    for (s0, e0), (s1, e1) in zip(pairs, pairs[1:]):
        # how far apart neighbouring fibers are at the start and the end: where
        # fibers gather into a tendon, strokes are thinned so they do not pile up
        gs = math.hypot(s1[0] - s0[0], s1[1] - s0[1]) / per_gap
        ge = math.hypot(e1[0] - e0[0], e1[1] - e0[1]) / per_gap
        for k in range(per_gap):
            t = (k + rng.uniform(0.25, 0.75)) / per_gap
            lines.append((lerp(s0, s1, t), lerp(e0, e1, t), gs, ge))
    out = []
    for s, e, gs, ge in lines:
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
            if axis:
                ax_cx, ax_cy, ax_dx, ax_dy, ax_h = axis
                shade = ((mid[0] - ax_cx) * -ax_dx + (mid[1] - ax_cy) * -ax_dy) / (2 * ax_h)
            else:
                shade = ((mid[0] - centre[0]) * -LIGHT[0] + (mid[1] - centre[1]) * -LIGHT[1]) / size
            keep = 0.12 + 1.6 * (shade + 0.15)
            gap = gs + (ge - gs) * ((t0 + t1) / 2)
            crowd = min(1.0, max(0.12, gap / 3.6))
            keep *= crowd
            if rng.random() < keep:
                p = []
                for j in range(3):
                    t = t0 + (t1 - t0) * j / 2
                    q = lerp(s, e, t)
                    b = bow * math.sin(math.pi * t) + (0.6 if j == 1 else 0) * rng.uniform(-1, 1)
                    p.append((q[0] + nx * b, q[1] + ny * b))
                out.append(p)
            if shade > 0.28 and rng.random() < 0.55 * crowd:
                # deepest shadow: a short cross stroke over the fiber stroke
                c = lerp(s, e, (t0 + t1) / 2)
                a = math.atan2(uy, ux) + math.radians(rng.uniform(50, 70))
                l2 = rng.uniform(4, 8)
                out.append([(c[0] - math.cos(a) * l2, c[1] - math.sin(a) * l2), c,
                            (c[0] + math.cos(a) * l2, c[1] + math.sin(a) * l2)])
            pos += seg + rng.uniform(1.5, 5) * (1.6 - min(1.0, max(0.0, shade + 0.5)))
    return out


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


# ---------------------------------------------------------------------------
# PARTS: each group is cut into its muscles and heads along these lines.
# Lines run a little past the edges of the group so each one cuts cleanly;
# a seed point inside each piece says which part it is. Figure's left half.
# ---------------------------------------------------------------------------

PART_NAMES = {
    'chest-upper': 'Upper chest', 'chest-middle': 'Middle chest', 'chest-lower': 'Lower chest',
    'front-delts': 'Front delts', 'side-delts': 'Side delts', 'rear-delts': 'Rear delts',
    'biceps-long': 'Biceps, long head', 'biceps-short': 'Biceps, short head',
    'brachialis': 'Brachialis',
    'triceps-long': 'Triceps, long head', 'triceps-lateral': 'Triceps, lateral head',
    'triceps-medial': 'Triceps, medial head',
    'brachioradialis': 'Brachioradialis', 'wrist-flexors': 'Wrist flexors',
    'wrist-extensors': 'Wrist extensors',
    'traps-upper': 'Upper traps', 'traps-middle': 'Middle traps', 'traps-lower': 'Lower traps',
    'rhomboids': 'Rhomboids', 'infraspinatus': 'Infraspinatus', 'teres-minor': 'Teres minor',
    'teres-major': 'Teres major',
    'lats': 'Lats', 'lower-back': 'Spinal erectors', 'abs': 'Abs',
    'external-oblique': 'External oblique', 'serratus': 'Serratus',
    'glute-max': 'Gluteus maximus', 'glute-med': 'Gluteus medius',
    'rectus-femoris': 'Rectus femoris', 'vastus-lateralis': 'Vastus lateralis',
    'vastus-medialis': 'Vastus medialis', 'sartorius': 'Sartorius',
    'tfl': 'Tensor fasciae latae', 'hip-flexors': 'Hip flexors (iliopsoas)',
    'biceps-femoris': 'Biceps femoris', 'semitendinosus': 'Semitendinosus',
    'semimembranosus': 'Semimembranosus',
    'adductor-longus': 'Adductor longus', 'adductor-magnus': 'Adductor magnus',
    'gracilis': 'Gracilis', 'pectineus': 'Pectineus',
    'gastroc-medial': 'Calf, inner head', 'gastroc-lateral': 'Calf, outer head',
    'soleus': 'Soleus', 'tibialis-anterior': 'Tibialis anterior',
}

# A part normally belongs to the group it is cut from. The hip flexors sit
# inside the adductor shape at the top of the thigh but count with the quads.
PART_GROUP = {'hip-flexors': 'quads'}

SPLITS = {
    'back': {
        'traps': ([[(-1, 140), (40, 144), (80, 149), (100, 154)],
                   [(-1, 200), (30, 193), (50, 183), (60, 180)]],
                  {'traps-upper': [(40, 132)], 'traps-middle': [(40, 165)],
                   'traps-lower': [(15, 240)]}),
        'upper-back': ([[(30, 213), (56, 212), (70, 212), (92, 212)],
                        [(30, 236), (42, 234), (56, 231), (70, 226), (83, 218), (92, 215)],
                        [(26, 237), (34, 250), (42, 258)]],
                       {'infraspinatus': [(60, 200)], 'teres-minor': [(60, 220)],
                        'teres-major': [(60, 238)], 'rhomboids': [(30.5, 245)]}),
        'triceps': ([[ARM(36, -8), ARM(56, -6), ARM(76, -2), ARM(96, 2), ARM(120, 2),
                      ARM(156, 2)],
                     [ARM(100, -42), ARM(110, -20), ARM(124, -12), ARM(156, -10)]],
                    {'triceps-long': [ARM(80, -18)], 'triceps-lateral': [ARM(106, 18)],
                     'triceps-medial': [ARM(132, -20)]}),
        'forearms': ([[FORE(-14, 22), FORE(4, 20), FORE(40, 19), FORE(76, 14), FORE(108, 10),
                       FORE(132, 9)],
                      [FORE(-12, -8), FORE(10, -7), FORE(40, -11), FORE(80, -10),
                       FORE(116, -8), FORE(132, -8)]],
                     {'brachioradialis': [FORE(30, 26)], 'wrist-extensors': [FORE(50, 4)],
                      'wrist-flexors': [FORE(50, -20)]}),
        'obliques': ([], {'external-oblique': [(58.5, 335)]}),
        'glutes': ([], {'glute-med': [(70, 370)], 'glute-max': [(40, 410)]}),
        'hamstrings': ([[(36, 436), (36, 456), (39, 500), (41, 540), (42, 575), (43, 606),
                         (43, 640)],
                        [(24, 495), (30, 540), (34, 570), (37, 595), (40, 612), (42, 640)]],
                       {'biceps-femoris': [(55, 520)], 'semitendinosus': [(35, 500)],
                        'semimembranosus': [(30, 580)]}),
        'adductors': ([[(9, 436), (12, 470), (14, 494), (17, 522), (20, 550), (24, 575),
                        (30, 590)]],
                      {'gracilis': [(12.5, 500)], 'adductor-magnus': [(20, 480)]}),
        'quads': ([], {'vastus-lateralis': [(75, 520)]}),
        'calves': ([[(43, 600), (41, 637), (40, 662), (41, 690), (42, 704), (42, 740), (41, 780)],
                    [(6, 712), (24, 726), (38, 731), (48, 731)],
                    [(76, 692), (57, 708), (45, 716), (36, 716)]],
                   {'gastroc-medial': [(25, 670)], 'gastroc-lateral': [(58, 670)],
                    'soleus': [(32, 748), (50, 740)]}),
    },
    'front': {
        'traps': ([], {'traps-upper': [(60, 142)]}),
        'chest': ([[(-1, 164), (14, 166), (38, 172), (60, 182), (72, 190), (84, 192)],
                   [(-1, 212), (20, 222), (46, 226), (68, 224), (86, 215), (94, 211)]],
                  {'chest-upper': [(40, 160)], 'chest-middle': [(40, 196)],
                   'chest-lower': [(40, 238)]}),
        'biceps': ([[ARM(68, 16), ARM(80, 14), ARM(100, 18), ARM(118, 15), ARM(134, 8),
                     FORE(10, 3), FORE(26, 3)],
                    [ARM(44, -2), ARM(62, -2), ARM(86, 0), ARM(106, 0), ARM(126, 0),
                     FORE(12, 0), FORE(26, 0)],
                    [ARM(118, -32), ARM(126, -16), ARM(134, -10), ARM(146, -4), FORE(26, -2)]],
                   {'biceps-long': [ARM(95, 8)], 'biceps-short': [ARM(95, -10)],
                    'brachialis': [ARM(112, 24), ARM(138, -18)]}),
        'triceps': ([[ARM(100, -40), ARM(102, -24), ARM(104, -12)]],
                    {'triceps-long': [ARM(70, -25)], 'triceps-medial': [ARM(118, -23)]}),
        'forearms': ([[FORE(12, -2), FORE(18, 0), FORE(44, 16), FORE(80, 12), FORE(116, 8),
                       FORE(132, 8)]],
                     {'brachioradialis': [FORE(50, 24)], 'wrist-flexors': [FORE(60, -10)]}),
        'obliques': ([[(56, 247), (56, 262), (58, 280), (64, 296), (76, 302), (84, 300)]],
                     {'serratus': [(72, 262)], 'external-oblique': [(45, 320)]}),
        'quads': ([[(57, 360), (56, 380), (53, 396), (45, 428), (37, 462), (29, 496), (23, 528),
                    (20, 556), (19, 572), (17, 586)],
                   [(62, 356), (62, 372), (64, 394), (70, 420), (78, 446), (86, 452), (95, 452)],
                   [(52, 382), (56, 388), (60, 396), (64, 440), (63, 490), (58, 540), (51, 580),
                    (46, 601), (45, 614)],
                   [(52, 382), (52, 396), (48, 440), (44, 490), (40, 540), (37, 590), (37, 604),
                    (37, 614)]],
                  {'sartorius': [(40, 430)], 'tfl': [(72, 400)], 'rectus-femoris': [(54, 470)],
                   'vastus-lateralis': [(76, 500)], 'vastus-medialis': [(28, 575)]}),
        'adductors': ([[(45, 383), (42, 400), (39, 416), (40, 425)],
                       [(32, 394), (29, 420), (26, 440), (28, 452), (31, 458)],
                       [(15, 410), (12, 440), (12, 470), (14, 494), (19, 500)]],
                      {'hip-flexors': [(44, 400)], 'pectineus': [(35, 410)],
                       'adductor-longus': [(22, 450)], 'gracilis': [(10, 460)]}),
        'shins': ([], {'tibialis-anterior': [(47, 700)]}),
        # The abs stay one part, cut at their three tendinous lines so each
        # block of the six-pack is shaded as its own rounded form.
        'abs': ([[(-1, 268), (14, 266), (34, 270)], [(-1, 295), (14, 294), (34, 298)],
                 [(-1, 321), (14, 320), (32, 323)]],
                {'abs': [(14, 255), (14, 281), (14, 308), (14, 370)]}),
        'calves': ([[(6, 712), (20, 722), (34, 728)], [(76, 694), (62, 704), (52, 712)]],
                   {'gastroc-medial': [(18, 680)], 'gastroc-lateral': [(66, 672)],
                    'soleus': [(22, 738), (60, 714)]}),
    },
}

# Groups that are one part, named after the group.
SINGLE = {'front-delts', 'side-delts', 'rear-delts', 'lats', 'lower-back'}


def cut_parts(view, gid, polys_xy, side):
    """Cut one group (already in drawing coordinates) into its parts.
    Returns [(part, shapely polygon)], and the cut lines clipped to the group."""
    from shapely.geometry import Polygon, LineString, Point
    from shapely.ops import split, unary_union
    shapes = [Polygon(sample(p, closed=True, step=1.5)).buffer(0) for p in polys_xy]
    whole = unary_union(shapes)
    if gid in SINGLE or gid not in SPLITS[view]:
        return [(gid, sh) for sh in shapes], []
    lines, seeds = SPLITS[view][gid]
    pieces = list(shapes)
    cuts = []
    for line in lines:
        L = LineString(sample([to_xy(q, side) for q in line], step=1.5))
        cuts.append(L)
        nxt = []
        for pc in pieces:
            if L.crosses(pc):
                res = split(pc, L)
                nxt.extend(g for g in res.geoms if g.area > 0.5)
            else:
                nxt.append(pc)
        pieces = nxt
    # A cut that clips the corner of a neighbouring muscle leaves a sliver;
    # give each sliver back to the piece it shares the longest edge with.
    seed_pts = [Point(to_xy(q, side)) for pts in seeds.values() for q in pts]
    has_seed = lambda g: any(g.contains(pt) for pt in seed_pts)
    slivers = [g for g in pieces if not has_seed(g) and g.area < 60]
    pieces = [g for g in pieces if g not in slivers]
    for sl in slivers:
        best = max(pieces, key=lambda g: sl.buffer(0.3).intersection(g).area)
        pieces[pieces.index(best)] = unary_union([best, sl]).buffer(0)
    out = []
    for pc in pieces:
        hits = [part for part, pts in seeds.items()
                for q in pts if pc.contains(Point(to_xy(q, side)))]
        if len(hits) != 1:
            raise SystemExit('%s %s %s: piece at %s has seeds %s'
                             % (view, gid, side, tuple(round(c) for c in pc.centroid.coords[0]), hits))
        out.append((hits[0], pc))
    found = {part for part, _ in out}
    missing = set(seeds) - found
    if missing:
        raise SystemExit('%s %s: no piece for %s' % (view, gid, missing))
    inner = []
    for L in cuts:
        g = L.intersection(whole.buffer(-0.3))
        for seg in getattr(g, 'geoms', [g]):
            if seg.length > 2:
                inner.append(list(seg.simplify(0.4).coords))
    return out, inner


def resample(line, closed=False, step=4.0):
    """Thin out a dense outline to points about `step` apart, keeping corners,
    so the hand wobble does not turn it ragged."""
    if len(line) < 24:
        return line
    out = [line[0]]
    acc = 0.0
    n = len(line)
    for i in range(1, n):
        a, b = line[i - 1], line[i]
        acc += math.hypot(b[0] - a[0], b[1] - a[1])
        sharp = False
        if 0 < i < n - 1:
            c = line[i + 1]
            v1 = (b[0] - a[0], b[1] - a[1]); v2 = (c[0] - b[0], c[1] - b[1])
            l1, l2 = math.hypot(*v1), math.hypot(*v2)
            if l1 and l2 and (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2) < 0.5:
                sharp = True
        if acc >= step or sharp:
            out.append(b)
            acc = 0.0
    if not closed and out[-1] != line[-1]:
        out.append(line[-1])
    return out


def poly_d_holes(pc):
    """A shape with holes, as one path drawn with the even-odd rule."""
    out = []
    for g in getattr(pc, 'geoms', [pc]):
        for ring in [g.exterior] + list(g.interiors):
            pts = list(ring.coords)[:-1]
            out.append('M' + ' '.join('%.1f %.1f' % q for q in pts) + 'Z')
    return ''.join(out) + '" clip-rule="evenodd'


def poly_d(pc):
    out = []
    for g in getattr(pc, 'geoms', [pc]):
        if g.area < 1:
            continue
        g = g.simplify(0.05)
        if not g.is_valid:
            g = g.buffer(0.02).buffer(-0.02)
        ext = list(g.exterior.coords)[:-1]
        out.append('M' + ' '.join('%.1f %.1f' % q for q in ext) + 'Z')
    return ''.join(out)


def edge_runs(poly, closed, soft, rng, body=None):
    """Split an outline into runs by how it faces the light, the way a
    graphite artist lets an edge go dark where the form turns away from the
    light and fade, or vanish, where the light hits it. Returns
    [(weight, points)] with weight 'dark', 'mid' or 'light'."""
    from shapely.geometry import Point
    n = len(poly)
    if n < 2:
        return []
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1]
               for i in range(n)) if closed else 0
    sign = 1 if area > 0 else -1
    runs, run, cur = [], [], None
    segs = range(n if closed else n - 1)
    for i in segs:
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        ox, oy = sign * dy / L, -sign * dx / L
        f = ox * -LIGHT[0] + oy * -LIGHT[1] if closed else 0.0
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        outer = False
        if body is not None and closed:
            outer = not body.contains(Point(mid[0] + ox * 2.5, mid[1] + oy * 2.5))
        if soft is not None and soft.distance(Point(mid)) < 1.8:
            w = None                                  # a join the eye should not stop at
        elif outer:
            # the body's own outline: firm in shadow, lighter in the light
            w = 'dark' if f > -0.05 else 'mid'
        elif f > 0.45:
            w = 'mid'                                 # inside the body, edges are quieter
        elif f > -0.2:
            w = 'light'
        else:
            w = None if rng.random() < 0.4 else 'light'    # lost edges in the light
        if w != cur:
            if cur and len(run) > 1:
                runs.append((cur, run))
            run = [a] if w else []
            cur = w
        if w:
            run.append(b)
    if cur and len(run) > 1:
        runs.append((cur, run))
    return runs


def build2(view, regions, details, extras, fibers, seed):
    """Draw one view in graphite. Layers, bottom to top: the tap shapes (one
    per part), the soft tone on muscle and skin, graphite hatching, the gloss
    for lit muscles, construction lines, details, then the edges, weighted by
    the light."""
    from shapely.geometry import box, Polygon, LineString
    from shapely.ops import unary_union
    rng = random.Random(seed)
    taken = {'L': box(0, 0, 0, 0), 'R': box(0, 0, 0, 0)}
    half = {'L': box(-10, -10, CX, H + 10), 'R': box(CX, -10, W + 10, H + 10)}
    soft = {side: unary_union([LineString(sample([to_xy(q, side) for q in ln], step=1.5))
                               for ln in extras.get('soft', [])]) if extras.get('soft') else None
            for side in ('L', 'R')}
    fills, gloss, defs, hatching = [], [], [], []
    tones, skin_tones = {}, []
    edges = {'dark': [], 'mid': [], 'light': [], 'search': []}
    creases, crease_lines = [], []
    detail_ink, construct = [], []

    def tone_gradient(tid, pc, strength=1.0):
        cx, cy, dirx, diry, h = shade_axis(pc)
        stops = ((.2, 0), (.6, .17), (.88, .38), (1, .5))
        defs.append('<linearGradient id="%s" gradientUnits="userSpaceOnUse" '
                    'x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f">%s</linearGradient>'
                    % (tid, cx + dirx * h, cy + diry * h, cx - dirx * h, cy - diry * h,
                       ''.join('<stop offset="%g" stop-color="var(--map-shade,#1C1C1F)" '
                               'stop-opacity="%.2f"/>' % (o, a * strength) for o, a in stops)))

    pending = []

    def ink_outline(points, closed, side):
        pending.append((points, closed, side))

    def ink_now(points, closed, side, body):
        for w, run in edge_runs(dense(points, 3) if closed else points, closed, soft[side], rng,
                                body):
            edges[w].append(polyline(run))
            # a second, searching pass of the pencil beside the firm line
            if w in ('dark', 'mid') and rng.random() < 0.45 and len(run) > 3:
                off = rng.uniform(-1.1, 1.1)
                k0 = rng.randrange(0, max(1, len(run) // 3))
                k1 = min(len(run), k0 + rng.randrange(3, max(4, len(run))))
                seg = run[k0:k1]
                if len(seg) > 1:
                    edges['search'].append(polyline([(x + off, y + off * 0.6) for x, y in seg]))

    for gid, polys in regions:
        group_d = []
        for side in ('L', 'R'):
            polys_xy = [dedupe([to_xy(q, side) for q in poly]) for poly in polys]
            for p in polys_xy:
                group_d.append(smooth(p, closed=True))
                ink_outline(sample(wobble(p, rng, 0.45), closed=True, step=2.5), True, side)
                if gid in fibers:
                    c, size = centroid(p)
                    axis = shade_axis(Polygon(p).buffer(0))
                    pairs = [(to_xy(a, side), to_xy(b, side)) for a, b in fibers[gid]]
                    for ln in hatch(pairs, rng, c, size, per_gap=6, axis=axis):
                        hatching.append((gid, polyline(ln)))
            parts, inner = cut_parts(view, gid, polys_xy, side)
            # Where two parts of one muscle group meet there is no drawn line,
            # just the soft shadow of the crease between two rounded forms and
            # a faint touch of the pencil.
            for ln in inner:
                pts = ln[::max(1, len(ln) // 14)] + [ln[-1]]
                creases.append(smooth(wobble(pts, rng, 0.3)))
                if rng.random() < 0.85:
                    crease_lines.append(smooth(wobble(pts, rng, 0.45)))
            for k, (part, pc) in enumerate(parts):
                # Shapes never overlap: each half stops at the midline, and a
                # piece gives up anything a neighbour drawn earlier already has.
                pc = pc.intersection(half[side]).difference(taken[side]).buffer(0)
                taken[side] = unary_union([taken[side], pc])
                d = poly_d(pc)
                grp = PART_GROUP.get(part, gid)
                fills.append('<path class="mm-muscle" data-group="%s" data-part="%s" d="%s"/>'
                             % (grp, part, d))
                gloss.append('<path data-part="%s" d="%s"/>' % (part, d))
                tid = 'mm-%s-%s-%s%d' % (view, part, side, k)
                tone_gradient(tid, pc)
                tones.setdefault(gid, []).append(('<path fill="url(#%s)" d="%s"/>' % (tid, d),
                                                  '<path stroke="url(#%s)" d="%s"/>' % (tid, d)))
        rid = 'mm-%s-%s' % (view, gid)
        defs.append('<clipPath id="%s-c"><path d="%s"/></clipPath>' % (rid, ''.join(group_d)))

    # Skin that is not a muscle group (head, neck, knees, shins, hands, feet)
    # gets the same tone, so nothing reads as a flat diagram.
    skin_d = []
    for k, poly in enumerate(extras.get('skin', [])):
        both = []
        for side in ('L', 'R'):
            sh = Polygon(sample([to_xy(q, side) for q in poly], closed=True, step=1.5)).buffer(0)
            both.append(sh.intersection(half[side]).difference(taken[side]).buffer(0))
        # a shape that crosses the midline (head, neck) is shaded as one form
        merged = unary_union([b.buffer(0.3) for b in both]).buffer(-0.3)
        for j, sh in enumerate(getattr(merged, 'geoms', [merged])):
            if sh.area < 4:
                continue
            d = poly_d(sh)
            if not d:
                continue
            skin_d.append(d)
            tid = 'mm-%s-skin%d-%d' % (view, k, j)
            tone_gradient(tid, sh, 0.8)
            skin_tones.append(('<path fill="url(#%s)" d="%s"/>' % (tid, d),
                               '<path stroke="url(#%s)" d="%s"/>' % (tid, d)))
    defs.append('<clipPath id="mm-%s-skin-c"><path d="%s"/></clipPath>' % (view, ''.join(skin_d)))
    # Now the whole body is known: edges on its outside never vanish.
    body = {side: unary_union([taken[side]] + [
        Polygon(sample([to_xy(q, side) for q in poly], closed=True, step=2)).buffer(0)
        for poly in extras.get('skin', [])]).buffer(0.8) for side in ('L', 'R')}
    whole = unary_union([body['L'], body['R']])

    by_group = {}
    for gid, d in hatching:
        by_group.setdefault(gid, []).append(d)
    hatch_svg = ''.join('<path clip-path="url(#mm-%s-%s-c)" d="%s"/>' % (view, g, ''.join(ds))
                        for g, ds in by_group.items())
    # The wash fills each shape; the edge shading is the same gradient drawn
    # as a wide stroke and softened, like graphite smudged along the form.
    # Edge shading stays away from the soft joins (wrists, ankles).
    from shapely.geometry import box as _box
    nosoft = _box(-20, -20, W + 20, H + 20)
    for side in ('L', 'R'):
        if soft[side] is not None:
            nosoft = nosoft.difference(soft[side].buffer(7))
    defs.append('<clipPath id="mm-%s-nosoft"><path d="%s"/></clipPath>' % (view, poly_d(nosoft) if
                nosoft.geom_type == 'Polygon' and not nosoft.interiors else poly_d_holes(nosoft)))
    tone_svg = ''.join('<g clip-path="url(#mm-%s-%s-c)">%s<g clip-path="url(#mm-%s-nosoft)">'
                       '<g class="mm-edge">%s</g></g></g>'
                       % (view, g, ''.join(f for f, _ in ts), view, ''.join(e for _, e in ts))
                       for g, ts in tones.items())
    tone_svg += ('<g clip-path="url(#mm-%s-skin-c)">%s<g clip-path="url(#mm-%s-nosoft)">'
                 '<g class="mm-edge">%s</g></g></g>'
                 % (view, ''.join(f for f, _ in skin_tones), view, ''.join(e for _, e in skin_tones)))
    tone_svg += '<g class="mm-crease"><path d="%s"/></g>' % ''.join(creases)

    for line in details:
        for side in ('L', 'R'):
            detail_ink.append(smooth(wobble([to_xy(q, side) for q in line], rng, 0.4)))
    for line, closed, mirror in extras.get('out', []):
        line = resample(line, closed)
        for side in (('L', 'R') if mirror else ('L',)):
            w = wobble([to_xy(q, side) for q in line], rng, 0.45)
            ink_outline(sample(w, closed=closed, step=2.5), closed, side)
    for points, closed, side in pending:
        ink_now(points, closed, side, whole)
    for key, bucket, amount in (('detail', detail_ink, 0.35), ('construct', construct, 0.3)):
        for line, closed, mirror in extras.get(key, []):
            line = resample(line, closed)
            for side in (('L', 'R') if mirror else ('L',)):
                bucket.append(smooth(wobble([to_xy(q, side) for q in line], rng, amount), closed))

    css = ('.mm-muscle{fill:var(--mm-fill,transparent)}'
           '.mm-ink{fill:none;stroke:var(--map-ink,#2A2A2E);stroke-linecap:round;stroke-linejoin:round}'
           '.mm-ink,.mm-tone,.mm-gloss{pointer-events:none}'
           '.mm-tone{opacity:var(--map-tone,1)}'
           '.mm-edge{filter:url(#mm-%s-soft)}.mm-edge path{fill:none;stroke-width:9}'
           '.mm-crease{filter:url(#mm-%s-soft2)}'
           '.mm-crease path{fill:none;stroke:var(--map-shade,#1C1C1F);stroke-width:3.4;opacity:.4}'
           '.mm-gloss path{fill:url(#mm-%s-gl);opacity:0}'
           '.mm-dark{stroke-width:1.55;opacity:.9}.mm-mid{stroke-width:1.05;opacity:.6}'
           '.mm-light{stroke-width:.75;opacity:.3}.mm-search{stroke-width:.6;opacity:.22}'
           '.mm-cline{stroke-width:.7;opacity:.3}'
           '.mm-detail{stroke-width:.8;opacity:.55}'
           '.mm-construct{stroke-width:.65;opacity:.4}'
           '.mm-hatch{stroke-width:.6;opacity:.62}') % (view, view, view)
    gl = ('<radialGradient id="mm-%s-gl" cx=".34" cy=".3" r=".62">'
          '<stop offset="0" stop-color="#fff" stop-opacity=".75"/>'
          '<stop offset=".18" stop-color="#fff" stop-opacity=".42"/>'
          '<stop offset=".5" stop-color="#fff" stop-opacity=".1"/>'
          '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
          '<filter id="mm-%s-soft" x="-5%%" y="-5%%" width="110%%" height="110%%">'
          '<feGaussianBlur stdDeviation="2.4"/></filter>'
          '<filter id="mm-%s-soft2" x="-5%%" y="-5%%" width="110%%" height="110%%">'
          '<feGaussianBlur stdDeviation="1.3"/></filter>') % (view, view, view)
    return ''.join([
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" class="mm mm-%s">' % (W, H, view),
        '<style>%s</style>' % css,
        '<defs>%s%s</defs>' % (gl, ''.join(defs)),
        '<g class="mm-regions">%s</g>' % ''.join(fills),
        '<g class="mm-tone">%s</g>' % tone_svg,
        '<g class="mm-ink mm-hatch">%s</g>' % hatch_svg,
        '<g class="mm-gloss">%s</g>' % ''.join(gloss),
        '<g class="mm-ink mm-construct"><path d="%s"/></g>' % ''.join(construct),
        '<g class="mm-ink mm-detail"><path d="%s"/></g>' % ''.join(detail_ink),
        '<g class="mm-ink mm-cline"><path d="%s"/></g>' % ''.join(crease_lines),
        '<g class="mm-ink mm-search"><path d="%s"/></g>' % ''.join(edges['search']),
        '<g class="mm-ink mm-light"><path d="%s"/></g>' % ''.join(edges['light']),
        '<g class="mm-ink mm-mid"><path d="%s"/></g>' % ''.join(edges['mid']),
        '<g class="mm-ink mm-dark"><path d="%s"/></g>' % ''.join(edges['dark']),
        '</svg>',
    ])


# ---------------------------------------------------------------------------
# Head, hands and feet
# ---------------------------------------------------------------------------
# The head is the classic construction sketch a drawing starts from: the
# ball of the cranium, the center line, the brow line, the curve of the eye
# line, marks for the nose, mouth and chin, the jaw and the ears. Thirds:
# brow at the middle of the ball, nose at its bottom, chin the same distance
# again below.

HEAD_C, HEAD_R = (0, 50), 33
BROW, NOSE, CHIN = 50, 83, 116


def circle_pts(c, r, a0=0, a1=360, step=6):
    return [(c[0] + r * math.cos(math.radians(a)), c[1] - r * math.sin(math.radians(a)))
            for a in range(a0, a1 + 1, step)]


def capsule_chain(pts, radii):
    """A tapering finger or toe: one rounded segment per bone, each a little
    narrower than the last, with a slight swell at the joints."""
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    segs = []
    for (a, b), r in zip(zip(pts, pts[1:]), radii):
        segs.append(LineString([a, b]).buffer(r, quad_segs=8))
    for q, r in zip(pts[1:-1], radii[1:]):
        from shapely.geometry import Point
        segs.append(Point(q).buffer(r + 0.35, quad_segs=8))
    return unary_union(segs)


# Fingers in the hand's frame (u down the hand, v toward the thumb): the
# knuckle, the angle each finger fans to, the length of each bone and the
# half-width of each bone. A relaxed hand fans slightly.
FINGERS = [((39, 9.0), 3, (14, 9.5, 7), (3.15, 2.85, 2.5)),       # index
           ((40.5, 2.3), 0.5, (15.5, 10.5, 7.5), (3.35, 3.0, 2.6)), # middle
           ((39.5, -4.4), -2.5, (14.5, 9.5, 7), (3.15, 2.8, 2.45)), # ring
           ((37, -10.4), -6.5, (11.5, 7.5, 6), (2.7, 2.4, 2.1))]    # little
THUMB = ([(5, 10), (20, 15.2), (32, 18.6), (42, 20.2)], (5.6, 3.7, 3.2))


def finger_pts(base, ang, lengths):
    pts = [base]
    a = math.radians(ang)
    for L in lengths:
        u, v = pts[-1]
        pts.append((u + L * math.cos(a), v + L * math.sin(a)))
    return pts


def hand_shape():
    """The hand as one outline: palm, four tapering fingers and the thumb,
    in the hand's own frame, then placed at the end of the forearm."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    palm = Polygon([(-3, -13.6), (-3, 13.6), (8, 15.6), (16, 16), (24, 15), (38, 12.5),
                    (40.5, 6), (41, 0), (40, -6), (38, -12.5), (26, -15.6), (12, -15.2)])
    shapes = [palm]
    bones = []
    for base, ang, lengths, radii in FINGERS:
        pts = finger_pts(base, ang, lengths)
        bones.append((pts, radii))
        shapes.append(capsule_chain(pts, radii))
    shapes.append(capsule_chain(*THUMB))
    shape = unary_union(shapes).buffer(0.25).buffer(-0.25)
    outline = [HAND(u, v) for u, v in list(shape.simplify(0.2).exterior.coords)]
    return outline, bones


def hand_extras(view):
    outline, bones = hand_shape()
    out = [(outline, True, True)]
    detail = []
    for pts, radii in bones:
        # the bend at each finger joint: two short creases (palm) or a soft
        # wrinkle over the knuckle (back)
        for q, r in zip(pts[1:-1], radii[1:]):
            a = math.atan2(pts[-1][1] - pts[0][1], pts[-1][0] - pts[0][0])
            nu, nv = -math.sin(a), math.cos(a)
            c1 = (q[0] - nu * r * 0.75, q[1] - nv * r * 0.75)
            c2 = (q[0] + nu * r * 0.75, q[1] + nv * r * 0.75)
            if view == 'front':
                detail.append(([HAND(*c1), HAND(*c2)], False, True))
            else:
                mid = (q[0] - 0.9 * math.cos(a), q[1] - 0.9 * math.sin(a))
                detail.append(([HAND(*c1), HAND(*mid), HAND(*c2)], False, True))
    if view == 'front':
        # palm: the life line round the thumb's pad, the head line, the heart
        # line, the wrist creases and the edge of the pad below the little finger
        detail += [([HAND(5, 7), HAND(14, 4.5), HAND(23, 5.5), HAND(31, 9.5), HAND(35, 12.5)], False, True),
                   ([HAND(22, 14.5), HAND(26, 6), HAND(29, -3), HAND(31, -9)], False, True),
                   ([HAND(33, -14.5), HAND(32.5, -7), HAND(34, 0), HAND(37, 6)], False, True),
                   ([HAND(1.5, -11), HAND(1, 0), HAND(1.5, 11)], False, True),
                   ([HAND(10, -13), HAND(20, -11.5), HAND(29, -12.5)], False, True)]
    else:
        # back of the hand: the knuckles, the tendons fanning to the fingers,
        # and the nails
        for pts, radii in bones:
            k = pts[0]
            detail.append(([HAND(k[0] - 1.8, k[1] - radii[0] * 0.7), HAND(k[0] + 0.6, k[1]),
                            HAND(k[0] - 1.8, k[1] + radii[0] * 0.7)], False, True))
            detail.append(([HAND(4, k[1] * 0.3), HAND(k[0] - 6, k[1] * 0.92)], False, True))
            t, prev = pts[-1], pts[-2]
            a = math.atan2(t[1] - prev[1], t[0] - prev[0])
            nu, nv = -math.sin(a), math.cos(a)
            r = radii[-1] * 0.62
            back = (t[0] - 4.2 * math.cos(a), t[1] - 4.2 * math.sin(a))
            detail.append(([HAND(back[0] + nu * r, back[1] + nv * r),
                            HAND(t[0] - 0.9 * math.cos(a) + nu * r, t[1] - 0.9 * math.sin(a) + nv * r),
                            HAND(t[0] - 0.9 * math.cos(a) - nu * r, t[1] - 0.9 * math.sin(a) - nv * r),
                            HAND(back[0] - nu * r, back[1] - nv * r)], False, True))
    return out, detail, outline


TOES = [([(27, 810), (26.7, 819), (26.4, 826)], (5.0, 4.5)),
        ([(34.5, 812), (34.8, 820), (35, 826.5)], (3.2, 2.8)),
        ([(41, 813), (41.3, 820), (41.6, 825.5)], (3.0, 2.6)),
        ([(47.2, 813), (47.6, 819), (48, 823.5)], (2.8, 2.4)),
        ([(53, 812), (53.8, 817), (54.6, 821)], (2.6, 2.2))]


def foot_front():
    """The foot from the front: ankle, the instep widening to the ball of the
    foot, and five tapering toes."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    instep = Polygon([(28, 770), (51, 762), (51.5, 776), (53, 788), (55.5, 798), (58, 806),
                      (60, 812), (56.5, 816), (24, 816), (22.6, 812), (23.2, 806), (24.6, 799),
                      (26, 792), (27.6, 782)])
    shape = unary_union([instep] + [capsule_chain(p, r) for p, r in TOES])
    shape = shape.buffer(0.3).buffer(-0.3)
    ext = list(shape.simplify(0.25).exterior.coords)
    return ext


def extras_front():
    out, detail, construct, skin = [], [], [], []
    # Head: the ball of the cranium, the jaw down to the chin and the ears,
    # with the construction lines a figure drawing starts from.
    out.append((circle_pts(HEAD_C, HEAD_R, -50, 230), False, False))
    jaw = [(31, 62), (29.5, 80), (24, 97), (15, 110), (6, 115), (0, 116)]
    out.append((jaw, False, True))
    out.append(([(32, 53), (37, 54), (39.5, 63), (38, 75), (34, 82)], False, True))
    construct += [([(0, 10), (0, 128)], False, False),                       # center line
                  ([(-37, BROW), (37, BROW)], False, False),                 # brow line
                  ([(-31, 64), (-16, 68.5), (0, 69.5), (16, 68.5), (31, 64)], False, False),  # eye line
                  ([(-6, NOSE), (6, NOSE)], False, False),                   # base of the nose
                  ([(-5, 95), (5, 95)], False, False),                       # mouth
                  ([(-8, CHIN - 1), (8, CHIN - 1)], False, False),           # chin
                  ([(-26, 29), (-14, 24.5), (0, 23.5), (14, 24.5), (26, 29)], False, False),  # hairline
                  (circle_pts((0.6, 49.4), 33.6, -40, 220, 8), False, False),  # second pass
                  ([(23, 23), (26.5, 37), (27.5, 51), (25.5, 66), (21, 78)], False, True),  # side plane
                  ([(3.5, 52), (6, 81)], False, True),                       # sides of the nose
                  ([(8, 108), (8.5, 116)], False, True),                     # the chin's box
                  ([(30, 82), (19, 103), (9, 114)], False, True),            # jaw guide
                  ([(9, 68), (22, 68)], False, True)]                        # eye marks
    out.append(([(26, 100), (29, 108), (31, 116)], False, True))
    detail += [([(30, 94), (24, 112), (14, 132), (5, 149)], False, True),    # neck: SCM
               ([(27, 104), (22, 122), (16, 140), (15, 150)], False, True),
               ([(-2.5, 124), (0, 128), (2.5, 124)], False, False),          # Adam's apple
               ([(-2, 318), (0, 324), (2, 318)], False, False),              # navel
               ([(-4, 146), (0, 150), (4, 146)], False, False)]              # notch of the sternum
    skin.append([(0, 17)] + circle_pts(HEAD_C, HEAD_R, 90, -20, -6)[1:] +
                [(29.5, 80), (24, 97), (15, 110), (6, 115), (0, 116)])
    skin.append([(0, 104), (24, 100), (29, 108), (31, 116), (33, 122), (38, 126), (50, 134), (58, 147),
                 (34, 150), (6, 150), (0, 150)])
    skin.append([(0, 420), (6, 419), (12, 416), (5, 440), (0, 442)])
    # Knees and the bare parts of the lower leg.
    out += [([(66, 603), (63, 612), (61, 626), (63, 638)], False, True),
            ([(24, 614), (26, 624), (23, 638)], False, True),
            ([(56, 728), (53, 742), (51, 754), (51, 762)], False, True),
            ([(22, 740), (26, 756), (28, 772)], False, True)]
    detail += [
        # The kneecap, a rounded triangle, left open on its lit upper side
        ([(46.5, 609), (50, 615), (49.5, 622), (46, 629), (40, 633), (34, 629), (30.5, 622),
          (30, 615)], False, True),
        # its tendon down to the bump of the tibia
        ([(36, 633), (37.6, 648)], False, True),
        ([(44, 633), (42.4, 648)], False, True),
        ([(37, 650.5), (40, 652.5), (43, 650.5)], False, True),
        # the fat pads either side of the tendon
        ([(32, 632), (30.6, 638), (32.6, 643)], False, True),
        ([(48, 632), (49.4, 638), (47.4, 643)], False, True),
        # the iliotibial band to its bump on the tibia, and the head of the fibula
        ([(63, 606), (59, 622), (55.5, 638)], False, True),
        ([(60, 641), (62, 645.5), (60.5, 650)], False, True),
        # fibular muscles beside the shin
        ([(60, 652), (61, 690), (56, 730), (50, 770)], False, True)]
    skin.append([(66, 603), (63, 612), (61, 626), (63, 638), (67, 654), (70, 670), (69, 688),
                 (64, 706), (58, 724), (56, 728), (53, 742), (51, 754), (51, 762), (51.5, 776),
                 (53, 788), (55.5, 798), (58, 806), (60, 812), (56, 818), (40, 820), (24, 818),
                 (22.6, 812), (23.2, 806), (24.6, 799), (26, 792), (27.6, 782), (28, 772),
                 (26, 756), (22, 740), (17, 724), (13, 708), (11, 690), (12, 672), (16, 654),
                 (22, 638), (26, 624), (24, 614), (27, 614), (33, 608), (40, 606), (47, 603),
                 (56, 601)])
    # Hands.
    o, d, hand = hand_extras('front')
    out += o
    detail += d
    skin.append(hand)
    # Feet.
    foot = foot_front()
    out.append((foot, True, True))
    skin.append(foot)       # the toes; the rest of the foot shades with the leg
    for p, r in TOES:
        t = p[-1]
        detail.append(([(t[0] - r[1] * 0.6, t[1] - 2.6), (t[0], t[1] - 3.6), (t[0] + r[1] * 0.6, t[1] - 2.6)],
                       False, True))                                          # toenails
    detail += [([(36, 772), (32, 786), (29, 798)], False, True),             # tibialis anterior tendon
               ([(41, 782), (35, 798), (29, 809)], False, True),             # big toe extensor
               ([(45, 786), (42, 800), (40, 811)], False, True),             # long toe extensor
               ([(27, 786), (24.5, 791), (26, 797)], False, True),           # inner ankle bone
               ([(52, 788), (55, 795), (53, 801)], False, True),             # outer ankle bone
               ([(24, 806), (32, 808.5), (42, 809.5), (55, 808)], False, True)]  # the ball of the foot
    for x in (30.9, 37.9, 44.3, 50.3):                                        # between the toes
        detail.append(([(x, 815.5), (x + 0.4, 822.5)], False, True))
    soft = [[FORE(119, 18), FORE(122, 0), FORE(119, -17)],
            [(27, 772.5), (40, 767), (52, 762)]]
    return {'out': out, 'detail': detail, 'construct': construct, 'skin': skin, 'soft': soft}


def extras_back():
    out, detail, construct, skin = [], [], [], []
    # From behind: the ball of the skull, its lower curve over the nape kept
    # light, and the neck coming down from behind the ears into the traps.
    out.append((circle_pts(HEAD_C, HEAD_R, -28, 208), False, False))
    construct.append((circle_pts(HEAD_C, HEAD_R, 208, 332), False, False))
    out.append(([(26.5, 82), (28.2, 90), (29.6, 99), (30.2, 108)], False, True))
    out.append(([(32, 53), (37, 54), (39.5, 63), (38, 75), (34, 82)], False, True))
    construct += [([(0, 10), (0, 100)], False, False),
                  ([(-37, BROW), (37, BROW)], False, False),
                  ([(-31, 64), (-16, 61), (0, 60), (16, 61), (31, 64)], False, False),
                  (circle_pts((-0.6, 49.4), 33.6, -40, 220, 8), False, False),
                  ([(23, 23), (26.5, 37), (27.5, 51), (25.5, 66), (21, 78)], False, True),
                  ([(-22, 86), (-10, 90), (0, 91), (10, 90), (22, 86)], False, False),   # base of the skull
                  ([(16, 92), (20, 98)], False, True)]
    skin.append([(0, 17)] + circle_pts(HEAD_C, HEAD_R, 90, -36, -6)[1:] +
                [(26.5, 82), (28.2, 90), (29.6, 99), (30.2, 108), (31, 113), (32, 120), (28, 110),
                 (21, 102), (11, 99.5), (0, 99)])
    for y in range(140, 360, 13):
        detail.append(([(0, y), (1.2, y + 3), (0, y + 6)], False, False))
    o, d, hand = hand_extras('back')
    out += o
    detail += d
    skin.append(hand)
    # The back of the knee: the skin crease across it.
    detail += [([(28, 622), (36, 624.5), (44, 625), (54, 623)], False, True)]
    # Heel and the back of the ankle.
    heel = [(51, 762), (50, 775), (49, 786), (51, 795), (52, 806), (48, 818), (40, 824),
            (32, 820), (28, 806), (30, 792), (29, 782), (28, 772)]
    out.append((heel, False, True))
    skin.append(heel + [(35, 760), (41, 756), (47, 758)])
    detail += [([(49, 784), (53, 790), (51, 797)], False, True),
               ([(30, 786), (27, 792), (29, 798)], False, True),
               ([(34, 812), (40, 815.5), (46, 812)], False, True),
               ([(37.5, 772), (37, 790), (38, 806)], False, True),           # Achilles tendon
               ([(43.5, 772), (43, 790), (42, 806)], False, True),
               ([(52, 806), (56, 812), (58, 819), (55, 824)], False, True),  # the forefoot either side
               ([(28, 806), (24, 813), (24, 821), (28, 824)], False, True)]
    soft = [[FORE(119, 18), FORE(122, 0), FORE(119, -17)],
            [(51, 762), (46, 757), (41, 754), (35, 758), (28, 771)]]
    return {'out': out, 'detail': detail, 'construct': construct, 'skin': skin, 'soft': soft}


def svg_back():
    return build2('back', back_regions(), back_details(), extras_back(), back_fibers(), 409)


def svg_front():
    return build2('front', front_regions(), front_details(), extras_front(), front_fibers(), 434)


if __name__ == '__main__':
    for name, fn in (('muscle-back.svg', svg_back), ('muscle-front.svg', svg_front)):
        out = ROOT / 'art' / name
        s = fn()
        out.write_text(s)
        print('wrote', out.relative_to(ROOT), len(s), 'bytes')
