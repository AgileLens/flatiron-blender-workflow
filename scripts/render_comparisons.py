import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/flatiron_showcase.blend'))
s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=2
s.cycles.samples=16
c=s.camera;c.data.type='PERSP';c.data.lens=36;c.location=(55,140,3);c.rotation_euler=(Vector((0,0,42))-c.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=720;s.render.resolution_y=900;s.render.filepath=str(ROOT/'outputs/match-overview.png')
bpy.ops.render.render(write_still=True)
c.data.lens=110;c.location=(55,-5,14);c.rotation_euler=(Vector((8,-5,14))-c.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.filepath=str(ROOT/'outputs/match-detail.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.quit_blender()
