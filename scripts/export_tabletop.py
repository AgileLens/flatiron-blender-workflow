"""Export a Flatiron scene to the native tabletop USDZ (same convention as export_and_orbit.py).

The native app undoes exactly this 1/87 root scale for full-scale walkaround, so keep it.
  Blender -b --factory-startup --python scripts/export_tabletop.py -- --blend in.blend --usdz out.usdz
"""
import bpy, sys, argparse
argv = sys.argv[sys.argv.index('--') + 1:]
ap = argparse.ArgumentParser(); ap.add_argument('--blend', required=True); ap.add_argument('--usdz', required=True)
a = ap.parse_args(argv)
bpy.ops.wm.open_mainfile(filepath=a.blend)
s = bpy.context.scene
bpy.ops.object.select_all(action='DESELECT')
meshes = [o for o in s.objects if o.type == 'MESH' and o.name != 'Asphalt']
root = bpy.data.objects.new('Flatiron_tabletop_1m', None); s.collection.objects.link(root)
for o in meshes:
    o.parent = root; o.select_set(True)
root.scale = (1 / 87,) * 3; root.select_set(True)
bpy.context.view_layer.update()
bpy.ops.wm.usd_export(filepath=a.usdz, selected_objects_only=True, export_materials=True)
print('EXPORTED', a.usdz, len(meshes), 'meshes', flush=True)
