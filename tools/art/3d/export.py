"""Export the Composition figure as one light 3D model for the app (three.js).

Run:  OUT=/path/ python3 -I export.py
Writes OUT/figure.glb and OUT/figure.json.

Every point of the model carries:
  _PART   which of the app's 46 parts it belongs to (1 to 46; 0 = not tappable)
  _PIECE  which model piece it came from (outlines are drawn where pieces meet)
  _FIBER  the piece's long direction, for hatching along the muscle
  _AOA    how tucked into a crease it is (short reach)
  _AOB    how shut in it is (long reach: armpits, between the legs)
"""
import json
import math
import os
import sys

import bpy
import bmesh
import mathutils
import numpy as np
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene  # noqa: E402
import rig  # noqa: E402
import skin  # noqa: E402
from parts import ORDER, BY_NAME, base  # noqa: E402

OUT = os.environ.get('OUT', '/home/claude/3d/live/')
TARGET_TRIS = int(os.environ.get('TRIS', 520000))
os.makedirs(OUT, exist_ok=True)

objs, musc = scene.build()
sc = bpy.context.scene
print('built', len(objs))
# the skeleton, from the bones, before hidden bones are dropped
bones = rig.find(objs)
print('bones', len(bones))


def world_verts(o):
    n = len(o.data.vertices)
    co = np.empty(n * 3, np.float64)
    o.data.vertices.foreach_get('co', co)
    M = np.array(o.matrix_world)
    return co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]


# ---------- 1. keep only pieces that can be seen from some angle ----------
def code(i):
    return ((i >> 8) * 16 + 8, ((i >> 4) & 15) * 16 + 8, (i & 15) * 16 + 8)


sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'FLAT'
sh.color_type = 'OBJECT'
sc.display.render_aa = 'OFF'
sc.view_settings.view_transform = 'Raw'
sc.render.dither_intensity = 0
sc.render.film_transparent = True
for i, o in enumerate(objs, start=1):
    r, g, b = code(i)
    o.color = (r / 255, g / 255, b / 255, 1)
cam_data = bpy.data.cameras.new('vis')
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 2.1
cam = bpy.data.objects.new('vis', cam_data)
sc.collection.objects.link(cam)
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 520, 800
center = mathutils.Vector((0, 0, 0.88))
seen = set()
from PIL import Image  # noqa: E402
srgb = lambda c: ((c / 255) ** 2.2)  # noqa: E731
for pitch in (-26, 0, 28):
    for yaw in range(0, 360, 20):
        y, p = math.radians(yaw), math.radians(pitch)
        d = mathutils.Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
        cam.location = center + d * 6
        cam.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        path = f'/tmp/vis_{yaw}_{pitch}.png'
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        a = np.asarray(Image.open(path).convert('RGBA')).astype(np.int64)
        m = a[..., 3] > 200
        q = np.clip(np.round((a[..., :3] - 8) / 16), 0, 15).astype(np.int64)
        ids = (q[..., 0] << 8) | (q[..., 1] << 4) | q[..., 2]
        u, c = np.unique(ids[m], return_counts=True)
        good = [(int(x), n) for x, n in zip(u, c) if 1 <= x <= len(objs)]
        if yaw == 0 and pitch == 0:
            print('read back', sum(n for _, n in good), 'of', int(m.sum()), 'pixels as real pieces')
        seen.update(x for x, n in good if n >= 2)
keep = [o for i, o in enumerate(objs, start=1) if i in seen]
print('seen from some angle:', len(keep), 'of', len(objs))
# a check that the colour coding read back right: the big muscles must be there
for must in ('Latissimus dorsi muscle.l', 'Rectus femoris muscle.r', 'Head'):
    assert any(o.name == must for o in keep), must
# stray bits by the jaw that float free once the face is gone
for o in list(keep):
    if base(o.name) in ('Hyoid bone', 'Thyroid cartilage', 'Cricoid cartilage', 'Mentalis muscle', 'Geniohyoid muscle',
                        'Anterior belly of digastric muscle', 'Intermediate tendon of digastric muscle',
                        'External part of thyro-arytenoid muscle', 'Thyro-epiglottic part of thyro-arytenoid muscle',
                        'Oblique part of cricothyroid muscle', 'Straight part of cricothyroid muscle'):
        keep.remove(o)
for o in objs:
    if o not in keep:
        bpy.data.objects.remove(o, do_unlink=True)
objs = keep

# the outer obliques come with their faces turned every which way: point each face away
# from the middle of the trunk, or the crease bake looks into the body and paints them black
obl = [o for o in objs if base(o.name) == 'External abdominal oblique muscle']
axis = np.vstack([world_verts(o) for o in obl]).mean(0)
for o in obl:
    bm = bmesh.new(); bm.from_mesh(o.data)
    M = o.matrix_world
    R = M.to_3x3()
    flip = []
    for f in bm.faces:
        c = M @ f.calc_center_median()
        n = R @ f.normal
        if (c.x - axis[0]) * n.x + (c.y - axis[1]) * n.y < 0:
            flip.append(f)
    bmesh.ops.reverse_faces(bm, faces=flip)
    bm.to_mesh(o.data); bm.free(); o.data.update()
    print('obliques: turned', len(flip), 'faces of', len(o.data.polygons), 'in', o.name)

# ---------- 2. parts, pieces, fiber direction ----------
part_of = {}
for o in objs:
    p = BY_NAME.get(base(o.name))
    part_of[o.name] = ORDER.index(p) + 1 if p else 0

# the sheets: points lying over another part we want to tap take that part
SHEETS = ('External abdominal oblique muscle', 'Internal abdominal oblique muscle', 'Transversus abdominis muscle',
          'Descending part of trapezius muscle', 'Transverse part of trapezius muscle', 'Ascending part of trapezius muscle',
          'Iliotibial tract')
UNDER = {'abs': ('Rectus abdominis muscle', 'Linea alba'), 'rhomboids': ('Rhomboid major muscle', 'Rhomboid minor muscle'),
         'vastus-lateralis': ('Vastus lateralis muscle',), 'tfl': ('Tensor fasciae latae',)}
trees = {}
for part, names in UNDER.items():
    vs, ps = [], []
    for o in objs:
        if base(o.name) in names:
            off = len(vs)
            vs += [tuple(v) for v in world_verts(o)]
            ps += [tuple(off + i for i in poly.vertices) for poly in o.data.polygons]
    if vs:
        trees[part] = BVHTree.FromPolygons(vs, ps)


def wrist_and_ankle():
    out = {}
    for side in ('l', 'r'):
        hum = world_verts(bpy.data.objects[f'Humerus.{side}'])
        top = hum[hum[:, 2] > np.percentile(hum[:, 2], 94)].mean(0)
        fore = np.vstack([world_verts(bpy.data.objects[n]) for n in (f'Radius.{side}', f'Ulna.{side}') if n in bpy.data.objects])
        reach = np.linalg.norm(fore - top, axis=1).max()
        tib = np.vstack([world_verts(bpy.data.objects[n]) for n in (f'Tibia.{side}', f'Fibula.{side}') if n in bpy.data.objects])
        out[side] = (top, reach, tib[:, 2].min())
    return out


limits = wrist_and_ankle()
FOREARM = {ORDER.index(p) + 1 for p in ('brachioradialis', 'wrist-flexors', 'wrist-extensors')}
LOWLEG = {ORDER.index(p) + 1 for p in ('tibialis-anterior', 'gastroc-medial', 'gastroc-lateral', 'soleus')}

pieces = []
for k, o in enumerate(objs, start=1):
    me = o.data
    P = world_verts(o)
    n = len(P)
    part = np.full(n, part_of[o.name], np.float32)
    if base(o.name) in SHEETS:
        nr = np.empty(n * 3)
        me.vertices.foreach_get('normal', nr)
        N = nr.reshape(-1, 3) @ np.linalg.inv(np.array(o.matrix_world)[:3, :3])
        N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
        for i in range(n):
            best = None
            for pname, tree in trees.items():
                hit = tree.ray_cast(mathutils.Vector(P[i] + N[i] * 0.002), mathutils.Vector(-N[i]), 0.04)
                if hit[0] is not None and (best is None or hit[3] < best[1]):
                    best = (pname, hit[3])
            if best:
                part[i] = ORDER.index(best[0]) + 1
    side = o.name.rsplit('.', 1)[-1]
    if side in ('l', 'r'):
        top, reach, ankle = limits[side]
        if part_of[o.name] in FOREARM:
            part[np.linalg.norm(P - top, axis=1) > reach + 0.004] = 0
        if part_of[o.name] in LOWLEG:
            part[P[:, 2] < ankle + 0.01] = 0
    # the long direction of the piece (for hatching along the fibers)
    c = P - P.mean(0)
    _, _, vt = np.linalg.svd(c[:: max(1, n // 3000)], full_matrices=False)
    fib = vt[0]
    fib_gl = np.array([fib[0], fib[2], -fib[1]], np.float32)   # into the model file's up-is-y axes
    for name, vals, size in (('_PART', part, 1), ('_PIECE', np.full(n, k, np.float32), 1), ('_FIBER', np.tile(fib_gl, (n, 1)), 3)):
        at = me.attributes.new(name, 'FLOAT' if size == 1 else 'FLOAT_VECTOR', 'POINT')
        at.data.foreach_set('value' if size == 1 else 'vector', vals.astype(np.float32).ravel())
    pieces.append({'name': o.name, 'part': ORDER[part_of[o.name] - 1] if part_of[o.name] else None})

# ---------- 3. lighter: fewer triangles, keeping small pieces whole ----------
tris = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs}
total = sum(tris.values())
ratio = min(1.0, TARGET_TRIS / total)
print('triangles', total, 'ratio', round(ratio, 3))
for o in objs:
    if tris[o.name] < 400 or ratio >= 0.999:
        continue
    r = max(ratio, 400 / tris[o.name])
    mod = o.modifiers.new('slim', 'DECIMATE')
    mod.ratio = r
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier='slim')

# where the head is, for its construction lines (in the model file's axes)
hv = world_verts(bpy.data.objects['Head'])
head_min, head_max = hv.min(0), hv.max(0)
to_gl = lambda v: [float(v[0]), float(v[2]), float(-v[1])]  # noqa: E731
head_info = {'center': to_gl((head_min + head_max) / 2), 'size': [float(head_max[0] - head_min[0]), float(head_max[2] - head_min[2]), float(head_max[1] - head_min[1])],
             'piece': next(i for i, o in enumerate(objs, start=1) if o.name == 'Head')}

# ---------- 4. one model, smooth ----------
bpy.ops.object.select_all(action='DESELECT')
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
# Right-side pieces are mirrored copies of the left. Settling each piece's
# own transform first turns their faces the right way out; joining them
# as they are would leave that whole side facing inward.
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.join()
fig = bpy.context.active_object
fig.name = 'Figure'
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.shade_smooth()
print('joined', len(fig.data.vertices), 'points', sum(len(p.vertices) - 2 for p in fig.data.polygons), 'triangles')

# ---------- 4b. the skeleton's hold on each point, and each muscle's squeeze ----------
if os.environ.get('SAVE_PRE'):
    json.dump([{k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in b.items()} for b in bones], open(OUT + 'bones.json', 'w'))
    bpy.ops.wm.save_as_mainfile(filepath=OUT + 'pre_skin.blend')
joints, wts = skin.weights(fig, bones)
bpy.ops.object.select_all(action='DESELECT')
fig.select_set(True)
bpy.context.view_layer.objects.active = fig
flex_d, flex_n, vac_d = skin.flex(fig, ORDER)
print('skinned; biggest squeeze', round(float(np.abs(flex_d).max()), 4), 'vacuum', round(float(np.abs(vac_d).max()), 4))

# ---------- 5. creases and shut-in places, baked into the points ----------
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 48
sc.render.bake.target = 'VERTEX_COLORS'
world = bpy.data.worlds.new('w')
sc.world = world
mat = bpy.data.materials.new('clay')
mat.use_nodes = True
fig.data.materials.clear()
fig.data.materials.append(mat)
for name, reach in (('_AOA', 0.022), ('_AOB', 0.11)):
    ca = fig.data.color_attributes.new('bake', 'FLOAT_COLOR', 'POINT')
    fig.data.color_attributes.active_color = ca
    world.light_settings.distance = reach
    bpy.ops.object.bake(type='AO')
    col = np.empty(len(ca.data) * 4, np.float32)
    ca.data.foreach_get('color', col)
    at = fig.data.attributes.new(name, 'FLOAT', 'POINT')
    at.data.foreach_set('value', col.reshape(-1, 4)[:, 0].copy())
    fig.data.color_attributes.remove(ca)
    print('baked', name)
fig.data.materials.clear()

# ---------- 6. write it ----------
# figure.bin, all little-endian, in the model file's axes (y up, facing +z):
#   'CMP4', u32 points, u32 corners
#   position f32 x3 | index u32 | piece u16 | normal i8 x4 | fiber i8 x4 | part u8 | aoa u8 | aob u8
#   joints u8 x4 | weights u8 x4 | squeeze offset i8 x4 | squeeze normal i8 x4 | vacuum offset i8 x4
me = fig.data
n = len(me.vertices)
gl = lambda A: np.c_[A[:, 0], A[:, 2], -A[:, 1]]  # noqa: E731
co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
nr = np.empty(n * 3); me.vertices.foreach_get('normal', nr); nr = nr.reshape(-1, 3)
me.calc_loop_triangles()
tri = np.empty(len(me.loop_triangles) * 3, np.int64)
me.loop_triangles.foreach_get('vertices', tri)


def attr(name, size=1):
    a = me.attributes[name]
    v = np.empty(len(a.data) * size, np.float32)
    a.data.foreach_get('value' if size == 1 else 'vector', v)
    return v.reshape(-1, size) if size > 1 else v


def snorm4(v, scale=None):
    out = np.zeros((len(v), 4), np.int8)
    if scale is None:
        v = v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-12)
        out[:, :3] = np.clip(np.round(v * 127), -127, 127)
    else:
        out[:, :3] = np.clip(np.round(v / scale), -127, 127)
    return out


FLEX_SCALE, VAC_SCALE = 0.00015, 0.00025
w8 = np.round(wts * 255).astype(np.int32)
w8[:, 0] += 255 - w8.sum(1)          # the four weights add to exactly 255
with open(OUT + 'figure.bin', 'wb') as f:
    f.write(b'CMP4' + np.array([n, len(tri)], '<u4').tobytes())
    for arr in (gl(co).astype('<f4'), tri.astype('<u4'), np.round(attr('_PIECE')).astype('<u2'),
                snorm4(gl(nr)), snorm4(attr('_FIBER', 3)), np.round(attr('_PART')).astype(np.uint8),
                np.clip(np.round(attr('_AOA') * 255), 0, 255).astype(np.uint8),
                np.clip(np.round(attr('_AOB') * 255), 0, 255).astype(np.uint8),
                joints.astype(np.uint8), np.clip(w8, 0, 255).astype(np.uint8),
                snorm4(gl(flex_d), FLEX_SCALE), snorm4(gl(flex_n)), snorm4(gl(vac_d), VAC_SCALE)):
        f.write(np.ascontiguousarray(arr).tobytes())
info = {
    'parts': ORDER,
    'pieces': pieces,
    'head': head_info,
    'bones': [{'name': b['name'], 'head': to_gl(b['head']), 'tail': to_gl(b['tail']), 'parent': b['parent']} for b in bones],
    'flexScale': FLEX_SCALE,
    'vacScale': VAC_SCALE,
}
json.dump(info, open(OUT + 'figure.json', 'w'))
print('done', n, 'points', len(tri) // 3, 'triangles', os.path.getsize(OUT + 'figure.bin') // 1024, 'KB')
