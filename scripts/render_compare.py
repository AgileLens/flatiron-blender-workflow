"""Render matched review views of a Flatiron scene (source .blend or imported USDZ).

Views are placed from the model itself (ray hits on the west/Fifth Avenue facade and the
bounding box), so the before and after scenes get comparable framing even though the
footprints differ.
  Blender -b --factory-startup --python scripts/render_compare.py -- --blend X.blend --out DIR --tag after
"""
import bpy, sys, os, math, argparse
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
ap = argparse.ArgumentParser()
ap.add_argument('--blend'); ap.add_argument('--usdz'); ap.add_argument('--out', required=True); ap.add_argument('--tag', required=True)
ap.add_argument('--scale', type=float, default=1.0, help='USDZ scene-unit multiplier to full scale')
ap.add_argument('--engine', default='WORKBENCH', choices=['WORKBENCH', 'CYCLES'])
ap.add_argument('--views', default='overview,oblique,base,top,grazing')
ap.add_argument('--samples', type=int, default=24)
a = ap.parse_args(argv)
if a.blend:
    bpy.ops.wm.open_mainfile(filepath=a.blend)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.usd_import(filepath=a.usdz)
    for o in bpy.context.scene.objects:
        if o.parent is None:
            o.scale = [v * a.scale for v in o.scale]
s = bpy.context.scene
for o in list(s.objects):
    if o.type in ('CAMERA', 'LIGHT'):
        bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.update()
meshes = [o for o in s.objects if o.type == 'MESH' and 'asphalt' not in o.name.lower() and 'sidewalk' not in o.name.lower()]
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
C = (lo + hi) / 2; H = hi.z - lo.z
dg = bpy.context.evaluated_depsgraph_get()

def facade_hit(z, direction=Vector((-1, 0, 0)), y=None):
    origin = Vector((C.x, C.y if y is None else y, z)) + direction * 400
    ok, loc, nor, *_ = s.ray_cast(dg, origin, -direction)
    assert ok, 'facade ray missed'
    return loc, Vector((nor.x, nor.y, 0)).normalized()

cam_data = bpy.data.cameras.new('ReviewCam'); cam = bpy.data.objects.new('ReviewCam', cam_data)
s.collection.objects.link(cam); s.camera = cam
def look(pos, target, lens):
    cam.location = pos; cam.rotation_euler = (target - pos).to_track_quat('-Z', 'Y').to_euler(); cam_data.lens = lens
    cam_data.clip_start = .05; cam_data.clip_end = 2000

views = {}
views['overview'] = lambda: look(C + Vector((55, 150, 20 - C.z + 25)), C + Vector((0, 0, -4)), 42)
views['oblique'] = lambda: look(C + Vector((-120, 95, 70 - C.z + 20)), C + Vector((0, 4, 0)), 50)
def base():
    h, n = facade_hit(16.5); t = Vector((-n.y, n.x, 0))
    look(h + n * 13 + t * 5 + Vector((0, 0, 1.5)), h + t * 1.5 + Vector((0, 0, .5)), 40)
def top():
    h, n = facade_hit(72.0); t = Vector((-n.y, n.x, 0))
    look(h + n * 20 + t * 4 + Vector((0, 0, -9)), h + t * 1 + Vector((0, 0, 3.5)), 40)
def grazing():
    h, n = facade_hit(41.0); t = Vector((-n.y, n.x, 0))
    look(h + n * 1.6 + t * 6.5 + Vector((0, 0, .6)), h - t * 2.5 + n * .2, 32)
def street():
    # roughly the viewpoint of input photo 02: north-north-east of the prow at eye height
    prow = max((o.matrix_world @ v.co for o in meshes for v in o.data.vertices), key=lambda p: p.y)
    look(Vector((prow.x + 26, prow.y + 62, 1.7)), Vector((prow.x + 3, prow.y - 20, 42)), 22)
def prow_view(z, dist, lens):
    prow = max((o.matrix_world @ v.co for o in meshes for v in o.data.vertices), key=lambda p: p.y)
    look(Vector((prow.x + dist * .35, prow.y + dist, z - dist * .15)), Vector((prow.x, prow.y, z)), lens)
views.update(base=base, top=top, grazing=grazing, street=street,
             prow_low=lambda: prow_view(8.0, 22, 35), prow_top=lambda: prow_view(74.0, 26, 35))

s.render.engine = a.engine if a.engine != 'WORKBENCH' else 'BLENDER_WORKBENCH'
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1280, 960, 100
s.render.image_settings.file_format = 'PNG'
if a.engine == 'WORKBENCH':
    sh = s.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_shadows = True
    sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.curvature_ridge_factor = 1.2; sh.curvature_valley_factor = 1.0
    sh.background_type = 'WORLD'
    if s.world is None:
        s.world = bpy.data.worlds.new('bg')
    s.world.color = (.22, .25, .29)
else:
    s.cycles.device = 'CPU'; s.cycles.samples = a.samples; s.cycles.use_denoising = True
    s.view_settings.view_transform = 'AgX'
    sun_d = bpy.data.lights.new('Sun', 'SUN'); sun_d.energy = 3.2; sun_d.angle = .1
    sun = bpy.data.objects.new('Sun', sun_d); s.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(48), math.radians(-22), math.radians(-120))
os.makedirs(a.out, exist_ok=True)
for name in a.views.split(','):
    views[name]()
    s.render.filepath = os.path.join(a.out, f'{a.tag}_{name}.png')
    bpy.ops.render.render(write_still=True)
    print('RENDERED', s.render.filepath, flush=True)
