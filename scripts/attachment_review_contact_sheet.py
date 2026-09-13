from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/attachment-review'
def f(n):return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',n)
margin=24;gap=24;pw=1080;ph=1080;head=114;foot=166
sheet=Image.new('RGB',(2*pw+margin*2+gap,ph+head+foot),(18,25,33));draw=ImageDraw.Draw(sheet)
draw.text((margin,21),'Medallion backing | matched grazing comparison',font=f(32),fill=(239,244,250))
for i,(label,name) in enumerate([('BEFORE: CORRECTED NORMALS','before_grazing.png'),('AFTER: BACKED MEDALLIONS','backed_grazing.png')]):
 x=margin+i*(pw+gap);draw.text((x,75),label,font=f(24),fill=(119,214,202) if i else (239,244,250));sheet.paste(Image.open(OUT/name).convert('RGB'),(x,head))
 # Scientific annotation only: source render pixels remain unchanged in raw files.
 draw.rectangle((x+804,head+707,x+959,head+879),outline=(255,183,91),width=4)
y=head+ph+18
draw.text((margin,y),'TARGET PASS: large medallions have visible sidewalls joining supports; central recesses remain readable.',font=f(23),fill=(119,214,202))
draw.text((margin,y+35),'RETAINED: supported thin cresting in orange boxes; all 354 ledge rings have numerically verified contact.',font=f(23),fill=(255,207,138))
draw.text((margin,y+70),'Same preserved camera and daylight. Candidate SHA256: c37f707c7423…35b06582. Asset height remains 1.014 m.',font=f(21),fill=(222,230,240))
draw.text((margin,y+105),'One sampled view; no claim that all facade attachments are repaired. Cycles does not establish RealityKit culling or wearer acceptance.',font=f(21),fill=(185,198,213))
sheet.save(OUT/'attachment-comparison.png')
control=json.loads((OUT/'inputs/camera-control.json').read_text());actual=json.loads((OUT/'comparison-import-verification.json').read_text())['backed']
assert actual['cameras']['grazing']==control['camera']
report={'classification':'targeted backed-medallion PASS; retained thin cresting has verified closed-support contact','candidate_sha256':'c37f707c7423b468d0b7744912cad908808155794bd3d344e4ee04fc35b06582','before_sha256':control['before_package_sha256'],'render_exit_status':0,'new_render_frames':1,'elapsed_seconds':59.269,'camera_exactly_matches_preserved_control':True,'render_settings':{'engine':'Cycles CPU','threads':2,'samples':12,'resolution':[1080,1080]},'visual_target_verdict':'PASS for the sampled large Raised medallions: visible sidewalls bridge to backing and supporting columns; no visible air gap at inspected joins. Central recesses remain readable with support seen behind them.','global_attachment_verdict':'All-scene attachment proof is not claimed. The sampled Raised-ring repair passes visually. The unchanged thin ledge cresting is supported: the geometry audit verifies contact with closed ledge solids for all354 components, correcting the provisional floating interpretation.','supported_cresting_pixel_boxes':[[804,707,959,879]],'limits':['This one view cannot certify every one of the 1,062 repaired rings or all topology/holes. Geometry audit remains separate.','Cycles can render both surface sides; this is not RealityKit backface-culling or headset acceptance validation.','No geometry or input materials were modified by this review.','App runtime scale was not measured.'],'before_image_sha256':control['before_image_sha256'],'artifacts':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(OUT.glob('*.png'))}}
evidence=OUT/'inputs/residual-contact.json';contact=json.loads(evidence.read_text())
assert contact['components']==354 and contact['rings_intersecting_closed_support']==354 and contact['rings_with_inside_samples']==354 and not contact['rings_without_contact_evidence']
report['contact_audit']={'path':'inputs/residual-contact.json','sha256':hashlib.sha256(evidence.read_bytes()).hexdigest(),'geometry_auditor':'/root/vipe_benchmark','supported_rings':354,'samples_inside_closed_support_range':[min(x['samples_inside_closed_support'] for x in contact['rows']),max(x['samples_inside_closed_support'] for x in contact['rows'])],'closed_support_surface_intersections_range':[min(x['closed_support_surface_intersections'] for x in contact['rows']),max(x['closed_support_surface_intersections'] for x in contact['rows'])]}
report['correction']='Provisional detached/floating interpretation of the thin ledge cresting was overturned by numerical contact evidence. Raw before/after render files are unchanged.'
(OUT/'visual-review.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'camera_match':True,'comparison_sha256':hashlib.sha256((OUT/'attachment-comparison.png').read_bytes()).hexdigest()},indent=2))
