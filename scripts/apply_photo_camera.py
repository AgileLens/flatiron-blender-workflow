"""Convert fit_photo.py right/down/forward camera parameters to Blender.

Run in Blender, with --prepare (headless safe) or --render (foreground GUI).
The source copy, guides, archived fit and exact reference photo are immutable.
"""
from pathlib import Path
import sys,json,math,hashlib,traceback
import bpy,numpy as np
from mathutils import Vector,Matrix,Quaternion
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path('/Users/alex/Archives/flatiron-real-camera-20260912-01a090f8')
OUT=ROOT/'outputs/photo-camera'

def apply_fit_camera(scene,camera,parameters,image_size,sensor_width_mm=36):
    """p = [rotation-vector(3), world camera center(3), ln(f_px), cx, cy].

    fit_photo.py uses q = R*(X-C), with q axes right/down/forward.
    Blender local camera axes are right/up/backward. Thus its world rotation
    is R.T @ diag(1,-1,-1). Pixel origin is upper-left in the fit.
    """
    p=np.asarray(parameters,dtype=np.float64);W,H=image_size
    angle=float(np.linalg.norm(p[:3]));axis=Vector(p[:3]/angle) if angle else Vector((1,0,0))
    R=Quaternion(axis,angle).to_matrix()
    world_rotation=R.transposed() @ Matrix.Diagonal((1,-1,-1))
    camera.matrix_world=world_rotation.to_4x4();camera.location=Vector(p[3:6])
    camera.data.type='PERSP';camera.data.sensor_fit='HORIZONTAL';camera.data.sensor_width=sensor_width_mm
    camera.data.lens=math.exp(p[6])*sensor_width_mm/W
    camera.data.shift_x=(W/2-p[7])/W
    camera.data.shift_y=(p[8]-H/2)/W
    camera.data.clip_start=.001;camera.data.clip_end=10000
    scene.camera=camera;scene.render.resolution_x=W;scene.render.resolution_y=H
    scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=1;scene.render.pixel_aspect_y=1
    bpy.context.view_layer.update()
    return {'lens_mm':camera.data.lens,'sensor_width_mm':sensor_width_mm,'sensor_fit':'HORIZONTAL','shift_xy':[camera.data.shift_x,camera.data.shift_y],'matrix_world':[list(r) for r in camera.matrix_world]}

def geometry_signature(scene):
    result={}
    for o in scene.objects:
        if o.type!='MESH':continue
        h=hashlib.sha256()
        for v in o.data.vertices:h.update(np.asarray(v.co[:],dtype=np.float32).tobytes())
        for p in o.data.polygons:h.update(np.asarray(p.vertices[:],dtype=np.int32).tobytes())
        h.update(np.asarray(o.matrix_world,dtype=np.float32).tobytes())
        result[o.name]={'sha256':h.hexdigest(),'vertices':len(o.data.vertices),'polygons':len(o.data.polygons)}
    return result

def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    fit=json.loads((ARCHIVE/'results.json').read_text());guides=json.loads((ARCHIVE/'guides.json').read_text())
    assert hashlib.sha256((ARCHIVE/'flatiron_02.jpg').read_bytes()).hexdigest()==guides['image_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'showcase_control.blend'))
    scene=bpy.context.scene;signature=geometry_signature(scene);W,H=guides['image_size']
    report={'source':str(OUT/'showcase_control.blend'),'source_sha256':hashlib.sha256((OUT/'showcase_control.blend').read_bytes()).hexdigest(),'fit_sha256':hashlib.sha256((ARCHIVE/'results.json').read_bytes()).hexdigest(),'image_sha256':guides['image_sha256'],'image_size':[W,H],'projection_convention':'CV R world-to-camera right/down/forward; Blender world rotation R.T @ diag(1,-1,-1)','geometry_before':signature,'cameras':{}}
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.image_settings.file_format='PNG'
    for label,key in [('before','presentation_baseline'),('after','centered')]:
        entry=fit['results'][key];camera_info=apply_fit_camera(scene,scene.camera,entry['parameters'],[W,H])
        projected=[];depth=[]
        for g in guides['guides']:
            q=world_to_camera_view(scene,scene.camera,Vector(g['xyz']))
            projected.append([q.x*W,(1-q.y)*H]);depth.append(q.z)
        error=np.linalg.norm(np.asarray(projected)-np.asarray(entry['predicted']),axis=1)
        assert min(depth)>0,'Guide behind camera'
        assert float(error.max())<.01,('Projection conversion failed',label,float(error.max()))
        report['cameras'][label]={'fit_key':key,**camera_info,'projected':projected,'fit_projection_delta_px':error.tolist(),'max_projection_delta_px':float(error.max()),'train_photo_rmse_px':entry['train_rmse'],'held_out_photo_rmse_px':entry['test_rmse']}
        scene.render.filepath=str(OUT/(label+'.png'))
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(label+'.blend')))
    report['geometry_after']=geometry_signature(scene);report['geometry_identical']=report['geometry_before']==report['geometry_after']
    assert report['geometry_identical']
    (OUT/'projection-verification.json').write_text(json.dumps(report,indent=2))
    print('PROJECTION_VERIFIED',json.dumps({k:v['max_projection_delta_px'] for k,v in report['cameras'].items()}),flush=True)

def render_next():
    # open_mainfile can invalidate a timer's GUI context; defer render to a fresh timer.
    if not pending:
        (OUT/'render-complete.json').write_text(json.dumps({'complete':True,'render_pair':['before.png','after.png'],'engine':'Cycles CPU','threads':2,'samples':8,'image_size':[1608,1577]},indent=2))
        print('CAMERA_RENDER_PAIR_COMPLETE',flush=True);bpy.ops.wm.quit_blender();return None
    label=pending.pop(0)
    bpy.ops.wm.open_mainfile(filepath=str(OUT/(label+'.blend')))
    def render_loaded():
        try:
            print('CAMERA_RENDER_BEGIN',label,flush=True);bpy.ops.render.render(write_still=True);print('CAMERA_RENDER_DONE',label,flush=True)
            bpy.app.timers.register(render_next,first_interval=.5)
        except Exception:traceback.print_exc();bpy.ops.wm.quit_blender()
        return None
    bpy.app.timers.register(render_loaded,first_interval=.5)
    return None

if __name__=='__main__':
    if '--render' in sys.argv:
        pending=['before','after'];bpy.app.timers.register(render_next,first_interval=1)
    else:prepare()
