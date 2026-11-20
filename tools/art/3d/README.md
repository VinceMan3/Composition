# The muscle map, made from a 3D model

The Map tab's figure comes from the Z-Anatomy 3D models (CC BY-SA 4.0,
https://github.com/LluisV/Z-Anatomy), reshaped and drawn in graphite here.
See CREDITS.md for the license note.

## Setup
- `pip install --break-system-packages bpy` (Blender 5.3 as a Python module).
  Run the Blender scripts with `python3 -I` (without it an import clash
  crashes). Keep scripts out of folders holding files named like standard
  Python modules (a file called `inspect.py` broke the FBX importer).
- The models only:
  `git clone --depth 1 --filter=blob:none --no-checkout https://github.com/LluisV/Z-Anatomy zanat`, then
  `git checkout HEAD -- "Resources/Models/FBX/MuscularSystem100.fbx" "Resources/Models/FBX/SkeletalSystem100.fbx" LICENSE`
  (never `git ls-tree -l` there: it downloads every file). Point `ZA` at the
  top of `render.py` to that folder.

## Steps (about 25 minutes on 2 CPUs)
For VIEW in front, back:
1. `RES_W=2240 RES_H=3440 VIEW=front OUT=final/front/ python3 -I render.py -- ids`
   then `-- deep` and `-- shade`.
   - ids: every model piece in its own flat color (ids.png, ids.json).
   - deep: the same with the sheets over the abs (both obliques, transversus),
     the trapezius and the IT band hidden, so the abs, rhomboids, outer quad
     and TFL get tap shapes too.
   - shade: lit clay, key light from the viewer's upper left (the lights turn
     with the camera for the back).
   `render.py` drops labels and markers (names ending `.j`, `.i`, `.ol`,
   `.e1l` ...), sheets of connective tissue (but keeps the tensor fasciae
   latae), keeps each piece's world position when the group holders go,
   gives left and right pieces their own mesh, then `reshape.py` fills out a
   Classic Physique build (muscle bellies pushed out along smoothed normals,
   wider lats, a smaller waist) and turns the arms 30 degrees out. The skull
   and face become a smooth egg.
2. `VIEW=front STYLE=soft OUT=final/front/ python3 npr.py`: graphite layers
   (tone with core shadows and creases, hatching along each muscle, edges
   dark in shadow and lost in the light, a hand wobble, paper tooth, head
   construction lines on the front).
3. `python3 build.py final/ <repo>`: maps every model muscle to one of the 46
   parts (the model's top and bottom trapezius names come out swapped),
   clips forearm parts at the wrist and lower-leg parts at the ankle, drops
   slivers mostly seen from the other side, traces the tap shapes, and writes
   `art/muscle-<view>-light.webp`, `-shade.webp`, `-ink.webp` and `-map.svg`.
   It prints which side each part shows on; `content/muscles.js` must match
   (a check enforces it).

`compare.py` and `cards.html` made the Nov 14 comparison sheets.

## Still to come
Frames for a smooth spin when turning around.

## The live 3D figure (work in progress, Nov 20)

- `scene.py` builds the figure (shared by `render.py` and `export.py`); `parts.py` maps model pieces to the 46 parts.
- `rig.py` finds a 54-bone skeleton from the model's own bones (sphere fits for the shoulders and hips, ends of the long bones, vertebra bodies, every finger joint).
- `skin.py` ties every point to the skeleton: Blender's bone heat on a watertight voxel shell (worked ten times bigger, or the heat solver fails), copied to each point from the nearest place on the shell, blurred through space so layered pieces move together, kept to its own side, the arm's pull fading fast away from the upper arm, and the hand split among the fingers. It also makes each muscle's squeeze (belly swells, draws toward its middle, fades out where parts meet) and the vacuum.
- `export.py` writes `figure.bin` (points, triangles, parts, pieces, fibers, creases, bone weights, squeezes) and `figure.json` (part names, pieces, head, bones). Run: `OUT=/path/ python3 -I export.py` (about 5 minutes).
- `live/`: the test page. `figure3d.js` draws the model in graphite (three.js, dual quaternion skinning in the shader), `skeleton.js` turns bones, `poser.js` turns plain joint angles into a pose and moves between poses with a squeeze, `poses.js` holds the poses and the Flex it moves. Serve the folder with `figure.bin`, `figure.json`, `three.module.js`, `three.core.js` and `paper.webp` next to it.
