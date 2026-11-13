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
        [(42, 212), (56, 212), (70, 212), (84, 212)],
        [(42, 234), (56, 231), (70, 226), (83, 218)],
        [(29, 244), (34, 250), (39, 253)],
        # Rear delt and side delt: the middle bundles.
        [(70, 168), ARM(30, 0), ARM(62, 8)],
        [ARM(0, 28), ARM(36, 32), ARM(70, 20)],
        # Triceps: long head and lateral head meeting the common tendon.
        [ARM(56, -6), ARM(76, -2), ARM(96, 2)],
        [ARM(84, 26), ARM(100, 17), ARM(113, 9), ARM(126, 5)],
        [ARM(94, -26), ARM(107, -15), ARM(118, -7), ARM(128, -2)],
        # Forearm: olecranon, the back edge of the ulna (flexor carpi
        # ulnaris on one side, extensor carpi ulnaris on the other),
        # brachioradialis and the radial wrist extensors, extensor digitorum,
        # and the two thumb muscles that cross the lower third.
        [FORE(-4, -10), FORE(6, -11), FORE(10, -4)],
        [FORE(10, -7), FORE(40, -11), FORE(80, -10), FORE(118, -8)],
        [FORE(4, 19), FORE(40, 18), FORE(76, 13), FORE(110, 9)],
        [FORE(6, 7), FORE(40, 5), FORE(80, 2), FORE(116, 0)],
        [FORE(64, 5), FORE(86, 11), FORE(106, 14)],
        [FORE(70, -2), FORE(92, 5), FORE(112, 10)],
        # Lower back: the long column of the spinal erectors beside the spine.
        [(9, 296), (13, 314), (18, 334), (20, 350), (17, 362)],
        # Iliotibial band down the outside of the thigh.
        [(76, 432), (82, 470), (79, 515), (71, 565), (63, 612)],
        # Hamstrings: biceps femoris against semitendinosus, the long and
        # short heads of biceps femoris, and semimembranosus on the inner side.
        [(36, 456), (39, 500), (41, 540), (42, 575), (43, 606)],
        [(27, 540), (30, 566), (32, 590), (34, 610)],
        [(52, 520), (55, 560), (55, 592)],
        # Calves: the split between the two heads of gastrocnemius, the
        # lower edges of both heads, and the Achilles tendon.
        [(55, 628), (48, 632), (41, 637)], [(28, 627), (34, 632), (41, 637)],
        [(41, 637), (40, 662), (41, 690), (42, 704)],
        [(12, 712), (24, 726), (38, 731)],
        [(66, 694), (57, 708), (45, 716)],
        [(38, 731), (39, 755)],
        [(45, 718), (44, 754)],
    ]


def back_outline():
    """Lines that are not muscle groups: head, ears, hands, ankles and heels."""
    head = [(34 * math.cos(math.radians(a)), 62 - 46 * math.sin(math.radians(a)))
            for a in range(-40, 221, 6)]
    head = [p for p in head if not (p[1] > 94 and abs(p[0]) < 32)]
    return {
        'head': head,
        'neck': [[(31, 92), (30.5, 102), (30, 108)]],
        # the spinous processes, C7 down to L5, as small marks on the midline
        'spine': [[(0, y), (1.2, y + 3), (0, y + 6)] for y in range(140, 360, 13)],
        'ear': [(32, 56), (38, 58), (40, 68), (38, 81), (33, 87)],
        'hand': [HAND(0, 13), HAND(10, 17), HAND(24, 23), HAND(37, 24), HAND(39, 18),
                 HAND(31, 13), HAND(42, 14), HAND(58, 13), HAND(70, 10), HAND(73, 5),
                 HAND(75, 0), HAND(72, -5), HAND(69, -8), HAND(64, -12), HAND(56, -14),
                 HAND(40, -15), HAND(18, -15), HAND(0, -13)],
        'fingers': [[HAND(46, 6), HAND(68, 6)], [HAND(46, -1), HAND(71, -2)],
                    [HAND(44, -8), HAND(66, -9)]],
        'feet': [[(51, 762), (50, 775), (49, 786), (51, 795), (52, 806), (48, 818), (40, 824),
                  (32, 820), (28, 806), (30, 792), (29, 782), (28, 772)],
                 [(49, 784), (53, 790), (51, 797)], [(30, 786), (27, 792), (29, 798)],
                 [(34, 812), (40, 815), (46, 812)]],
    }


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
    ]


def front_details():
    return [
        # Neck: sternocleidomastoid, its sternal and collarbone heads.
        [(30, 94), (24, 112), (14, 132), (5, 149)],
        [(27, 104), (22, 122), (16, 140), (15, 150)],
        # Pec: the line between the collarbone head and the sternal head.
        [(14, 166), (38, 172), (62, 182), (84, 197)],
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
        [(0, 268), (14, 266), (30.5, 270)],
        [(0, 295), (14, 294), (31, 298)],
        [(0, 321), (14, 320), (28.5, 323)],
        # Biceps: its outer edge against brachialis, and the two heads.
        [ARM(80, 13), ARM(100, 18), ARM(118, 15), ARM(134, 8), FORE(10, 3)],
        [ARM(62, -2), ARM(86, 0), ARM(106, 0)],
        # Forearm: brachioradialis, flexor carpi radialis, the long finger
        # flexors and flexor carpi ulnaris, and pronator teres crossing.
        [FORE(18, 0), FORE(44, 16), FORE(80, 12), FORE(116, 8)],
        [FORE(20, -2), FORE(60, 2), FORE(116, 2)],
        [FORE(12, -8), FORE(60, -7), FORE(116, -4)],
        [FORE(4, -20), FORE(60, -17), FORE(116, -10)],
        [FORE(0, -16), FORE(26, -2), FORE(48, 10)],
        # Quads: rectus femoris down the middle, vastus lateralis outside,
        # the vastus medialis teardrop, tensor fasciae latae at the hip, and
        # the sartorius' outer edge.
        [(60, 396), (64, 440), (63, 490), (58, 540), (51, 580), (46, 601)],
        [(52, 396), (48, 440), (44, 490), (40, 540), (37, 590), (37, 604)],
        [(21, 548), (29, 562), (35, 582), (37, 600)],
        [(60, 372), (64, 394), (70, 420), (78, 446)],
        F['sart_out'],
        # Adductors: adductor longus, and pectineus beside it.
        [(19, 412), (22, 444), (21, 476), (17, 506)],
        [(34, 397), (30, 420), (25, 442)],
        # The shin bone's front edge and the kneecap's tendon.
        [(40, 650), (39, 690), (37, 730), (34, 768)],
        [(36, 636), (37, 648)], [(44, 636), (43, 648)],
        # Lower leg: the shin (tibialis anterior and the long toe extensor).
        [(52, 646), (56, 680), (53, 720), (45, 760), (40, 778)],
        [(60, 650), (61, 690), (56, 730), (50, 770)],
    ]


def front_outline():
    head = []
    for a in range(0, 361, 8):
        t = math.radians(a)
        x = 34 * math.cos(t)
        if math.sin(t) >= 0:
            y = 62 - 46 * math.sin(t)
        else:
            k = -math.sin(t)
            x *= 1 - 0.32 * k ** 2           # the jaw narrows to the chin
            y = 62 + 52 * k
        head.append((x, y))
    return {
        'head_full': head,
        'neck': [[(26, 100), (29, 108), (31, 116)]],
        'ear': [(33, 58), (38, 60), (40, 70), (38, 82), (33, 88)],
        'hand': back_outline()['hand'],
        'fingers': [[HAND(40, 12), HAND(44, 5), HAND(42, -4), HAND(40, -13)],
                    [HAND(20, -12), HAND(30, -2), HAND(36, 10)]],
        'feet': [[(51, 762), (50, 776), (52, 790), (57, 804), (60, 816), (58, 824), (46, 828),
                  (34, 828), (24, 826), (22, 816), (25, 800), (28, 786), (28, 772)],
                 [(48, 818), (49, 826)], [(41, 819), (41, 827)], [(33, 818), (32, 827)],
                 [(52, 786), (54, 792)], [(27, 786), (25, 792)]],
        # kneecap and its tendon, the shin bone's front edge, the navel,
        # the notch at the top of the sternum
        'extra': [[(40, 607), (48, 611), (51, 622), (46, 633), (40, 636), (34, 633), (30, 622),
                   (32, 611), (40, 607)],
                  # outline of the knee and lower leg where no muscle group is
                  [(66, 603), (63, 612), (61, 626), (63, 638)],
                  [(24, 614), (26, 624), (23, 638), (25, 636)],
                  [(56, 728), (53, 742), (51, 754), (51, 762)],
                  [(22, 740), (26, 756), (28, 772)]],
        'mid': [[(-2, 318), (0, 324), (2, 318)], [(-4, 146), (0, 150), (4, 146)]],
    }


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
            if shade > 0.28 and rng.random() < 0.55:
                # deepest shadow: a short cross stroke over the fiber stroke
                c = lerp(s, e, (t0 + t1) / 2)
                a = math.atan2(uy, ux) + math.radians(rng.uniform(50, 70))
                l2 = rng.uniform(4, 8)
                out.append([(c[0] - math.cos(a) * l2, c[1] - math.sin(a) * l2), c,
                            (c[0] + math.cos(a) * l2, c[1] + math.sin(a) * l2)])
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
    defs, fills, ink, hatching, detail_ink, out_ink, heavy, tones = [], [], [], [], [], [], [], []

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
        # Tone: a soft wash, clear on the lit side of each muscle and
        # darkening toward its shadow side, like graphite rubbed in under
        # the pen lines.
        for side in ('L', 'R'):
            for k, poly in enumerate(polys):
                p = dedupe([to_xy(q, side) for q in poly])
                (cx, cy), size = centroid(p)
                gid_t = '%s-t%s%d' % (rid, side, k)
                h = size * 0.55
                defs.append('<linearGradient id="%s" gradientUnits="userSpaceOnUse" '
                            'x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f">'
                            '<stop offset=".35" stop-color="var(--pen,#22347F)" stop-opacity="0"/>'
                            '<stop offset="1" stop-color="var(--pen,#22347F)" stop-opacity=".2"/>'
                            '</linearGradient>'
                            % (gid_t, cx + LIGHT[0] * h, cy + LIGHT[1] * h,
                               cx - LIGHT[0] * h, cy - LIGHT[1] * h))
                tones.append('<path fill="url(#%s)" d="%s"/>' % (gid_t, smooth(p, closed=True)))
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

    if 'head' in outline:
        out_ink.append(smooth(wobble([to_xy(q, 'L') for q in outline['head']], rng)))
    if 'head_full' in outline:
        out_ink.append(smooth(wobble([to_xy(q, 'L') for q in outline['head_full']], rng), True))
    for key in ('neck', 'fingers', 'feet', 'extra'):
        for line in outline.get(key, []):
            ink_line(line)
    for line in outline.get('spine', []) + outline.get('mid', []):
        detail_ink.append(smooth(wobble([to_xy(q, 'L') for q in line], rng, 0.3)))
    ink_line(outline['ear'])
    ink_line(outline['hand'])

    css = ('.mm-muscle{fill:var(--mm-fill,transparent)}'
           '.mm-ink{fill:none;stroke:var(--pen,#22347F);stroke-linecap:round;stroke-linejoin:round}'
           '.mm-ink,.mm-tone{pointer-events:none}'
           '.mm-line{stroke-width:1.5}.mm-heavy{stroke-width:1.2}.mm-out{stroke-width:2}'
           '.mm-detail{stroke-width:1;opacity:.85}.mm-hatch{stroke-width:.7;opacity:.7}')
    return ''.join([
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" class="mm mm-%s">' % (W, H, view),
        '<style>%s</style>' % css,
        '<g class="mm-regions">%s</g>' % ''.join(fills),
        '<defs>%s</defs>' % ''.join(defs),
        '<g class="mm-tone">%s</g>' % ''.join(tones),
        '<g class="mm-ink mm-hatch">%s</g>' % hatch_svg,
        '<g class="mm-ink mm-detail"><path d="%s"/></g>' % ''.join(detail_ink),
        '<g class="mm-ink mm-line"><path d="%s"/></g>' % ''.join(ink),
        '<g class="mm-ink mm-heavy"><path d="%s"/></g>' % ''.join(heavy),
        '<g class="mm-ink mm-out"><path d="%s"/></g>' % ''.join(out_ink),
        '</svg>',
    ])


def svg_back():
    return build('back', back_regions(), back_details(), back_outline(), back_fibers(), 409)


def svg_front():
    return build('front', front_regions(), front_details(), front_outline(), front_fibers(), 434)


if __name__ == '__main__':
    for name, fn in (('muscle-back.svg', svg_back), ('muscle-front.svg', svg_front)):
        out = ROOT / 'art' / name
        s = fn()
        out.write_text(s)
        print('wrote', out.relative_to(ROOT), len(s), 'bytes')
