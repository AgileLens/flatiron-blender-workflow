"""Scientific contact sheet: resize/place source imagery, no retouching or relighting."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/photo-camera'
ARCHIVE=Path('/Users/alex/Archives/flatiron-real-camera-20260912-01a090f8')
font=Path('/System/Library/Fonts/Supplemental/Arial.ttf')
def f(n):return ImageFont.truetype(str(font),n)
margin=30;gap=22;pw=804;ph=789;head=158;foot=174
sheet=Image.new('RGB',(2*margin+3*pw+2*gap,head+ph+foot),(18,25,33));draw=ImageDraw.Draw(sheet)
draw.text((margin,24),'Flatiron | camera alignment against the real photograph',font=f(35),fill=(239,244,250))
draw.text((margin,73),'Only the camera changes between renders. Original-scale showcase geometry, materials and lighting are held fixed.',font=f(23),fill=(185,198,213))
labels=[('REFERENCE','Chris06, photo 02 | original full frame',ARCHIVE/'flatiron_02.jpg'),('BEFORE','Archived presentation baseline | 36.00 mm',OUT/'before.png'),('AFTER','Centered fitted camera | 38.50 mm',OUT/'after.png')]
for i,(name,caption,path) in enumerate(labels):
    x=margin+i*(pw+gap)
    draw.text((x,109),name,font=f(21),fill=(119,214,202) if i==2 else (239,244,250))
    draw.text((x+170,112),caption,font=f(19),fill=(185,198,213))
    im=Image.open(path).convert('RGB')
    assert im.size==(1608,1577)
    # Equal full-frame display, rounded to one panel pixel. Original files retained unchanged.
    im=im.resize((pw,ph),Image.Resampling.LANCZOS);sheet.paste(im,(x,head))
y=head+ph+22
draw.text((margin,y),'Guide alignment improves; the remaining shape and facade mismatch is substantial.',font=f(27),fill=(255,207,138))
draw.text((margin,y+41),'Held-out guide RMSE: 196.7 px before → 33.7 px after. Blender projection agrees with archived fit within 0.00021 px.',font=f(21),fill=(222,230,240))
draw.text((margin,y+75),'Approximate model, coplanar guides; no metric camera/depth validation. Photo: Chris06, CC BY-SA 4.0. Full-frame panels resized only.',font=f(20),fill=(185,198,213))
draw.text((margin,y+107),'Known inward-normal geometry is retained in both renders. This is a camera comparison, not a final appearance assessment.',font=f(20),fill=(255,207,138))
sheet.save(OUT/'camera-contact-sheet.png')
report={'classification':'real-photo camera alignment comparison, not calibrated reconstruction','visual_assessment':{'improved':'Fitted camera improves image placement and street-level proportions relative to archived presentation baseline.','remaining_mismatch':['Upper roof crest/crown and sculptural ornament do not match the photograph.','Repeated heavy window framing and facade bands differ substantially from the real wall/window proportions.','Showcase stone is pale and clean compared with the photograph; lighting and context are not reconstructed.'],'guide_limit':'Two coplanar rails with approximate band associations; held-out depth validation not established.','upper_nose_guide_error_px':85.7575139524953},'known_geometry_issue':'Parent relayed sibling audit: inward winding on 22,586 box shells and 2,478 medallion planar components. This camera comparison preserves source normals and is not final appearance QA.','projection_gate_max_px':.00020474159624700604,'render_process_exit_code':0,'render_pair_elapsed_seconds':37.464,'render_settings':{'engine':'Cycles CPU','threads':2,'samples':8,'resolution':[1608,1577]},'before_camera':'results.presentation_baseline, not the original showcase camera','after_camera':'results.centered','photo':{'path':str(ARCHIVE/'flatiron_02.jpg'),'sha256':hashlib.sha256((ARCHIVE/'flatiron_02.jpg').read_bytes()).hexdigest(),'credit':'Chris06, 2013 Flatiron Building (New York City) (1), CC BY-SA 4.0','url':'https://commons.wikimedia.org/wiki/File:2013_Flatiron_Building_(New_York_City)_(1).jpg'},'artifacts':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [OUT/'before.png',OUT/'after.png',OUT/'camera-contact-sheet.png',OUT/'projection-verification.json',ROOT/'scripts/apply_photo_camera.py']}}
(OUT/'comparison-report.json').write_text(json.dumps(report,indent=2))
print(OUT/'camera-contact-sheet.png')
