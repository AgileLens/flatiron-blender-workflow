"""Render the build-4 model from each solved photo camera and overlay it on the photo.

  Blender -b --factory-startup --python scripts/render_photo_overlays.py -- \
      --blend outputs/build4/flatiron_v4.blend --cameras docs/build5/photo-cameras.json \
      --photos <dir> --out docs/build5
Camera convention matches solve_photo_cameras.py (q = R(X-C), right/down/forward; world rotation
of the Blender camera is R.T @ diag(1,-1,-1)), as in the materials-lab apply_photo_camera.py.
Also checks numerically that Blender projects each landmark where the solver did.
"""
import bpy, sys, os, json, argparse, math
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index('--') + 1:]
ap = argparse.ArgumentParser()
for k in ('--blend', '--cameras', '--photos', '--out'):
    ap.add_argument(k, required=True)
ap.add_argument('--only', default='')
a = ap.parse_args(argv)
bpy.ops.wm.open_mainfile(filepath=a.blend)
s = bpy.context.scene
for o in list(s.objects):
    if o.type in ('CAMERA', 'LIGHT') or o.name in ('Asphalt',):
        bpy.data.objects.remove(o, do_unlink=True)
cam = bpy.data.objects.new('PhotoCam', bpy.data.cameras.new('PhotoCam')); s.collection.objects.link(cam); s.camera = cam
# Validation look: stone is a holdout (occludes, renders transparent), glass glows magenta and
# frames yellow, so window rows and columns can be compared directly against the photo.
def emit(m, rgb=None):
    nt = m.node_tree; nt.nodes.clear(); out = nt.nodes.new('ShaderNodeOutputMaterial')
    if rgb is None:
        sh = nt.nodes.new('ShaderNodeHoldout')
    else:
        sh = nt.nodes.new('ShaderNodeEmission'); sh.inputs['Color'].default_value = (*rgb, 1); sh.inputs['Strength'].default_value = 1.0
    nt.links.new(sh.outputs[0], out.inputs['Surface'])
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    emit(m, (1.0, .05, .8) if 'glass' in m.name.lower() else (1.0, .85, .0) if 'frame' in m.name.lower() else None)
s.render.engine = 'CYCLES'; s.cycles.device = 'CPU'; s.cycles.samples = 2; s.cycles.use_denoising = False
s.render.film_transparent = True; s.view_settings.view_transform = 'Standard'
s.render.image_settings.file_format = 'PNG'; s.render.image_settings.color_mode = 'RGBA'
cams = json.load(open(a.cameras)); report = {}
for photo, c in cams.items():
    if a.only and photo not in a.only.split(','):
        continue
    W, H = c['size']; R = Matrix(c['R_world_to_camera_rdf']); f = c['focal_px']
    cam.matrix_world = (R.transposed() @ Matrix.Diagonal((1, -1, -1))).to_4x4(); cam.location = Vector(c['C'])
    cd = cam.data; cd.type = 'PERSP'; cd.sensor_fit = 'HORIZONTAL' if W >= H else 'VERTICAL'
    cd.sensor_width = cd.sensor_height = 36; cd.lens = f * 36 / (W if W >= H else H); cd.shift_x = cd.shift_y = 0
    cd.clip_start = .1; cd.clip_end = 5000
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = W, H, 100
    bpy.context.view_layer.update()
    worst = 0.0
    for p in c['points']:
        import photo_landmarks  # noqa: late import, needs scripts dir on sys.path
        X = Vector(photo_landmarks.landmark(p['name']))
        v = world_to_camera_view(s, cam, X)
        u_b, v_b = v.x * W, (1 - v.y) * H
        worst = max(worst, math.hypot(u_b - p['projected'][0], v_b - p['projected'][1]))
    out = os.path.join(a.out, 'render-' + photo.replace('.jpg', '.png'))
    s.render.filepath = out; bpy.ops.render.render(write_still=True)
    report[photo] = {'blender_vs_solver_max_px': worst, 'render': out}
    print('OVERLAY', photo, 'blender-vs-solver max', round(worst, 3), 'px', flush=True)
json.dump(report, open(os.path.join(a.out, 'blender-projection-check.json'), 'w'), indent=2)
