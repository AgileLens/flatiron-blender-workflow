from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/normals-review'
font='/System/Library/Fonts/Supplemental/Arial.ttf'
def f(n):return ImageFont.truetype(font,n)
metrics={}
for view in ['overview','grazing']:
 images=[Image.open(OUT/(label+'_'+view+'.png')).convert('RGB') for label in ['baseline','normals_fixed']]
 a,b=[np.asarray(im,dtype=np.int16) for im in images];d=np.abs(a-b)
 metrics[view]={'mean_abs_rgb_difference_0_255':float(d.mean()),'max_abs_rgb_difference_0_255':int(d.max()),'differing_pixel_fraction':float(np.any(d!=0,axis=2).mean())}
 pw,ph=images[0].size;margin=24;gap=24;head=112;foot=122
 sheet=Image.new('RGB',(2*pw+2*margin+gap,ph+head+foot),(18,25,33));draw=ImageDraw.Draw(sheet)
 title='Raised facade rings remain separated after normal correction' if view=='grazing' else 'Flatiron normal correction | matching overview'
 draw.text((margin,20),title,font=f(30 if view=='grazing' else 25),fill=(239,244,250))
 for i,(label,im) in enumerate(zip(['ORIGINAL BASELINE','CORRECTED NORMALS'],images)):
  x=margin+i*(pw+gap);draw.text((x,71),label,font=f(24),fill=(119,214,202) if i else (239,244,250));sheet.paste(im,(x,head))
 y=head+ph+18
 draw.text((margin,y),'Same imported size: 0.403 × 0.850 × 1.014 m. Same camera, material inputs and daylight.',font=f(22 if view=='grazing' else 20),fill=(222,230,240))
 draw.text((margin,y+34),'Cycles renders both surface sides; this does not establish RealityKit backface-culling behavior.',font=f(22 if view=='grazing' else 20),fill=(185,198,213))
 draw.text((margin,y+68),'Geometry was not moved. The app’s runtime scale is outside this comparison.',font=f(22 if view=='grazing' else 20),fill=(255,207,138))
 sheet.save(OUT/(view+'-comparison.png'))
report={'classification':'geometry visibility diagnostic, no appearance acceptance','render_exit_status':0,'render_elapsed_seconds':90.659,'render_frames':4,'same_camera_and_lighting':True,'observations':['Both grazing renders show thin open medallion rings standing in front of backing strips and ledges, with visible separation and displaced ring-shaped shadows.','Normal correction does not close the visible medallion spacing in these views.','The overall building silhouette and imported bounds are unchanged.'],'limits':['Cycles may render both sides of surfaces, unlike runtime backface culling; the renders do not establish whether normal correction fixes the RealityKit culling defect.','Pixel differences include stochastic render/denoising effects and are not an independent proof of geometric equality.','The app runtime scale and user scale controls were not measured.'], 'target_source_metres':[8.18083405,1.33939765,75.05000067],'target_provenance':'SceneAudit sibling /root/vipe_benchmark supplied Raised medallions component faces 6528–6543','asset_scale_from_source':1/87,'imported_dimensions_metres':[.4034300446510315,.8500281870365143,1.0135633731260896],'pixel_difference_metrics':metrics,'artifacts':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(OUT.glob('*.png'))}}
(OUT/'visual-review.json').write_text(json.dumps(report,indent=2))
print(json.dumps(metrics,indent=2))
