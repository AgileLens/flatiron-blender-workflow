"""Gridded, zoomed crop of a photo for reading landmark pixel coordinates by eye.
  python3 scripts/grid_crop.py <photo> x0 y0 x1 y1 step maxwidth out.png   (x1/y1 <= 0 means full size)
Grid labels are in original-image pixels; PHOTOS env var sets the photo directory."""
import sys
from PIL import Image, ImageDraw, ImageFont
import os
P=os.environ.get('PHOTOS', 'outputs/references') + '/'
f,x0,y0,x1,y1,step,maxw,out=sys.argv[1],*map(int,sys.argv[2:8]),sys.argv[8]
im=Image.open(P+f).convert('RGB')
if x1<=0: x1=im.width
if y1<=0: y1=im.height
c=im.crop((x0,y0,x1,y1)); k=maxw/c.width; c=c.resize((maxw,int(c.height*k)))
d=ImageDraw.Draw(c); fnt=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
for x in range((x0//step+1)*step, x1, step):
    X=(x-x0)*k; d.line([(X,0),(X,c.height)],fill=(255,0,0) if x%(step*5)==0 else (255,120,0),width=1); d.text((X+2,2),str(x),fill=(255,255,0),font=fnt)
for y in range((y0//step+1)*step, y1, step):
    Y=(y-y0)*k; d.line([(0,Y),(c.width,Y)],fill=(0,160,255) if y%(step*5)==0 else (0,220,255),width=1); d.text((2,Y+2),str(y),fill=(255,255,0),font=fnt)
c.save(out); print(out, c.size)
