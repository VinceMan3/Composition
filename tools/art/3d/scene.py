"""Builds the Composition figure in Blender: the Z-Anatomy muscles and bones,
cleaned of labels and sheets, reshaped to a Classic Physique build, arms 30
degrees out, a plain egg for the head. Used by render.py and export.py.

    objs, musc = build()   # mesh objects, and the names that came from the muscle file
"""
import math
import os
import sys

import bpy
import mathutils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reshape  # noqa: E402


def build():
    ZA = '/home/claude/3d/zanat/Resources/Models/FBX/'
    SKIP = ('fascia', 'bursa', 'sheath', 'retinaculum', 'aponeurosis', 'septum', 'cross section', 'ligament', 'capsule', 'membrane', 'disc', 'cartilage', 'meniscus')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=ZA + 'MuscularSystem100.fbx')
    musc = {o.name for o in bpy.data.objects if o.type == 'MESH'}
    bpy.ops.import_scene.fbx(filepath=ZA + 'SkeletalSystem100.fbx')
    bpy.context.view_layer.update()
    PARENTS = {o.name: reshape.chain(o) for o in bpy.data.objects if o.type == 'MESH'}
    # Keep every piece where it really is before the group holders are removed.
    for o in [o for o in bpy.data.objects if o.type == 'MESH']:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    DROP = {'Take a picture', 'Diaphragm', 'Platysma.l', 'Platysma.r'}
    def keep(o):
        if o.type != 'MESH' or o.name in DROP or o.name.startswith('Sinus'): return False
        if any(s in o.name.lower() for s in SKIP) and not o.name.startswith('Tensor fasciae latae'): return False
        # real left, right and middle pieces only; the others are labels and markers
        return '.' not in o.name or o.name.rsplit('.', 1)[1] in ('l', 'r')
    for o in list(bpy.data.objects):
        if not keep(o):
            bpy.data.objects.remove(o, do_unlink=True)
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    # Left and right pieces can share one mesh; give each its own before reshaping.
    for o in objs:
        if o.data.users > 1:
            o.data = o.data.copy()
    BUILD = os.environ.get('BUILD', 'classic')
    if BUILD == 'classic':
        reshape.grow(objs)
        reshape.pose_arms(objs, PARENTS, 30)
    # The head is a plain construction egg, no face: drop the skull and face
    # muscles and put a smooth egg where the skull was.
    def box(o):
        cs = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
        return mathutils.Vector([min(c[i] for c in cs) for i in range(3)]), mathutils.Vector([max(c[i] for c in cs) for i in range(3)])
    skull = [o for o in objs if any(k in o.name for k in ('Frontal bone', 'Occipital bone', 'Parietal bone', 'Mandible', 'Temporal bone', 'Zygomatic bone', 'Maxilla'))]
    mn = mathutils.Vector((1e9,) * 3); mx = mathutils.Vector((-1e9,) * 3)
    for o in skull:
        a, b = box(o); mn = mathutils.Vector(map(min, mn, a)); mx = mathutils.Vector(map(max, mx, b))
    print('skull', mn, mx)
    keep_neck = ('Sternocleidomastoid', 'trapezius', 'Splenius', 'Levator scapulae', 'Scalene', 'scalene', 'Omohyoid', 'Sternohyoid', 'Sternothyroid', 'Thyrohyoid')
    chin = mn.z
    for o in list(objs):
        a, b = box(o)
        c = (a + b) / 2
        if c.z > chin + 0.01 and not any(k in o.name for k in keep_neck):
            bpy.data.objects.remove(o, do_unlink=True)
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, radius=1)
    egg = bpy.context.active_object; egg.name = 'Head'
    size = mx - mn
    egg.scale = (size.x * 0.5 * 0.92, size.y * 0.5 * 0.95, size.z * 0.5 * 1.0)
    egg.location = ((mn.x + mx.x) / 2, (mn.y + mx.y) / 2 + 0.005, (mn.z + mx.z) / 2 + 0.005)
    bpy.ops.object.shade_smooth()
    objs.append(egg)
    print('kept', len(objs))
    return objs, musc
