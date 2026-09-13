from pathlib import Path
import bpy,math,json,traceback,hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/attachment-review'

def run():
 try:
  results={}
  for label,path in [('backed',OUT/'inputs/backed.usdz')]:
   expected={'backed':'c37f707c7423b468d0b7744912cad908808155794bd3d344e4ee04fc35b06582'}
   assert hashlib.sha256(path.read_bytes()).hexdigest()==expected[label]
   bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
   for m in list(bpy.data.materials):bpy.data.materials.remove(m)
   bpy.ops.wm.usd_import(filepath=str(path),import_materials=True,import_textures_mode='IMPORT_COPY',import_textures_dir=str(OUT/('imported_'+label)))
   s=bpy.context.scene
   meshes=[o for o in s.objects if o.type=='MESH'];bpy.context.view_layer.update()
   pts=[o.matrix_world @ Vector(v) for o in meshes for v in o.bound_box]
   bounds=[[min(p[k] for p in pts),max(p[k] for p in pts)] for k in range(3)]
   results[label]={'path':str(path),'sha256':expected[label],'meshes':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'polygons':sum(len(o.data.polygons) for o in meshes),'bounds':bounds,'dimensions':[b[1]-b[0] for b in bounds],'materials':{m.name:[{'name':n.name,'type':n.type,'image':n.image.filepath if n.type=='TEX_IMAGE' and n.image else None} for n in m.node_tree.nodes] for m in bpy.data.materials if m.use_nodes}}
   (OUT/'comparison-import-verification.json').write_text(json.dumps(results,indent=2))
   s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12;s.cycles.use_denoising=True
   s.render.threads_mode='FIXED';s.render.threads=2
   s.render.resolution_x=540;s.render.resolution_y=720;s.render.resolution_percentage=100
   s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
   world=bpy.data.worlds.new('Matched daylight');world.use_nodes=True;s.world=world
   w=world.node_tree;w.nodes.clear();bg=w.nodes.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.35
   sky=w.nodes.new('ShaderNodeTexSky');sky.sky_type='SINGLE_SCATTERING';sky.sun_elevation=math.radians(32);sky.sun_rotation=math.radians(125)
   wo=w.nodes.new('ShaderNodeOutputWorld');w.links.new(sky.outputs[0],bg.inputs[0]);w.links.new(bg.outputs[0],wo.inputs[0])
   # Ground only in verification scene, excluded from delivery.
   bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.005))
   mat=bpy.data.materials.new('Neutral verification ground');mat.diffuse_color=(.18,.18,.18,1);mat.use_nodes=True;mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.18,.18,.18,1);bpy.context.object.data.materials.append(mat)
   bpy.ops.object.camera_add();c=bpy.context.object;s.camera=c;c.data.type='PERSP';c.data.clip_start=.001;c.data.clip_end=100
   control=json.loads((OUT/'inputs/camera-control.json').read_text());cfg=control['camera']
   assert hashlib.sha256((OUT/'before_grazing.png').read_bytes()).hexdigest()==control['before_image_sha256']
   for view,location,target,lens in [('grazing',cfg['location'],cfg['target'],cfg['lens_mm'])]:
    s.render.resolution_x,s.render.resolution_y=cfg['resolution']
    results[label].setdefault('cameras',{})[view]={'location':list(location),'target':list(target),'lens_mm':lens,'resolution':cfg['resolution']}
    c.location=location;c.data.lens=lens;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(OUT/(label+'_'+view+'.png'));print('RENDER_BEGIN',label,view,flush=True);bpy.ops.render.render(write_still=True);print('RENDER_DONE',label,view,flush=True)
   (OUT/'comparison-import-verification.json').write_text(json.dumps(results,indent=2))
  assert all(abs(a-b)<1e-6 for a,b in zip(control['dimensions'],results['backed']['dimensions']))
  (OUT/'complete.json').write_text(json.dumps({'complete':True,'frames':1,'render_engine':'Cycles CPU','samples':12,'threads':2,'bounds_equal':True,'limitation':'Cycles can render both sides of surfaces; this does not prove RealityKit backface-culling behavior. Geometry not modified by this diagnostic; input candidate adds backing and sidewalls.'},indent=2))
  print('ATTACHMENT_REVIEW_COMPLETE',flush=True)
 except Exception:
  traceback.print_exc()
 finally:
  bpy.ops.wm.quit_blender()
 return None
bpy.app.timers.register(run,first_interval=2)
