import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def signature(path):
 bpy.ops.wm.open_mainfile(filepath=str(path))
 out={}
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   data={'v':[tuple(v.co) for v in o.data.vertices],'p':[tuple(p.vertices) for p in o.data.polygons],'m':[m.name for m in o.data.materials]}
   out[o.name]=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
 return out
a=signature(ROOT/'assets/flatiron_accepted.blend');b=signature(ROOT/'outputs/rebuild/flatiron_live_final.blend')
result={'geometry_and_material_assignment_match':a==b,'accepted':a,'rebuilt':b}
(ROOT/'outputs/rebuild-comparison.json').write_text(json.dumps(result,indent=2))
print('GEOMETRY_MATCH',a==b,flush=True)
def check_usdz():
 bpy.ops.object.select_all(action='SELECT')
 bpy.ops.object.delete(use_global=False)
 bpy.ops.wm.usd_import(filepath=str(ROOT/'outputs/flatiron_tabletop.usdz'))
 bpy.context.view_layer.update()
 from mathutils import Vector
 points=[o.matrix_world@Vector(c) for o in bpy.context.scene.objects if o.type=='MESH' for c in o.bound_box]
 print('USDZ_EXTENT',[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)],flush=True)
 bpy.ops.wm.quit_blender()
bpy.app.timers.register(check_usdz,first_interval=2.0)
