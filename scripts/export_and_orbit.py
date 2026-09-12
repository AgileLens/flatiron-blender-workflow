from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import bpy,math,time,json
from mathutils import Vector
s=bpy.context.scene
# Export a one-metre tabletop asset, preserving source dimensions in the .blend.
bpy.ops.object.select_all(action='DESELECT')
meshes=[o for o in s.objects if o.type=='MESH' and o.name!='Asphalt']
root=bpy.data.objects.new('Flatiron_tabletop_1m',None);s.collection.objects.link(root)
for o in meshes:o.parent=root;o.select_set(True)
root.scale=(1/87,)*3;root.select_set(True)
bpy.context.view_layer.update()
bpy.ops.wm.usd_export(filepath=str(ROOT/'outputs/flatiron_tabletop.usdz'),selected_objects_only=True,export_materials=True)
root.scale=(1,1,1)
for o in meshes:o.parent=None
bpy.data.objects.remove(root,do_unlink=True)
# The Cycles sky supplies sunlight; remove the Eevee test light.
for o in list(s.objects):
 if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True
s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
frames=ROOT/'outputs/orbit';frames.mkdir(exist_ok=True)
c=s.camera;c.data.type='PERSP';c.data.lens=46
for i in range(144):
 p=frames/f'{i:04d}.png'
 if p.exists():continue
 angle=math.radians(30+300*i/143)
 c.location=(245*math.sin(angle),245*math.cos(angle),100+12*math.sin(i/143*math.pi))
 c.rotation_euler=(Vector((0,0,40))-c.location).to_track_quat('-Z','Y').to_euler()
 s.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 if i%12==0:print('ORBIT_FRAME',i,flush=True)
print('ORBIT_COMPLETE',flush=True)
