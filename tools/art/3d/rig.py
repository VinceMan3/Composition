"""The figure's skeleton, found from the model's own bones.

    bones = rig.find(objs)   # list of dicts: name, head, tail, parent (index or -1), finger (bool)

Every position is in Blender's world (meters, z up, the figure faces -y).
Joints come from the bones themselves: ball joints by fitting a sphere to the
joint's surface, hinges and the spine from the ends and middles of the bones.
"""
import numpy as np


def _pts(objs, name):
    for o in objs:
        if o.name == name:
            n = len(o.data.vertices)
            co = np.empty(n * 3)
            o.data.vertices.foreach_get('co', co)
            M = np.array(o.matrix_world)
            return co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    raise KeyError(name)


def _sphere(P):
    """Least-squares sphere through points: center."""
    A = np.c_[2 * P, np.ones(len(P))]
    b = (P ** 2).sum(1)
    x, *_ = np.linalg.lstsq(A, b, rcond=None)
    return x[:3]


def _ends(P, toward):
    """The two ends of a long bone, the first one nearer `toward`."""
    c = P.mean(0)
    _, _, vt = np.linalg.svd(P - c, full_matrices=False)
    ax = vt[0]
    s = (P - c) @ ax
    lo, hi = np.percentile(s, 4), np.percentile(s, 96)
    a = P[s <= lo].mean(0)
    b = P[s >= hi].mean(0)
    return (a, b) if np.linalg.norm(a - toward) < np.linalg.norm(b - toward) else (b, a)


def _body(objs, name):
    """The middle of a vertebra's body (the front half of the bone)."""
    P = _pts(objs, name)
    front = P[P[:, 1] < np.median(P[:, 1])]
    return front.mean(0)


FINGERS = {1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth'}
FNAME = {1: 'thumb', 2: 'index', 3: 'middle', 4: 'ring', 5: 'pinky'}


def find(objs):
    bones = []

    def add(name, head, tail, parent, finger=False):
        bones.append({'name': name, 'head': np.asarray(head, float), 'tail': np.asarray(tail, float),
                      'parent': -1 if parent is None else [b['name'] for b in bones].index(parent), 'finger': finger})

    # ----- hips and spine -----
    hip = {}
    for s in ('l', 'r'):
        F = _pts(objs, f'Femur.{s}')
        top = F[F[:, 2] > F[:, 2].max() - 0.09]
        # the head is the inner part of the top of the femur
        inner = top[np.abs(top[:, 0]) < np.percentile(np.abs(top[:, 0]), 45)]
        hip[s] = _sphere(inner)
    mid = (hip['l'] + hip['r']) / 2
    L5, L1 = _body(objs, 'Vertebra L5'), _body(objs, 'Vertebra L1')
    T12, T7, T1 = _body(objs, 'Vertebra T12'), _body(objs, 'Vertebra T7'), _body(objs, 'Vertebra T1')
    C7, C4 = _body(objs, 'Vertebra C7'), _body(objs, 'Vertebra C4')
    H = _pts(objs, 'Head')
    head_c = H.mean(0)
    add('pelvis', mid, L5, None)
    add('spine1', L5, T12, 'pelvis')
    add('spine2', T12, T7, 'spine1')
    add('spine3', T7, T1, 'spine2')
    add('neck', C7, C4 + (C4 - C7) * 0.8, 'spine3')
    add('head', C4 + (C4 - C7) * 0.8, np.array([head_c[0], head_c[1], H[:, 2].max()]), 'neck')

    for s in ('l', 'r'):
        # ----- arm -----
        Cl = _pts(objs, f'Clavicle.{s}')
        sc, ac = _ends(Cl, np.array([0, Cl[:, 1].mean(), Cl[:, 2].mean()]))
        Hu = _pts(objs, f'Humerus.{s}')
        hu_top, hu_bot = _ends(Hu, ac)
        near = Hu[np.linalg.norm(Hu - hu_top, axis=1) < 0.035]
        shoulder = _sphere(near)
        R = _pts(objs, f'Radius.{s}')
        U = _pts(objs, f'Ulna.{s}')
        r_top, r_bot = _ends(R, hu_bot)
        u_top, u_bot = _ends(U, hu_bot)
        elbow = (hu_bot * 0.6 + (r_top + u_top) / 2 * 0.4)
        wrist = (r_bot * 0.6 + u_bot * 0.4)
        M3 = _pts(objs, f'Third metacarpal bone.{s}')
        m3a, m3b = _ends(M3, wrist)
        add(f'clavicle.{s}', sc, ac, 'spine3')
        add(f'upperarm.{s}', shoulder, elbow, f'clavicle.{s}')
        fore_mid = elbow + (wrist - elbow) * 0.5
        add(f'forearm.{s}', elbow, fore_mid, f'upperarm.{s}')
        add(f'twist.{s}', fore_mid, wrist, f'forearm.{s}')
        add(f'hand.{s}', wrist, m3b, f'twist.{s}')
        # ----- fingers: three bones each, from the phalanges -----
        for k in range(1, 6):
            nm = FINGERS[k]
            pieces = ([f'First metacarpal bone.{s}'] if k == 1 else []) + \
                [f'{part} phalanx of {nm} finger of hand.{s}' for part in (('Proximal', 'Distal') if k == 1 else ('Proximal', 'Middle', 'Distal'))]
            ends = [_ends(_pts(objs, n), wrist) for n in pieces]
            # joints: where one piece ends and the next begins (the middle of the gap)
            joints = [ends[0][0]] + [(ends[i][1] + ends[i + 1][0]) / 2 for i in range(len(ends) - 1)] + [ends[-1][1]]
            parent = f'hand.{s}'
            for i in range(len(joints) - 1):
                n = f'{FNAME[k]}{i + 1}.{s}'
                add(n, joints[i], joints[i + 1], parent, finger=True)
                parent = n
        # ----- leg -----
        F = _pts(objs, f'Femur.{s}')
        f_top, f_bot = _ends(F, hip[s])
        T = _pts(objs, f'Tibia.{s}')
        t_top, t_bot = _ends(T, f_bot)
        knee = (f_bot + t_top) / 2
        ankle = _pts(objs, f'Talus.{s}').mean(0)
        balls = []
        tips = []
        for k in range(1, 6):
            M = _pts(objs, f'{["First", "Second", "Third", "Fourth", "Fifth"][k - 1]} metatarsal bone.{s}')
            a, b = _ends(M, ankle)
            balls.append(b)
            D = _pts(objs, f'Distal phalanx of {FINGERS[k]} finger of foot.{s}')
            tips.append(D[np.argmin(D[:, 1])])
        ball = np.mean(balls[:3], axis=0)
        tip = np.mean(tips[:3], axis=0)
        add(f'thigh.{s}', hip[s], knee, 'pelvis')
        add(f'shin.{s}', knee, ankle, f'thigh.{s}')
        add(f'foot.{s}', ankle, ball, f'shin.{s}')
        add(f'toes.{s}', ball, tip, f'foot.{s}')
    return bones
