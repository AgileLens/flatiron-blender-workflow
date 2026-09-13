"""Post-replay repair for Flatiron's 1,062 raised annular strips.

Run after the final live step and winding correction. Front d=.44/.46,
support d=.35: add sidewalls and rear annulus at d=.348 (2 mm overlap).
The central opening is retained. No front vertex, face or normal is moved.
Only accepts the diagnosed generator topology, preventing double application.
"""
import numpy as np
from collections import Counter

def backed_ring_arrays(points, counts, indices, normals):
    points=np.asarray(points,dtype=np.float32); counts=np.asarray(counts,dtype=np.int32)
    indices=np.asarray(indices,dtype=np.int32); normals=np.asarray(normals,dtype=np.float32)
    assert points.shape==(33984,3) and counts.shape==(16992,) and np.all(counts==4)
    front=indices.reshape(-1,4); rear=points.copy(); added=[]; rows=[]
    for ci in range(1062):
        fs=front[ci*16:(ci+1)*16]; vids=np.arange(ci*32,(ci+1)*32)
        assert np.array_equal(np.unique(fs),vids)
        q=points[vids].astype(float); n=np.linalg.svd(q-q.mean(0),full_matrices=False)[2][-1]; n[2]=0; n/=np.linalg.norm(n)
        if n@normals[ci*64]<0:n=-n
        assert np.max(np.abs((points[vids].astype(float)-points[vids].astype(float).mean(0))@n))<1e-5
        depth=.092 if ci%2==0 else .112
        if ci%2:
            delta=points[vids].astype(float).mean(0)-points[vids-32].astype(float).mean(0)
            assert np.linalg.norm(delta-n*.02)<1e-5
        rear[vids]=points[vids]-depth*n
        edge_counts=Counter(tuple(sorted((int(a),int(b)))) for f in fs for a,b in zip(f,np.roll(f,-1)))
        back=[list(reversed(f+len(points))) for f in fs]
        sides=[[int(b),int(a),int(a)+len(points),int(b)+len(points)] for f in fs for a,b in zip(f,np.roll(f,-1)) if edge_counts[tuple(sorted((int(a),int(b))))]==1]
        assert len(sides)==32
        start=len(front)+len(added);added.extend(back+sides)
        rows.append({'component':ci,'depth_m':depth,'front_faces':list(range(ci*16,(ci+1)*16)),'back_faces':list(range(start,start+16)),'side_faces':list(range(start+16,start+48))})
    pts=np.concatenate((points,rear)); newfaces=np.asarray(added,dtype=np.int32)
    poly=pts[newfaces].astype(float); raw=np.cross(poly,np.roll(poly,-1,axis=1)).sum(1)
    face_normals=raw/np.linalg.norm(raw,axis=1)[:,None]
    return pts,np.full(len(front)+len(newfaces),4,dtype=np.int32),np.concatenate((front,newfaces)).ravel(),np.concatenate((normals,np.repeat(face_normals,4,axis=0).astype(np.float32))),rows

def apply_to_blender():
    import bpy
    obj=bpy.data.objects['Raised medallions']; old=obj.data
    points=np.array([v.co[:] for v in old.vertices],dtype=np.float32)
    counts=np.array([len(p.vertices) for p in old.polygons],dtype=np.int32)
    indices=np.array([i for p in old.polygons for i in p.vertices],dtype=np.int32)
    normals=np.array([p.normal[:] for p in old.polygons for _ in p.vertices],dtype=np.float32)
    pts,cnt,ind,norm,rows=backed_ring_arrays(points,counts,indices,normals)
    assert not old.uv_layers and all(p.material_index==0 for p in old.polygons)
    mesh=bpy.data.meshes.new('Raised medallions backed'); mesh.from_pydata(pts.tolist(),[],ind.reshape(-1,4).tolist())
    for mat in old.materials:mesh.materials.append(mat)
    mesh.update();obj.data=mesh
    return pts,cnt,ind,norm,rows
