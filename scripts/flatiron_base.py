"""Initial procedural geometry used by the successful live MCP replay."""
import bpy, math, os, sys, argparse, random
from mathutils import Vector
from collections import defaultdict
p=argparse.ArgumentParser();p.add_argument('--revision',type=int,default=2);args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
REV=args.revision
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
random.seed(7)
def mat(name,color,rough=.6,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
 return m
mats=[mat('Warm limestone',(.60,.55,.44)),mat('Pale terracotta relief',(.73,.67,.55)),mat('Recessed blue charcoal glass',(.075,.13,.16),.24,.3),mat('Bronze window frames',(.14,.115,.08),.42,.35),mat('Mortar shadow',(.31,.285,.23)),mat('Roof zinc',(.24,.27,.27),.7),mat('Sidewalk',(.43,.44,.42)),mat('Asphalt',(.115,.135,.15))]
verts=defaultdict(list);faces=defaultdict(list)
def poly(v,f,ma):
 k=len(verts[ma]);verts[ma].extend(v);faces[ma].extend([tuple(k+i for i in face) for face in f])
def box(c,dim,ma=0,t=(1,0),n=(0,1)):
 x,y,z=c;w,d,h=dim
 v=[(x+t[0]*a+n[0]*b,y+t[1]*a+n[1]*b,z+cc) for a,b,cc in [(-w/2,-d/2,-h/2),(w/2,-d/2,-h/2),(w/2,d/2,-h/2),(-w/2,d/2,-h/2),(-w/2,-d/2,h/2),(w/2,-d/2,h/2),(w/2,d/2,h/2),(-w/2,d/2,h/2)]]
 poly(v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],ma)
# Fillet the triangular footprint; dimensions are artistic assumptions in metres.
corners=[Vector((-16,-40)),Vector((16,-40)),Vector((0,40))];path=[];path_normals=[];segments=[]
for i,c in enumerate(corners):
 a=(corners[i-1]-c).normalized();b=(corners[(i+1)%3]-c).normalized();ang=a.angle(b);r=2.5
 center=c+(a+b).normalized()*r/math.sin(ang/2);start=c+a*r/math.tan(ang/2);end=c+b*r/math.tan(ang/2)
 sa=math.atan2(start.y-center.y,start.x-center.x);ea=math.atan2(end.y-center.y,end.x-center.x)
 while ea<sa:ea+=2*math.pi
 arc=[center+Vector((math.cos(sa+(ea-sa)*j/16),math.sin(sa+(ea-sa)*j/16)))*r for j in range(17)]
 path.extend(arc);path_normals.extend([(q-center).normalized() for q in arc]);segments.append((start,end,center,sa,ea))
def ring(z,h,offset,ma=1):
 # Arc normals remain correct at the transition to each long straight side.
 pp=[]
 for i,q in enumerate(path):
  n=path_normals[i];pp.append(q+n*offset)
 v=[(q.x,q.y,zz) for zz in (z,z+h) for q in pp];N=len(pp)
 f=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
 poly(v,f,ma)
ring(0,84.6,-.12,0)
# Flat sides evenly spaced, curved corners subdivided by their arc length.
bays=[]
for i,seg in enumerate(segments):
 start=seg[1];end=segments[(i+1)%3][0];t=(end-start).normalized();n=Vector((t.y,-t.x));L=(end-start).length;count=round(L/3.05)
 for j in range(count):bays.append((start+t*L*(j+.5)/count,t,n,L/count))
 a,b,c,sa,ea=seg;count=max(1,round((ea-sa)*2.5/2.4))
 for j in range(count):
  theta=sa+(ea-sa)*(j+.5)/count;n=Vector((math.cos(theta),math.sin(theta)));t=Vector((-n.y,n.x));bays.append((c+n*2.5,t,n,(ea-sa)*2.5/count))
levels=[0,5,9,13,17]+[17+3.6*i for i in range(1,15)]+[71.2,74.4,81.4,84.6]
def local(q,t,n,x,d,z):return(q.x+t.x*x+n.x*d,q.y+t.y*x+n.y*d,z)
def arch(q,t,n,w,z,h):
 # Solid stone arch ring outside a dark glazed arched opening.
 spring=z+h-w/2
 for k in range(18):
  a=k*math.pi/18;b=(k+1)*math.pi/18
  vs=[]
  for d in (.025,.24):
   for rr,an in [(w/2,a),(w/2,b),(w/2+.22,b),(w/2+.22,a)]:vs.append(local(q,t,n,rr*math.cos(an),d,spring+rr*math.sin(an)))
  poly(vs,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7)],1)
 # arch glass fan
 vs=[local(q,t,n,0,.012,spring)]+[local(q,t,n,w/2*math.cos(k*math.pi/24),.012,spring+w/2*math.sin(k*math.pi/24)) for k in range(25)]
 poly(vs,[tuple(range(26))],2)
def medallion(q,t,n,x,z,r=.29):
 for rr,thick,d in [(r,.055,.28),(r*.76,.035,.30)]:
  vs=[]
  for rad in (rr-thick,rr):
   for k in range(16):vs.append(local(q,t,n,x+rad*math.cos(k*math.tau/16),d,z+rad*math.sin(k*math.tau/16)))
  poly(vs,[(k,(k+1)%16,(k+1)%16+16,k+16) for k in range(16)],1)
for idx,(q,t,n,bw) in enumerate(bays):
 for fl,(lo,hi) in enumerate(zip(levels,levels[1:])):
  crown=fl==20;base=fl<4;arched=fl in (18,20)
  w=bw*(.69 if base else .52);bot=lo+(.45 if fl==0 else .65);h=hi-bot-.48
  if crown:w=bw*.73
  gh=h-w/2 if arched else h
  box(local(q,t,n,0,.015,bot+gh/2),(w,.10,gh),2,t,n)
  if arched:arch(q,t,n,w,bot,h)
  for x in (-w/2,w/2):box(local(q,t,n,x,.12,bot+gh/2),(.105,.22,gh+.12),3,t,n)
  for z in (bot,bot+gh*.5,bot+gh):box(local(q,t,n,0,.13,z),(w,.21,.095),3,t,n)
  if base or crown:box(local(q,t,n,0,.14,bot+gh/2),(.07,.22,gh),3,t,n)
  for z in (bot-.10,bot+h+.12):
   if not (arched and z>bot):box(local(q,t,n,0,.22,z),(w+.32,.44,.16),1,t,n)
  if base:
   for zstep in range(int((hi-lo)/.48)):
    box(local(q,t,n,bw/2,.14,lo+.24+zstep*.48),(bw-w-.13,.35,.41),0,t,n)
  if REV>=2:
   # Shaft course joints and alternately enriched vertical strips.
   if 4<=fl<=17:
    for j in range(6):box(local(q,t,n,bw/2,.025,lo+.28+j*.54),(bw-w-.09,.035,.025),4,t,n)
    if idx%3==0:
     for j in range(5):
      zz=lo+.45+j*.62
      box(local(q,t,n,bw/2,.12,zz),(.49,.18,.43),1,t,n)
      box(local(q,t,n,bw/2,.22,zz),(.27,.05,.22),0,t,n)
   if fl in (3,19,20):
    box(local(q,t,n,bw/2,.15,(lo+hi)/2),(bw-w-.14,.25,hi-lo-.4),1,t,n)
    medallion(q,t,n,bw/2,(lo+hi)/2,min(.40,(bw-w)*.38))
    for zz in (lo+.45,hi-.4):medallion(q,t,n,bw/2,zz,.19)
 for z in levels[1:]:
  if REV>=2 and z in (17,74.4,81.4):medallion(q,t,n,0,z+.22,.22)
# Continuous floor bands, base entablature, and layered overhanging cornice.
for z in levels[1:]:ring(z-.2,.22,.20,1)
for z in (5,13,17,67.4,71.2,74.4,81.4):
 ring(z-.36,.16,.28);ring(z-.20,.20,.42);ring(z,.14,.30)
for z,h,o in [(84.3,.25,.28),(84.55,.26,.45),(84.81,.30,.70),(85.11,.58,.91),(85.69,.22,1.28),(85.91,.23,1.42),(86.14,.20,1.2),(86.34,.5,.64),(86.84,.16,.8)]:ring(z,h,o)
if REV>=2:
 for i,seg in enumerate(segments):
  st=seg[1];en=segments[(i+1)%3][0];t=(en-st).normalized();n=Vector((t.y,-t.x));L=(en-st).length
  for j in range(round(L/.8)):
   q=st+t*(j+.5)*L/round(L/.8)
   box(local(q,t,n,0,.57,85.2),(.35,1.0,.52),1,t,n)
  for j in range(round(L/.25)):
   q=st+t*(j+.5)*L/round(L/.25)
   box(local(q,t,n,0,.34,84.48),(.12,.32,.22),1,t,n)
ring(86.9,.04,-.35,5)
# Roof recess and modest service penthouse.
box((0,-18,87.4),(8,14,1.0),5)
# Entry portal on broad portion of a long face.
q,t,n,bw=bays[11]
for x in (-1.3,1.3):box(local(q,t,n,x,.6,2.2),(.42,.9,4.4),1,t,n)
box(local(q,t,n,0,.62,4.5),(3.3,1.1,.38),1,t,n)
# presentation ground, curb and sidewalk
ring(-.28,.28,2.1,6)
box((0,0,-.45),(260,260,.32),7)
for ma in verts:
 mesh=bpy.data.meshes.new(mats[ma].name);mesh.from_pydata(verts[ma],[],faces[ma]);mesh.update();ob=bpy.data.objects.new(mats[ma].name,mesh);bpy.context.collection.objects.link(ob);ob.data.materials.append(mats[ma])
# Lighting and camera
world=bpy.data.worlds.new('Soft blue sky');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.68,.85,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;bpy.context.scene.world=world
bpy.ops.object.light_add(type='SUN',location=(30,50,100));sun=bpy.context.object;sun.rotation_euler=(math.radians(27),math.radians(-25),math.radians(-28));sun.data.energy=2.5;sun.data.angle=.12
bpy.ops.object.camera_add();cam=bpy.context.object;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.unit_settings.system='METRIC'
scene['reconstruction_status']='Uncalibrated AI-guided visual approximation; no photogrammetry or measured camera calibration.'
scene['dimension_provenance']='Nominal 87 m height and 80 x 32 m pre-fillet triangle: inherited rough prior-knowledge estimates, not photo measurements. All detail dimensions guessed.'
scene['validation_status']='Script revised from supplied photos; render comparison still required.'
scene.render.resolution_x=960;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
views=[('prow',(112,158,94),(0,0,43),57),('side',(-130,92,74),(0,-2,43),53)]
if REV>=2:views.append(('detail',(55,63,86),(1,17,74),64))
for name,pos,target,lens in views:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
 scene.render.filepath=os.path.join(OUT,f'flatiron_v{REV}_{name}.png')
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,f'flatiron_v{REV}.blend'))
 bpy.ops.render.render(write_still=True)
# Reopen the delivered scene at the overall view, rather than the last close-up.
name,pos,target,lens=views[0]
cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
scene.render.filepath=os.path.join(OUT,f'flatiron_v{REV}_prow.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,f'flatiron_v{REV}.blend'))
print('COMPLETED',REV,'bays',len(bays),'floors',len(levels)-1,'faces',sum(map(len,faces.values())))
