"""Portable artistic PBR candidate; accepted geometry is immutable."""
from pathlib import Path
import bpy, numpy as np, json, hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'; TEX=OUT/'materials'; TEX.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/flatiron_accepted.blend'))
s=bpy.context.scene
s.render.threads_mode='FIXED';s.render.threads=2

def geometry():
 result={}
 for o in s.objects:
  if o.type!='MESH':continue
  h=hashlib.sha256()
  for v in o.data.vertices:h.update(np.asarray(v.co[:],dtype=np.float32).tobytes())
  for p in o.data.polygons:h.update(np.asarray(p.vertices[:],dtype=np.int32).tobytes())
  result[o.name]={'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'sha256':h.hexdigest(),'dimensions':list(o.dimensions)}
 return result
before=geometry()
N=512
rng=np.random.default_rng(271828)
y,x=np.mgrid[0:N,0:N]/N
# Periodic Fourier bands: soft mineral mottling, fine pores and subtle rain streaks.
def noise(freqs):
 v=np.zeros((N,N))
 for freq,amp in freqs:
  for i in range(12):
   kx=int(rng.integers(-freq,freq+1));ky=int(rng.integers(-freq,freq+1))
   v+=amp*np.sin(2*np.pi*(kx*x+ky*y)+rng.uniform(0,2*np.pi))/12
 return v
coarse=noise([(3,1),(9,.55),(27,.25)])
fine=noise([(70,1),(160,.4)])
streak=np.sin(2*np.pi*x*35+.2*np.sin(2*np.pi*y*2))*.3+noise([(12,.3)])
def save_image(name,data,color=False):
 if data.ndim==2:data=np.repeat(data[...,None],3,axis=2)
 rgba=np.concatenate((np.clip(data,0,1),np.ones((N,N,1))),axis=2).astype(np.float32)
 image=bpy.data.images.new(name,width=N,height=N,alpha=False,is_data=True)
 image.pixels.foreach_set(rgba.ravel());image.filepath_raw=str(TEX/(name+'.png'));image.file_format='PNG';image.save()
 bpy.data.images.remove(image)
 image=bpy.data.images.load(str(TEX/(name+'.png')),check_existing=False)
 image.colorspace_settings.name='sRGB' if color else 'Non-Color'
 return image

def stone(name,slug,base,roughness,grain):
 mat=bpy.data.materials[name];nodes=mat.node_tree.nodes;links=mat.node_tree.links
 bs=nodes.get('Principled BSDF')
 # Stored base color is sRGB. All scalar maps and tangent normals are data.
 pigment=(coarse*.045+fine*.009+streak*.006)*grain
 color=save_image(slug+'_basecolor',np.array(base)[None,None,:]+pigment[...,None],True)
 rough=save_image(slug+'_roughness',roughness+coarse*.12+fine*.045)
 height=(coarse*.15+fine*.018)*grain
 dy,dx=np.gradient(height)
 normal=np.stack((-dx*10,-dy*10,np.ones_like(dx)),axis=2)
 normal/=np.linalg.norm(normal,axis=2,keepdims=True)
 normal=save_image(slug+'_normal',normal*.5+.5)
 uv=nodes.new('ShaderNodeUVMap');uv.uv_map='st'
 for image,target in [(color,'Base Color'),(rough,'Roughness'),(normal,'Normal')]:
  tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.extension='REPEAT';links.new(uv.outputs['UV'],tex.inputs['Vector'])
  if target=='Normal':
   norm=nodes.new('ShaderNodeNormalMap');norm.uv_map='st';links.new(tex.outputs['Color'],norm.inputs['Color']);links.new(norm.outputs['Normal'],bs.inputs['Normal'])
  else:links.new(tex.outputs['Color'],bs.inputs[target])
 bs.inputs['Metallic'].default_value=0
 bs.inputs['Specular IOR Level'].default_value=.3
 bs.inputs['Roughness'].default_value=roughness
 mat['material_provenance']='Artist-authored seamless mineral texture, not a photographic sample; geometry unchanged.'
 return mat
stone('Warm limestone','limestone',(.730,.709,.665),.76,1)
stone('Pale terracotta relief','terracotta',(.810,.779,.721),.64,.7)
# The accepted closed shell has no interiors. Keep backed, reflective glazing;
# transmission would falsely reveal that shell rather than credible rooms.
glass=bpy.data.materials['Recessed blue charcoal glass'].node_tree.nodes.get('Principled BSDF')
glass.inputs['Base Color'].default_value=(.028,.044,.051,1)
glass.inputs['Metallic'].default_value=.08
glass.inputs['Roughness'].default_value=.16
glass.inputs['IOR'].default_value=1.5
glass.inputs['Coat Weight'].default_value=.35
glass.inputs['Coat Roughness'].default_value=.12
# Moderated mortar and less yellow oxidized frame metal.
for name,color,rough,metal in [('Mortar shadow',(.245,.232,.212,1),.85,0),('Bronze window frames',(.095,.084,.065,1),.40,.45)]:
 b=bpy.data.materials[name].node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=color;b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
# Face projection changes UVs only. A 4 m source-space repeat becomes 4/87 m on the tabletop.
for o in s.objects:
 if o.type!='MESH' or not any(m and m.name in ['Warm limestone','Pale terracotta relief'] for m in o.data.materials):continue
 uv=o.data.uv_layers.new(name='st')
 for poly in o.data.polygons:
  normal=poly.normal;axis=max(range(3),key=lambda k:abs(normal[k]))
  for li in poly.loop_indices:
   co=o.matrix_world @ o.data.vertices[o.data.loops[li].vertex_index].co
   if axis==2:u,v=co.x,co.y
   elif axis==0:u,v=co.y,co.z
   else:u,v=co.x,co.z
   if normal[axis]<0:u=-u
   uv.data[li].uv=(u/4,v/4)
after=geometry();assert before==after,'Geometry changed'
s['material_candidate']='Artist-authored portable PBR refinement; no photo calibration; accepted mesh preserved.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'flatiron_material_candidate.blend'))
bpy.ops.object.select_all(action='DESELECT')
meshes=[o for o in s.objects if o.type=='MESH' and o.name!='Asphalt']
root=bpy.data.objects.new('Flatiron_tabletop_1m',None);s.collection.objects.link(root)
for o in meshes:o.parent=root;o.select_set(True)
root.scale=(1/87,)*3;root.select_set(True);bpy.context.view_layer.update()
bpy.ops.wm.usd_export(filepath=str(OUT/'flatiron_tabletop_materials.usdz'),selected_objects_only=True,export_materials=True,generate_preview_surface=True,generate_materialx_network=False,export_uvmaps=True,rename_uvmaps=True,export_textures_mode='NEW',relative_paths=True,convert_world_material=False)
(OUT/'material-geometry-verification.json').write_text(json.dumps({'source':str(ROOT/'assets/flatiron_accepted.blend'),'before':before,'after':after,'geometry_identical':before==after,'texture_resolution':512,'texture_repeat_metres_source':4},indent=2))
print('MATERIAL_CANDIDATE_EXPORTED',flush=True)
