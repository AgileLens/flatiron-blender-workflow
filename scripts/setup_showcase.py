from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import bpy,math,json
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/flatiron_accepted.blend'))
s=bpy.context.scene
s.render.engine='CYCLES'
s.cycles.device='CPU'
s.cycles.samples=24
s.cycles.use_denoising=True
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
s.world.use_nodes=True
w=s.world.node_tree;w.nodes.clear()
bg=w.nodes.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.35
sky=w.nodes.new('ShaderNodeTexSky');sky.sky_type='SINGLE_SCATTERING';sky.sun_elevation=math.radians(18);sky.sun_rotation=math.radians(125)
out=w.nodes.new('ShaderNodeOutputWorld');w.links.new(sky.outputs[0],bg.inputs[0]);w.links.new(bg.outputs[0],out.inputs[0])
for name in ['Warm limestone','Pale terracotta relief']:
 m=bpy.data.materials.get(name);n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
 tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=8;tex.inputs['Detail'].default_value=3
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.035
 l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],bs.inputs['Normal'])
for name in ['Asphalt']:
 m=bpy.data.materials[name];m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.18,.19,.19,1)
c=s.camera;c.data.type='PERSP';c.data.lens=46
c.location=(125,215,104);target=Vector((0,0,40));c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(ROOT/'outputs/hero-test.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/flatiron_showcase.blend'))
bpy.ops.render.render(write_still=True)
