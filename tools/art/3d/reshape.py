"""Reshape the Z-Anatomy figure: a Classic Physique build and arms 30 degrees out.

grow(objs)       fills out muscles along their surface normals, most at the
                 belly and fading to nothing at the tendons, so attachments stay put.
pose_arms(objs)  turns each arm out at the shoulder. Arm bones and arm muscles
                 turn as one piece; muscles that cross the shoulder blend from
                 the torso to the arm; everything else stays still.
Distances are in meters (the model is 1.79 m tall).
"""
import math

import bpy
import numpy as np

# How far each muscle's belly is pushed out, in meters.
GROW = {
    'Acromial part of deltoid muscle': 0.021, 'Clavicular part of deltoid muscle': 0.017,
    'Scapular spinal part of deltoid muscle': 0.017,
    'Clavicular head of pectoralis major muscle': 0.013, 'Sternocostal head of pectoralis major muscle': 0.015,
    '(Abdominal part of pectoralis major muscle)': 0.009,
    'Latissimus dorsi muscle': 0.026, 'Teres major muscle': 0.009, 'Teres minor muscle': 0.005,
    'Infraspinatus muscle': 0.008,
    'Descending part of trapezius muscle': 0.011, 'Transverse part of trapezius muscle': 0.007,
    'Ascending part of trapezius muscle': 0.005,
    'Long head of biceps brachii': 0.015, 'Short head of biceps brachii': 0.014, 'Brachialis muscle': 0.008,
    'Long head of triceps brachii': 0.014, 'Lateral head of triceps brachii': 0.014, 'Medial head of triceps brachii': 0.008,
    'Brachioradialis muscle': 0.012, 'Extensor carpi radialis longus': 0.008, 'Extensor carpi radialis brevis': 0.006,
    'Flexor carpi radialis': 0.004, 'Humeral head of flexor carpi ulnaris': 0.004, 'Palmaris longus muscle': 0.003,
    'Superficial head of pronator teres': 0.004, 'Extensor digitorum': 0.003, 'Humeral head of extensor carpi ulnaris': 0.003,
    'Serratus anterior muscle': 0.005,
    'External abdominal oblique muscle': -0.012,
    'Gluteus maximus muscle': 0.011, 'Gluteus medius muscle': 0.008,
    'Rectus femoris muscle': 0.017, 'Vastus lateralis muscle': 0.021, 'Vastus medialis muscle': 0.019,
    'Vastus intermedius muscle': 0.008, 'Sartorius muscle': 0.004, 'Tensor fasciae latae': 0.006,
    'Adductor longus': 0.008, 'Adductor magnus': 0.011, 'Gracilis muscle': 0.004, 'Pectineus muscle': 0.004,
    'Long head of biceps femoris': 0.013, 'Short head of biceps femoris': 0.006,
    'Semitendinosus muscle': 0.012, 'Semimembranosus muscle': 0.011,
    'Medial head of gastrocnemius': 0.015, 'Lateral head of gastrocnemius': 0.013, 'Soleus muscle': 0.010,
    'Tibialis anterior muscle': 0.005,
    'Iliocostalis lumborum muscle': 0.006, 'Longissimus thoracis muscle': 0.008,
    'Sternocleidomastoid muscle': 0.004,
}


def base(name):
    return name.rsplit('.', 1)[0] if name.rsplit('.', 1)[-1] in ('l', 'r') else name


def world_coords(o):
    n = len(o.data.vertices)
    co = np.empty(n * 3, np.float64)
    o.data.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    M = np.array(o.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3], M


def set_world(o, P, M):
    Minv = np.linalg.inv(M)
    loc = P @ Minv[:3, :3].T + Minv[:3, 3]
    o.data.vertices.foreach_set('co', loc.astype(np.float32).ravel())
    o.data.update()


def world_normals(o, M):
    n = len(o.data.vertices)
    nr = np.empty(n * 3, np.float64)
    o.data.vertices.foreach_get('normal', nr)
    nr = nr.reshape(-1, 3)
    N = np.linalg.inv(M[:3, :3]).T
    nr = nr @ N.T
    return nr / (np.linalg.norm(nr, axis=1, keepdims=True) + 1e-12)


def smooth_normals(o, N, rounds=12):
    """Average each point's direction with its neighbours', so the push follows
    the muscle's overall shape instead of its fine fiber ridges."""
    ne = len(o.data.edges)
    e = np.empty(ne * 2, np.int64)
    o.data.edges.foreach_get('vertices', e)
    e = e.reshape(-1, 2)
    for _ in range(rounds):
        acc = N.copy()
        np.add.at(acc, e[:, 0], N[e[:, 1]])
        np.add.at(acc, e[:, 1], N[e[:, 0]])
        N = acc / (np.linalg.norm(acc, axis=1, keepdims=True) + 1e-12)
    return N


def grow(objs, scale=1.0):
    done = 0
    for o in objs:
        amount = GROW.get(base(o.name))
        if not amount:
            continue
        P, M = world_coords(o)
        N = smooth_normals(o, world_normals(o, M))
        # position along the muscle's length, 0 at one end and 1 at the other
        c = P - P.mean(0)
        _, _, vt = np.linalg.svd(c[:: max(1, len(c) // 4000)], full_matrices=False)
        t = c @ vt[0]
        t = (t - t.min()) / (t.max() - t.min() + 1e-9)
        w = np.sin(np.pi * t) ** 0.8
        b = base(o.name)
        if b == 'Latissimus dorsi muscle':
            # the wings: most of the growth at the outer edge, under the arm
            w *= 0.35 + 0.65 * smoothstep(0.08, 0.17, np.abs(P[:, 0]))
        if b == 'External abdominal oblique muscle':
            # a smaller waist: pull in the sides only, not the sheet over the abs
            w = smoothstep(0.09, 0.14, np.abs(P[:, 0])) * smoothstep(0.85, 1.05, P[:, 2]) * (1 - smoothstep(1.15, 1.3, P[:, 2]))
        set_world(o, P + N * (amount * scale * w)[:, None], M)
        done += 1
    print('grew', done)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def chain(o):
    out = []
    while o.parent:
        o = o.parent
        out.append(o.name)
    return out


def classify(o, parents):
    """'arm' turns with the arm, 'blend' stretches across the shoulder, None stays."""
    p = parents.get(o.name, [])
    b = base(o.name)
    if 'Bones of free part of upper limb.g' in p:
        return 'arm'
    if 'Muscles of upper limb.g' in p:
        return 'blend' if 'Scapulohumeral muscles.g' in p else 'arm'
    if b in ('Clavicular head of pectoralis major muscle', 'Sternocostal head of pectoralis major muscle',
             '(Abdominal part of pectoralis major muscle)', 'Latissimus dorsi muscle', 'Pectoralis minor muscle'):
        return 'blend'
    return None


def pose_arms(objs, parents, target_deg=30.0):
    for side in ('l', 'r'):
        hum = bpy.data.objects.get(f'Humerus.{side}')
        P, _ = world_coords(hum)
        top = P[P[:, 2] > np.percentile(P[:, 2], 94)].mean(0)
        bot = P[P[:, 2] < np.percentile(P[:, 2], 6)].mean(0)
        d = bot - top
        now = math.degrees(math.atan2(abs(d[0]), -d[2]))
        turn = math.radians(target_deg - now)
        sgn = 1 if top[0] > 0 else -1
        phi = -sgn * turn
        arm = d / np.linalg.norm(d)
        R = np.array([[math.cos(phi), 0, math.sin(phi)], [0, 1, 0], [-math.sin(phi), 0, math.cos(phi)]])
        print(f'arm {side}: now {now:.1f} deg, turning {math.degrees(turn):.1f}')
        for o in objs:
            if not o.name.endswith('.' + side):
                continue
            kind = classify(o, parents)
            if not kind:
                continue
            P, M = world_coords(o)
            v = P - top
            if kind == 'arm':
                w = np.ones(len(P))
            else:
                s = v @ arm                                   # how far down the arm
                # only the part wrapped around the upper-arm bone follows the arm
                along = np.clip(s, 0, np.linalg.norm(d))
                off = np.linalg.norm(v - along[:, None] * arm[None], axis=1)
                w = smoothstep(-0.015, 0.11, s) * (1 - smoothstep(0.045, 0.085, off))
                if 'deltoid' not in o.name:
                    # the chest, lats and teres only follow near where they
                    # attach at the top of the arm
                    w *= 1 - smoothstep(0.08, 0.15, np.linalg.norm(v, axis=1))
            # turn each point about the shoulder by its share of the angle
            ang = phi * w
            c, s_ = np.cos(ang), np.sin(ang)
            x = v[:, 0] * c + v[:, 2] * s_
            z = -v[:, 0] * s_ + v[:, 2] * c
            Q = np.stack([x, v[:, 1], z], 1) + top
            set_world(o, Q, M)
