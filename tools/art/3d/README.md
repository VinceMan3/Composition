# Muscle map from a 3D model (test, Nov 14)

Plan B for the muscle map art: render the Z-Anatomy muscle and skeleton
models (CC BY-SA 4.0, https://github.com/LluisV/Z-Anatomy) in Blender, then
turn the renders into a graphite drawing.

Setup:
- `pip install --break-system-packages bpy` (Blender 5.3 as a Python module).
  Run Blender scripts with `python3 -I` (without it, an import clash crashes).
  Keep scripts out of folders with files named like standard modules
  (a file called `inspect.py` broke the FBX importer).
- Clone the model files only:
  `git clone --depth 1 --filter=blob:none --no-checkout https://github.com/LluisV/Z-Anatomy zanat`
  then `git checkout HEAD -- "Resources/Models/FBX/MuscularSystem100.fbx" "Resources/Models/FBX/SkeletalSystem100.fbx" LICENSE`
  (do not run `git ls-tree -l` there: it downloads every file).

Steps (paths at the top of each script):
1. `python3 -I render.py -- ids` renders each piece in its own flat color
   (ids.png, ids.json); `python3 -I render.py -- shade` renders the lit clay
   (shade.png). Pieces whose names end in `.j`, `.i`, `.ol`, `.e1l` and so on
   are labels and markers and are dropped; group holders carry rotation and
   scale, so each piece keeps its world position before they are removed.
   The skull and face are replaced with a smooth egg.
2. `python3 npr.py` (or `STYLE=soft python3 npr.py`) makes the graphite
   layers: tone, parallel hatching along each piece, edges dark in shadow
   and lost in the light, a slight hand wobble, paper grain.
3. `compare.py` puts the current drawing and both styles side by side with
   the chest picked; `cards.html` is the three card directions.

Still to do if Vince picks this: Classic Physique build (reshape in
Blender), arms 30 degrees out (pose the arms), construction lines on the
head, the back view, a second ID pass with the oblique's sheet hidden so the
abs get their own region, regions mapped to the 46 parts, then the same
layers the app uses now (tools/art/mapimages.py), and frames for a smooth
spin.
