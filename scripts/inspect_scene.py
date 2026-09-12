import bpy,json
from pathlib import Path
r=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(r/'assets/flatiron_accepted.blend'))
s=bpy.context.scene
info={'blender':bpy.app.version_string,'objects':[{'name':o.name,'type':o.type,'dimensions':list(o.dimensions),'location':list(o.location),'vertices':len(o.data.vertices) if o.type=='MESH' else 0} for o in s.objects]}
(r/'outputs/scene-info.json').write_text(json.dumps(info,indent=2))
print('FLATIRON_INSPECT_DONE',flush=True)
