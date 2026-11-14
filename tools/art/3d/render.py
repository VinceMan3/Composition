import bpy, sys, math, mathutils, colorsys, json, random, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reshape
ZA = '/home/claude/3d/zanat/Resources/Models/FBX/'
OUT = os.environ.get('OUT', '/home/claude/3d/work/')
RES = (int(os.environ.get('RES_W', 1300)), int(os.environ.get('RES_H', 2000)))
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
sc = bpy.context.scene
cam_data = bpy.data.cameras.new('cam'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = 1.98
cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, -5, 0.85); cam.rotation_euler = (math.radians(90), 0, 0)
VIEW = os.environ.get('VIEW', 'front')
if VIEW == 'back':
    cam.location = (0, 5, 0.85); cam.rotation_euler = (math.radians(90), 0, math.radians(180))
sc.render.resolution_x, sc.render.resolution_y = RES
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.render.image_settings.file_format = 'PNG'
which = sys.argv[-1]
if which == 'shade':
    mat = bpy.data.materials.new('clay'); mat.use_nodes = True
    b = mat.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1); b.inputs['Roughness'].default_value = 0.9
    for o in objs:
        o.data.materials.clear(); o.data.materials.append(mat)
    # a soft key light from the upper left, a weak fill from the right
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.6; sun.angle = math.radians(16)
    so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(55), math.radians(-38), math.radians(-40))
    fill = bpy.data.lights.new('fill', 'SUN'); fill.energy = 0.35; fill.angle = math.radians(40)
    fo = bpy.data.objects.new('fill', fill); sc.collection.objects.link(fo)
    fo.rotation_euler = (math.radians(75), math.radians(30), math.radians(35))
    if VIEW == 'back':
        # turn the lights with the camera, so the light still comes from the viewer's upper left
        so.rotation_euler.z += math.pi; fo.rotation_euler.z += math.pi
    world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 1, 1, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.38
    sc.cycles.samples = 24; sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    sc.render.filepath = OUT + 'shade.png'
else:
    # flat ids: every object its own color, no blending at edges.
    # 'deep' hides the sheets that lie over parts we still want to tap.
    if which == 'deep':
        SEE_THROUGH = ('External abdominal oblique muscle', 'Internal abdominal oblique muscle', 'Transversus abdominis',
                       'part of trapezius muscle', 'Iliotibial tract')
        for o in objs:
            if any(k in o.name for k in SEE_THROUGH):
                o.hide_render = True
    sc.cycles.samples = 1; sc.cycles.use_denoising = False
    sc.cycles.pixel_filter_type = 'BOX'; sc.cycles.filter_width = 0.01
    sc.view_settings.view_transform = 'Raw'; sc.render.dither_intensity = 0
    sc.render.film_transparent = True
    ids = {}
    random.seed(3)
    for i, o in enumerate(objs, start=1):
        r, g, b = (i >> 16) & 255, (i >> 8) & 255, i & 255
        m = bpy.data.materials.new(f'id{i}'); m.use_nodes = True
        nt = m.node_tree; nt.nodes.clear()
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (r / 255, g / 255, b / 255, 1); em.inputs['Strength'].default_value = 1
        outn = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0], outn.inputs[0])
        o.data.materials.clear(); o.data.materials.append(m)
        ids[i] = [o.name, o.name in musc]
    json.dump(ids, open(OUT + 'ids.json', 'w'))
    sc.render.filepath = OUT + ('ids_deep.png' if which == 'deep' else 'ids.png')
bpy.ops.render.render(write_still=True)
print('done', which)
