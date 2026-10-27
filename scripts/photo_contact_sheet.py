"""One contact sheet of every reference photo with its solved-camera window overlay (60%).
  python3 scripts/photo_contact_sheet.py docs/build5/photo-cameras.json <photos dir> <renders dir> docs/build5/overlay-contact-sheet.jpg
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont
cams_path, P, R, out = sys.argv[1:5]
cams = json.load(open(cams_path))
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 18)
tiles = []
for f in [f'flatiron_0{i}.jpg' for i in range(1, 9)]:
    im = Image.open(P + '/' + f).convert('RGBA'); c = cams.get(f)
    if c and c.get('used') is not False and 'R_world_to_camera_rdf' in c:
        r = Image.open(R + '/render-' + f.replace('.jpg', '.png')).convert('RGBA'); r.putalpha(r.split()[3].point(lambda v: int(v * .6)))
        im = Image.alpha_composite(im, r); txt = f"{f[9:11]}  fit {c['fit_rmse_px']:.1f}px  holdout {c['holdout_rmse_px']:.1f}px  USED"
    else:
        txt = f"{f[9:11]}  not solved (no unique landmarks)  NOT USED"
    im = im.convert('RGB'); im.thumbnail((560, 620)); t = Image.new('RGB', (580, 660), (18, 24, 30))
    t.paste(im, (10, 34)); ImageDraw.Draw(t).text((10, 8), txt, fill=(235, 235, 235), font=font); tiles.append(t)
sheet = Image.new('RGB', (580 * 4, 660 * 2), (18, 24, 30))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % 4) * 580, (i // 4) * 660))
sheet.save(out, quality=85); print('CONTACT', out)
