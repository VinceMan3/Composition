"""Ties the joined figure to its skeleton, and makes each muscle's squeeze.

    W = skin.weights(fig, bones)          # (points, bones) weights, rows sum to 1
    fd, fn, vd = skin.flex(fig, parts)    # squeeze offsets, squeeze normals, vacuum offsets

Weights: Blender's bone heat on a watertight copy of the figure (a voxel
shell, made lighter), then copied onto every point from the nearest place on
that shell. Fingers are too close together for the shell, so the hand's share
is split among the finger bones by how near each point is to them.

All positions in Blender's world (meters, z up, facing -y).
"""
import bmesh
import bpy
import mathutils
import numpy as np
from mathutils.bvhtree import BVHTree


def _verts(me):
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    return co.reshape(-1, 3)


def _normals(me):
    nr = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('normal', nr)
    return nr.reshape(-1, 3)


def _attr(me, name, size=1):
    a = me.attributes[name]
    v = np.empty(len(a.data) * size, np.float32)
    a.data.foreach_get('value' if size == 1 else 'vector', v)
    return v.reshape(-1, size) if size > 1 else v


def _seg_dist(P, a, b):
    ab = b - a
    t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


HEAT_SCALE = 10.0
SMOOTH = 0.011
ARM_R = 0.075   # meters: how far from the upper arm's bone its pull is full   # meters: neighbors this close move together, so touching pieces do not tear apart


def _smooth(P, W, sigma, cell=0.007):
    """Blur the weights through space (not along the surface): every piece near a
    point gets about the same pull, deep pieces included."""
    from scipy.ndimage import gaussian_filter, map_coordinates
    lo = P.min(0) - 4 * sigma
    idx = np.floor((P - lo) / cell).astype(int)
    shape = tuple(idx.max(0) + 2 + int(4 * sigma / cell))
    flat = np.ravel_multi_index(idx.T, shape)
    cnt = np.bincount(flat, minlength=int(np.prod(shape))).astype(np.float32).reshape(shape)
    s = sigma / cell
    cnt_b = gaussian_filter(cnt, s, mode='constant')
    coords = ((P - lo) / cell - 0.5).T
    den = map_coordinates(cnt_b, coords, order=1)
    out = np.zeros_like(W)
    for j in range(W.shape[1]):
        if W[:, j].max() <= 0:
            continue
        g = np.bincount(flat, weights=W[:, j], minlength=cnt.size).astype(np.float32).reshape(shape)
        out[:, j] = map_coordinates(gaussian_filter(g, s, mode='constant'), coords, order=1)
    out = np.clip(out / np.maximum(den, 1e-9)[:, None], 0, None)
    return out / np.maximum(out.sum(1, keepdims=True), 1e-9)


def weights(fig, bones, voxel=0.009, shell_faces=10 ** 9):
    sc = bpy.context.scene
    # ----- a watertight shell of the whole figure -----
    me = fig.data.copy()
    shell = bpy.data.objects.new('shell', me)
    sc.collection.objects.link(shell)
    m = shell.modifiers.new('vox', 'REMESH')
    m.mode = 'VOXEL'
    m.voxel_size = voxel
    bpy.context.view_layer.objects.active = shell
    bpy.ops.object.select_all(action='DESELECT')
    shell.select_set(True)
    bpy.ops.object.modifier_apply(modifier='vox')
    nf = len(shell.data.polygons)
    if nf > shell_faces:
        d = shell.modifiers.new('slim', 'DECIMATE')
        d.ratio = shell_faces / nf
        bpy.ops.object.modifier_apply(modifier='slim')
    bm = bmesh.new(); bm.from_mesh(shell.data)
    # keep only the outer skin: drop little shells sealed inside the body
    bm.verts.ensure_lookup_table()
    seen, islands = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, isl = [v], []
        seen.add(v.index)
        while stack:
            x = stack.pop(); isl.append(x)
            for e in x.link_edges:
                o = e.other_vert(x)
                if o.index not in seen:
                    seen.add(o.index); stack.append(o)
        islands.append(isl)
    islands.sort(key=len, reverse=True)
    drop = [v for isl in islands[1:] for v in isl]
    bmesh.ops.delete(bm, geom=drop, context='VERTS')
    print('shell islands', len(islands), 'kept', len(islands[0]))
    # bone heat works best at a larger size: work ten times bigger
    for v in bm.verts:
        v.co *= HEAT_SCALE
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(shell.data); bm.free()
    print('shell', len(shell.data.vertices), 'points', len(shell.data.polygons), 'faces')

    # ----- the skeleton as a Blender armature; fingers left out of the heat -----
    ad = bpy.data.armatures.new('rig')
    arm = bpy.data.objects.new('rig', ad)
    sc.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = []
    for b in bones:
        e = ad.edit_bones.new(b['name'])
        e.head = mathutils.Vector(b['head']) * HEAT_SCALE
        e.tail = mathutils.Vector(b['tail']) * HEAT_SCALE
        e.use_deform = not b['finger']
        if b['parent'] >= 0:
            e.parent = eb[b['parent']]
        eb.append(e)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    shell.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    names = [b['name'] for b in bones]
    gi = {g.index: names.index(g.name) for g in shell.vertex_groups if g.name in names}
    Ws = np.zeros((len(shell.data.vertices), len(bones)), np.float32)
    for v in shell.data.vertices:
        for g in v.groups:
            if g.group in gi:
                Ws[v.index, gi[g.group]] = g.weight
    empty = Ws.sum(1) == 0
    print('shell points with no weight:', int(empty.sum()))
    # points the heat missed take the nearest bone
    if empty.any():
        S = _verts(shell.data)[empty] / HEAT_SCALE
        D = np.stack([_seg_dist(S, b['head'], b['tail']) if not b['finger'] else np.full(len(S), 9.0) for b in bones], 1)
        Ws[np.where(empty)[0], D.argmin(1)] = 1
    Ws /= Ws.sum(1, keepdims=True)

    # ----- copy onto every point of the figure from the nearest place on the shell -----
    SV = _verts(shell.data) / HEAT_SCALE
    tris = np.array([tuple(p.vertices) for p in shell.data.polygons])
    tree = BVHTree.FromPolygons([tuple(v) for v in SV], [tuple(t) for t in tris])
    P = _verts(fig.data)
    W = np.zeros((len(P), len(bones)), np.float32)
    for i, p in enumerate(P):
        loc, _, fi, _ = tree.find_nearest(mathutils.Vector(p))
        a, b, c = SV[tris[fi]]
        # barycentric weights on that triangle
        v0, v1, v2 = b - a, c - a, np.array(loc) - a
        d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
        d20, d21 = v2 @ v0, v2 @ v1
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-18:
            u = vv = 1 / 3
        else:
            vv = (d11 * d20 - d01 * d21) / den
            u = (d00 * d21 - d01 * d20) / den
        w0 = max(0.0, 1 - vv - u)
        W[i] = w0 * Ws[tris[fi][0]] + max(0.0, vv) * Ws[tris[fi][1]] + max(0.0, u) * Ws[tris[fi][2]]
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    W = _smooth(P, W, SMOOTH)
    # a point only follows the limbs on its own side (the thighs touch, so the shell joins them)
    for j, b in enumerate(bones):
        side = b['name'].rsplit('.', 1)[-1]
        if side == 'l':
            W[P[:, 0] < -0.004, j] = 0
        elif side == 'r':
            W[P[:, 0] > 0.004, j] = 0
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    # the trunk stays on the ribs: away from the upper arm, the arm's pull fades fast
    for s in ('l', 'r'):
        ub = names.index(f'upperarm.{s}')
        a, b = bones[ub]['head'], bones[ub]['tail']
        d = _seg_dist(P, a, b)
        fade = np.exp(-(np.maximum(d - ARM_R, 0) / 0.03) ** 2)
        moved = W[:, ub] * (1 - fade)
        W[:, ub] -= moved
        # what the arm lets go of goes to the shoulder blade and chest it sits on
        W[:, names.index(f'clavicle.{s}')] += moved * 0.35
        W[:, names.index('spine3')] += moved * 0.65

    # ----- the hand's share, split among the fingers -----
    for s in ('l', 'r'):
        hb = names.index(f'hand.{s}')
        hp = np.where(W[:, hb] > 0.02)[0]
        if not len(hp):
            continue
        Q = P[hp]
        wrist = bones[hb]['head']
        chains = []
        for f in ('thumb', 'index', 'middle', 'ring', 'pinky'):
            idx = [names.index(f'{f}{k}.{s}') for k in (1, 2, 3)]
            chains.append(idx)
        # nearest finger chain for each point (palm points count too)
        cd = np.stack([np.min(np.stack([_seg_dist(Q, bones[j]['head'], bones[j]['tail']) for j in ch], 1), 1) for ch in chains], 1)
        best = cd.argmin(1)
        share = W[hp, hb].copy()
        new = np.zeros((len(hp), len(bones)), np.float32)
        sig = 0.0045
        for ci, ch in enumerate(chains):
            sel = best == ci
            if not sel.any():
                continue
            R = Q[sel]
            # candidates: the palm (wrist to this finger's first joint) and the finger's three bones
            palm_d = _seg_dist(R, wrist, bones[ch[0]]['head'])
            ds = [palm_d] + [_seg_dist(R, bones[j]['head'], bones[j]['tail']) for j in ch]
            D = np.stack(ds, 1)
            # how far past each joint along the finger: a point belongs to the bone it is beyond
            G = np.exp(-((D - D.min(1, keepdims=True)) / sig) ** 2)
            G /= G.sum(1, keepdims=True)
            rows = np.where(sel)[0]
            new[rows, hb] += G[:, 0]
            for k, j in enumerate(ch):
                new[rows, j] += G[:, k + 1]
        W[hp, hb] = 0
        W[hp] += new * share[:, None]
    # at most four bones per point
    top = np.argsort(-W, axis=1)[:, :4]
    W4 = np.take_along_axis(W, top, 1)
    W4 /= np.maximum(W4.sum(1, keepdims=True), 1e-9)
    bpy.data.objects.remove(shell, do_unlink=True)
    bpy.data.objects.remove(arm, do_unlink=True)
    return top.astype(np.uint8), W4.astype(np.float32)


def _smooth_vec(P, V, sigma, cell=0.006):
    """Blur vectors through space over these points only."""
    from scipy.ndimage import gaussian_filter, map_coordinates
    lo = P.min(0) - 4 * sigma
    idx = np.floor((P - lo) / cell).astype(int)
    shape = tuple(idx.max(0) + 2 + int(4 * sigma / cell))
    flat = np.ravel_multi_index(idx.T, shape)
    s = sigma / cell
    coords = ((P - lo) / cell - 0.5).T
    den = map_coordinates(gaussian_filter(np.bincount(flat, minlength=int(np.prod(shape))).astype(np.float32).reshape(shape), s, mode='constant'), coords, order=1)
    out = np.zeros_like(V)
    for j in range(V.shape[1]):
        g = np.bincount(flat, weights=V[:, j], minlength=int(np.prod(shape))).astype(np.float32).reshape(shape)
        out[:, j] = map_coordinates(gaussian_filter(g, s, mode='constant'), coords, order=1)
    return out / np.maximum(den, 1e-9)[:, None]


def flex(fig, parts):
    """Squeeze offsets per point (the muscle belly swells and draws toward its middle),
    the normals the squeezed shape would have, and the vacuum's offsets."""
    me = fig.data
    P = _verts(me)
    N = _normals(me)
    part = np.round(_attr(me, '_PART')).astype(int)
    piece = np.round(_attr(me, '_PIECE')).astype(int)
    fib_gl = _attr(me, '_FIBER', 3)
    fib = np.c_[fib_gl[:, 0], -fib_gl[:, 2], fib_gl[:, 1]]   # back to Blender's axes
    D = np.zeros_like(P)
    for key in set(zip(piece[part > 0], part[part > 0])):
        sel = np.where((piece == key[0]) & (part == key[1]))[0]
        if len(sel) < 30:
            continue
        Q = P[sel]
        F = fib[sel[0]] / (np.linalg.norm(fib[sel[0]]) + 1e-9)
        c = Q.mean(0)
        t = (Q - c) @ F
        lo, hi = np.percentile(t, 2), np.percentile(t, 98)
        L = max(hi - lo, 1e-4)
        u = np.clip((t - lo) / L, 0, 1)
        belly = np.sin(np.pi * u) ** 1.4
        across = Q - c - np.outer(t, F)
        thick = np.sqrt((across ** 2).sum(1).mean())
        amp = np.clip(0.55 * thick, 0.002, 0.017)
        D[sel] = N[sel] * (amp * belly)[:, None] - np.outer((u - 0.5) * L * 0.12 * belly, F)
    # pieces lying on each other (a sheet over a muscle) must swell together, and a
    # squeeze fades out where one part meets another, so nothing pokes through
    from scipy.spatial import cKDTree
    for pid in np.unique(part[part > 0]):
        sel = np.where(part == pid)[0]
        if len(sel) < 30:
            continue
        D[sel] = _smooth_vec(P[sel], D[sel], 0.009)
        others = np.where((part > 0) & (part != pid))[0]
        if len(others):
            dist, _ = cKDTree(P[others]).query(P[sel], k=1)
            t = np.clip((dist - 0.003) / 0.012, 0, 1)
            D[sel] *= (t * t * (3 - 2 * t))[:, None]
    # normals of the squeezed shape
    co0 = P.copy()
    me.vertices.foreach_set('co', (P + D).ravel())
    me.update()
    N1 = _normals(me)
    me.vertices.foreach_set('co', co0.ravel())
    me.update()
    # the vacuum: the stomach drawn in under the ribs, most at the middle of the abs
    vac = np.zeros_like(P)
    ab = [parts.index(p) + 1 for p in ('abs', 'external-oblique') if p in parts]
    sel = np.isin(part, ab)
    if sel.any():
        Q = P[sel]
        z0, z1 = np.percentile(Q[:, 2], 3), np.percentile(Q[:, 2], 97)
        h = (Q[:, 2] - z0) / max(z1 - z0, 1e-6)
        band = np.exp(-((h - 0.42) / 0.26) ** 2)
        front = np.clip(-N[sel][:, 1], 0, 1) ** 0.7
        idx = np.where(sel)[0]
        v = -N[sel] * (0.024 * band * (0.35 + 0.65 * front))[:, None]
        # layers move together, and the pull fades out at the edges of the stomach
        vac[idx] = _smooth_vec(P[idx], v, 0.012)
        from scipy.spatial import cKDTree
        others = np.where((part > 0) & ~sel)[0]
        dist, _ = cKDTree(P[others]).query(P[idx], k=1)
        t = np.clip((dist - 0.004) / 0.03, 0, 1)
        vac[idx] *= (t * t * (3 - 2 * t))[:, None]
    return D.astype(np.float32), N1.astype(np.float32), vac.astype(np.float32)
