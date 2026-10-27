"""Whole-model attachment audit: which pieces float off the building?

Run headless:
  Blender -b --factory-startup --python scripts/audit_attachment.py -- \
      --usdz docs/flatiron_tabletop_supported.usdz --scale 87 --out outputs/audit.json
  (or --blend path.blend --scale 1 to audit a source scene in metres)

Every loose part (connected vertex set) is one element. Two elements are in
contact when their triangles intersect (BVH overlap) or a vertex/face-centre of
one lies within --eps of the other. Elements that reach the ground through a
chain of contacts are supported; everything else floats. Its gap is the
distance from its nearest point to the nearest supported element (how far it
hovers off the building); the distance to any other floating cluster is
reported separately.
Distances are reported at full building scale (metres) and at tabletop scale.
This measures the delivered asset directly; it does not trust the generator.
"""
import bpy, sys, json, argparse, math, time
from collections import defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--usdz'); ap.add_argument('--blend')
ap.add_argument('--scale', type=float, default=87.0, help='multiply scene units to reach full-scale metres')
ap.add_argument('--tabletop-display-scale', type=float, default=0.887956,
                help='runtime scale applied to the 1/87 asset in the tabletop (build1 receipt)')
ap.add_argument('--eps', type=float, default=0.002, help='contact tolerance, full-scale metres')
ap.add_argument('--exclude', action='append', default=['Asphalt'])
ap.add_argument('--out', required=True)
a = ap.parse_args(argv)
t0 = time.time()

if a.blend:
    bpy.ops.wm.open_mainfile(filepath=a.blend)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.usd_import(filepath=a.usdz)
bpy.context.view_layer.update()

pts, tris, tri_comp = [], [], []
comp_obj, comp_tris = [], []
for o in bpy.context.scene.objects:
    if o.type != 'MESH' or any(x.lower() in o.name.lower() for x in a.exclude):
        continue
    m = o.data; m.calc_loop_triangles()
    mw = o.matrix_world
    base = len(pts)
    pts.extend([(mw @ v.co) * a.scale for v in m.vertices])
    # union-find over vertices joined by polygons -> loose parts
    parent = list(range(len(m.vertices)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for p in m.polygons:
        vs = p.vertices; r0 = find(vs[0])
        for v in vs[1:]:
            r = find(v)
            if r != r0: parent[r] = r0
    local = {}
    for lt in m.loop_triangles:
        root = find(lt.vertices[0])
        if root not in local:
            local[root] = len(comp_obj); comp_obj.append(o.name); comp_tris.append([])
        c = local[root]
        comp_tris[c].append(len(tris))
        tris.append(tuple(base + v for v in lt.vertices)); tri_comp.append(c)

N = len(comp_obj)
bvh = BVHTree.FromPolygons(pts, tris, all_triangles=True, epsilon=0.0)
print('AUDIT elements', N, 'triangles', len(tris), 'vertices', len(pts), flush=True)

# 1) intersecting triangles between different elements
adj = defaultdict(set)
for i, j in bvh.overlap(bvh):
    ci, cj = tri_comp[i], tri_comp[j]
    if ci != cj:
        adj[ci].add(cj); adj[cj].add(ci)
# 2) touching within eps (vertices and triangle centroids)
def samples(c):
    out = []
    for ti in comp_tris[c]:
        tv = [pts[k] for k in tris[ti]]
        out.extend(tv); out.append((tv[0] + tv[1] + tv[2]) / 3)
    return out
for c in range(N):
    seen = set()
    for q in samples(c):
        for co, nor, idx, dist in bvh.find_nearest_range(q, a.eps):
            oc = tri_comp[idx]
            if oc != c and oc not in seen:
                seen.add(oc); adj[c].add(oc); adj[oc].add(c)

# ground roots: anything reaching within eps of the lowest point of the model
zmin = min(p.z for p in pts)
roots = [c for c in range(N) if min(pts[k].z for ti in comp_tris[c] for k in tris[ti]) <= zmin + a.eps]
supported = set(roots); stack = list(roots)
while stack:
    c = stack.pop()
    for o in adj[c]:
        if o not in supported:
            supported.add(o); stack.append(o)
floating = [c for c in range(N) if c not in supported]
# group floating elements into clusters that touch each other
cluster = {}
for c in floating:
    if c in cluster: continue
    cid = len(set(cluster.values())); stack = [c]; cluster[c] = cid
    while stack:
        x = stack.pop()
        for o in adj[x]:
            if o not in supported and o not in cluster:
                cluster[o] = cid; stack.append(o)

members = defaultdict(set)
for k, v in cluster.items():
    members[v].add(k)
def gap_of(c, allowed):
    """Nearest distance from element c to any triangle whose element passes allowed()."""
    best = math.inf; best_to = None
    for q in samples(c):
        for radius in (0.5, 3.0, 12.0):
            hits = [(d, tri_comp[i]) for co, n, i, d in bvh.find_nearest_range(q, radius) if allowed(tri_comp[i])]
            if hits:
                d, oc = min(hits)
                if d < best: best, best_to = d, oc
                break
    return best, best_to

rows = []
for c in floating:
    # Primary metric: how far the element hovers off the supported building.
    g, to = gap_of(c, lambda oc: oc in supported)
    g_any, _ = gap_of(c, lambda oc: oc not in members[cluster[c]])
    vs = [pts[k] for ti in comp_tris[c] for k in tris[ti]]
    cen = sum(vs, Vector()) / len(vs)
    rows.append({'element': c, 'mesh': comp_obj[c], 'gap_m': g, 'nearest_supported_mesh': comp_obj[to] if to is not None else None,
                 'gap_to_any_other_cluster_m': g_any,
                 'center_m': [round(cen.x, 3), round(cen.y, 3), round(cen.z, 3)], 'triangles': len(comp_tris[c])})

def stats(v):
    v = sorted(v)
    if not v: return None
    pick = lambda f: v[min(len(v) - 1, int(f * (len(v) - 1) + .5))]
    return {'n': len(v), 'min': v[0], 'p50': pick(.5), 'p95': pick(.95), 'max': v[-1]}
per_mesh = {}
for name in sorted(set(comp_obj)):
    cs = [c for c in range(N) if comp_obj[c] == name]
    fl = [r['gap_m'] for r in rows if r['mesh'] == name]
    per_mesh[name] = {'elements': len(cs), 'floating': len(fl), 'gap_full_scale_m': stats(fl)}
to_table_mm = 1000.0 / 87.0 * a.tabletop_display_scale
gaps = [r['gap_m'] for r in rows]
visible = [g for g in gaps if g >= 0.01]
result = {
    'input': a.usdz or a.blend, 'scale_to_full_m': a.scale, 'contact_eps_m': a.eps,
    'elements': N, 'triangles': len(tris), 'vertices': len(pts),
    'ground_roots': len(roots), 'supported': len(supported), 'floating': len(floating),
    'floating_clusters': len(set(cluster.values())),
    'floating_gap_full_scale_m': stats(gaps),
    'floating_with_gap_ge_1cm': len(visible),
    'floating_gap_tabletop_mm': {k: (v * to_table_mm if isinstance(v, float) else v) for k, v in (stats(gaps) or {}).items()},
    'per_mesh': per_mesh,
    'largest_gaps': sorted(rows, key=lambda r: -r['gap_m'])[:25],
    'seconds': round(time.time() - t0, 1),
}
with open(a.out, 'w') as f:
    json.dump(result, f, indent=2)
print('AUDIT_DONE floating', len(floating), 'of', N, 'gap', result['floating_gap_full_scale_m'], flush=True)
