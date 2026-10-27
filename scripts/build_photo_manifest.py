"""Package the reference photos and their solved cameras for the native viewer.

Writes <out>/photos.json plus resized JPEGs (max 1600 px, attribution kept in the manifest).
Camera vectors stay in Blender full-scale coordinates (Z up); the app converts them.
  python3 scripts/build_photo_manifest.py <photos dir> docs/build5/photo-cameras.json docs/build5/correspondences.json \
      docs/build5/photo-licenses.json <out dir>
"""
import json, os, sys, math
import numpy as np
from PIL import Image
from photo_landmarks import landmark

photos, cams_path, corr_path, lic_path, out = sys.argv[1:6]
cams, corr, lic = json.load(open(cams_path)), json.load(open(corr_path)), {r['input']: r for r in json.load(open(lic_path))}
os.makedirs(out, exist_ok=True)
LICENSE_URL = {'CC BY-SA 4.0': 'https://creativecommons.org/licenses/by-sa/4.0/', 'CC BY 3.0': 'https://creativecommons.org/licenses/by/3.0/',
               'Public domain': 'https://creativecommons.org/publicdomain/mark/1.0/'}
AUTHOR = {'flatiron_01.jpg': 'Irving Underhill (1903)', 'flatiron_02.jpg': 'Chris06', 'flatiron_03.jpg': 'Mariano Gutierrez',
          'flatiron_04.jpg': 'Epicgenius', 'flatiron_05.jpg': 'Epicgenius', 'flatiron_06.jpg': 'Epicgenius',
          'flatiron_07.jpg': 'Epicgenius', 'flatiron_08.jpg': 'Unknown author (1909)'}
entries = []
for f in sorted(lic):
    L = lic[f]; name = L['LicenseShortName']
    if name not in LICENSE_URL:
        raise SystemExit(f'{f}: license {name!r} not cleared for bundling')
    im = Image.open(os.path.join(photos, f)).convert('RGB'); W0, H0 = im.size
    im.thumbnail((1600, 1600)); im.save(os.path.join(out, f), quality=86)
    adapted = name.startswith('CC')
    e = {'id': f.split('.')[0], 'file': f, 'title': L['title'].replace('File:', ''), 'author': AUTHOR[f], 'license': name,
         'licenseURL': LICENSE_URL[name], 'sourceURL': L['descriptionurl'],
         'credit': f"{AUTHOR[f]} · {name} · Wikimedia Commons" + (' · resized' if adapted else ''),
         'used': bool(f in cams and corr[f].get('used', False)), 'note': corr[f].get('why', ''),
         'bayNote': corr[f].get('bay_identification', '')}
    c = cams.get(f)
    if c and e['used']:
        R = np.array(c['R_world_to_camera_rdf']); C = np.array(c['C']); fpx = c['focal_px']; W, H = c['size']
        assert (W, H) == (W0, H0), f
        X = np.array([landmark(p['name']) for p in corr[f]['points']]); Pm = X.mean(0); Pu = Pm + [0, 0, 10.0]
        def uv(P):
            q = R @ (P - C); return [(fpx * q[0] / q[2] + W / 2) / W, (fpx * q[1] / q[2] + H / 2) / H]
        e['camera'] = {'positionBlender': C.tolist(), 'rightBlender': R[0].tolist(), 'upBlender': (-R[1]).tolist(),
                       'forwardBlender': R[2].tolist(), 'hfovDeg': c['hfov_deg'], 'vfovDeg': c['vfov_deg'],
                       'headingDeg': c['heading_deg_from_north'], 'pitchDeg': c['pitch_deg'], 'heightM': c['camera_height_m'],
                       'anchorBlender': Pm.tolist(), 'anchorUV': uv(Pm), 'anchorUpUV': uv(Pu),
                       'fitRMSEpx': c['fit_rmse_px'], 'holdoutRMSEpx': c['holdout_rmse_px'], 'imageSizePx': [W, H],
                       'focalSource': c['focal_source']}
    entries.append(e)
json.dump({'photos': entries, 'coordinateNote': 'Blender full scale, metres, Z up; USDZ asset = Blender / 87 with Z-up -> RealityKit Y-up (x, z, -y)'},
          open(os.path.join(out, 'photos.json'), 'w'), indent=1)
print('MANIFEST', len(entries), 'photos,', sum(e['used'] for e in entries), 'with cameras ->', out)
