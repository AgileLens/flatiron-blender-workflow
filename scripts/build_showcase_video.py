"""Compose an honest process showcase from original photos and rendered outputs."""
import argparse,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--photos',type=Path,required=True);p.add_argument('--ffmpeg',default='ffmpeg');p.add_argument('--font',default='/System/Library/Fonts/Supplemental/Arial.ttf');p.add_argument('--stills-only',action='store_true');a=p.parse_args()
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'outputs';clips=out/'clips';clips.mkdir(exist_ok=True)
def run(args):subprocess.run([a.ffmpeg,'-hide_banner','-loglevel','error','-y',*args],check=True)
def title(text,key,size,y,color='white'):
 f=clips/(key+'.txt');f.write_text(text)
 return f"drawtext=fontfile='{a.font}':textfile='{f}':fontsize={size}:fontcolor={color}:x=38:y={y}"
def still(name,imgs,headline,sub,foot,duration=4):
 args=[];n=len(imgs);width=1200//n;height=490
 for im in imgs:args+=['-loop','1','-framerate','24','-i',str(im)]
 f=[]
 for i in range(n):f.append(f'[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x14191e,setsar=1[v{i}]')
 f.append((''.join(f'[v{i}]' for i in range(n))+f'hstack=inputs={n},' if n>1 else '[v0]')+'pad=1280:720:40:152:color=0x14191e,'+','.join([title(headline,name+'h',34,35),title(sub,name+'s',20,89,'0xdbc39b'),title(foot,name+'f',15,675,'0xb4bdc5'),f'fade=t=in:d=0.18,fade=t=out:st={duration-.18}:d=0.18'])+'[v]')
 run(args+['-filter_complex',';'.join(f),'-map','[v]','-t',str(duration),'-r','24','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(clips/(name+'.mp4'))])
photo=lambda i:a.photos/f'flatiron_{i:02d}.jpg'
still('01',[photo(i) for i in range(1,5)],'FLATIRON / Eight reference images','Historic form. Street-level proportions. Facade detail.','Photos via Wikimedia Commons: Irving Underhill; Chris06; Mariano Gutierrez; Epicgenius. Full credits in repository.',3)
still('02',[photo(i) for i in range(5,9)],'READ THE BUILDING','A rounded wedge. Repeating bays. A layered cornice.','Epicgenius / CC BY-SA 4.0; historical 1909 image / public domain. Image credits and source links in repository.',3)
still('03',[photo(2),out/'match-overview.png'],'REFERENCE → EDITABLE GEOMETRY','Approximate comparison angle | Blender mesh and materials','Reference: Chris06 / CC BY-SA 4.0. Dimensions are estimates; this is not a calibrated reconstruction.',5)
still('04',[photo(4),out/'match-detail.png'],'INSPECT. REVISE. RENDER.','Facade relief and cornice refined through a live Blender MCP loop','Reference: Epicgenius / CC BY-SA 4.0. Sculpture remains simplified. Process reconstruction, not original timelapse.',4)
if a.stills_only:raise SystemExit(0)
frames=sorted((out/'orbit').glob('*.png'))
if len(frames)!=144:raise SystemExit(f'Orbit incomplete: {len(frames)}/144 frames')
filters="minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"+title('FLATIRON / Light and form','orbith',26,30)+','+title('Editable model · Cycles render','orbits',18,671,'0xeeeeee')+',fade=t=in:d=.18,fade=t=out:st=11.7:d=.18'
run(['-framerate','12','-i',str(out/'orbit/%04d.png'),'-vf',filters,'-r','24','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(clips/'05.mp4')])
# Closing card, with the audited pass explicitly scoped.
still('06',[out/'hero-final.png'],'BUILD IT. INSPECT IT. SHARE IT.','Astra + Codex + Blender MCP | Open workflow by Agile Lens','Successful pass: 63,929 uncached input + 4,214 output + 438,656 cached input. Full experiment receipt in repository.',4)
manifest=clips/'concat.txt';manifest.write_text(''.join(f"file '{clips / (str(i).zfill(2)+'.mp4')}'\n" for i in range(1,7)))
run(['-f','concat','-safe','0','-i',str(manifest),'-c','copy','-movflags','+faststart',str(out/'flatiron-showcase.mp4')])
print(out/'flatiron-showcase.mp4')
