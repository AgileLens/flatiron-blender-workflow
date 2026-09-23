"""Composite each solved-camera render over its photo: photo | 50% blend with landmarks.

Model windows render magenta (glass) and yellow (frames); stone is a holdout, so the photo shows through.
Red crosses = annotated photo points, green circles = model projection (fit), yellow = held out.
  python3 scripts/compose_photo_overlays.py docs/build5/photo-cameras.json <photos dir> <renders dir> docs/build5
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

cams, photos, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
sheets = sys.argv[4] if len(sys.argv) > 4 else out
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 22)
for photo, c in cams.items():
    render = os.path.join(out, 'render-' + photo.replace('.jpg', '.png'))
    if not os.path.exists(render):
        continue
    im = Image.open(os.path.join(photos, photo)).convert('RGBA'); r = Image.open(render).convert('RGBA').resize(im.size)
    a = r.split()[3].point(lambda v: int(v * .6)); r.putalpha(a)
    blend = Image.alpha_composite(im, r); d = ImageDraw.Draw(blend)
    for p in c['points']:
        (u, v), (pu, pv) = p['observed'], p['projected']
        d.line([(u - 9, v), (u + 9, v)], fill=(255, 30, 30, 255), width=3); d.line([(u, v - 9), (u, v + 9)], fill=(255, 30, 30, 255), width=3)
        col = (255, 220, 0, 255) if p['holdout'] else (40, 230, 60, 255)
        d.ellipse([pu - 6, pv - 6, pu + 6, pv + 6], outline=col, width=3); d.line([(u, v), (pu, pv)], fill=col, width=2)
    used = c.get('used')
    label = (f"{photo}  fit {c['fit_rmse_px']:.1f}px  holdout {c['holdout_rmse_px'] if c['holdout_rmse_px'] is None else round(c['holdout_rmse_px'], 1)}px  "
             f"f={c['focal_px']:.0f}px ({c['focal_source']})  {'USED' if used else 'NOT USED' if used is False else ''}")
    W = im.width; sheet = Image.new('RGBA', (W * 2 + 30, im.height + 60), (18, 24, 30, 255))
    sheet.paste(im, (10, 50)); sheet.paste(blend, (W + 20, 50))
    ImageDraw.Draw(sheet).text((12, 12), label, fill=(235, 235, 235, 255), font=font)
    k = 2400 / sheet.width
    sheet.convert('RGB').resize((2400, int(sheet.height * k))).save(os.path.join(sheets, 'overlay-' + photo), quality=85)
    print('SHEET', photo)
