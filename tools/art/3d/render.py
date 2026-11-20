import bpy, sys, math, mathutils, colorsys, json, random, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get('OUT', '/home/claude/3d/work/')
RES = (int(os.environ.get('RES_W', 1300)), int(os.environ.get('RES_H', 2000)))
import scene
objs, musc = scene.build()
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
