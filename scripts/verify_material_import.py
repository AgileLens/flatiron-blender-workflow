from pathlib import Path
import bpy,json
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';result={}
for label,path in [('baseline',ROOT/'docs/flatiron_tabletop.usdz'),('candidate',OUT/'flatiron_tabletop_materials.usdz')]:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.wm.usd_import(filepath=str(path),import_materials=True,import_textures_mode='IMPORT_COPY',import_textures_dir=str(OUT/('verify_'+label)))
 bpy.context.view_layer.update();meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];pts=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
 result[label]={'meshes':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'faces':sum(len(o.data.polygons) for o in meshes),'dimensions':[max(p[k] for p in pts)-min(p[k] for p in pts) for k in range(3)],'textures':[{'file':i.filepath,'size':list(i.size),'colorspace':i.colorspace_settings.name} for i in bpy.data.images if i.source=='FILE'],'uv_meshes':[o.name for o in meshes if len(o.data.uv_layers)>0]}
(OUT/'import-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
