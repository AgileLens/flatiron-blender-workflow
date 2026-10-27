"""Named 3D landmarks on the build-4 model, for camera solves against the reference photos.

Names (all at full scale, Blender Z-up metres, facade plane d=0 unless stated):
  win/<side>/<pair>/<window>/<story>/<corner>
      side: Fifth | Broadway | 22nd | SW | SE | Prow; window: 0/1 (pairs), 0..2 (prow), 'pair' for
      two-bay openings (stories 1-3, 18). corner: bl br tl tr (left/right as seen from outside, which
      is always the path direction), crown (arch top), cb (bottom centre).
  top/<SW|SE|Prow>      top of the main cornice (corona) at the corner's arc midpoint, d=+1.70
  ground/<SW|SE|Prow>   foot of the facade at the corner's arc midpoint
  oculus/<Fifth|Broadway>  centre of the oculus over the entrance
  oriel/<Fifth|Broadway>/<pair>/hood  top of an oriel hood at the middle of its front face
  band/<SW|SE|Prow>/<cornice|c17|c4|dentil3|ground_cornice|ground>  top of a band at a corner (arc midpoint)
Path order is CCW: 22nd St runs west->east, Broadway south->north, Fifth north->south. So on
Broadway pair 0 is at the SE end and pair 8 at the prow; on Fifth pair 0 is at the prow.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flatiron_v4 as F

PATH = F.build()
FEATS = {f['name']: f for f in PATH.features}


# (projection, top height) of the horizontal bands that are easy to find at a corner in a photo
BANDS = {'cornice': (1.70, F.Z[21] + 1.72), 'c17': (0.55, F.Z[18] + 0.25), 'c4': (0.38, F.Z[5] + 0.15),
         'dentil3': (0.30, F.Z[4] + 0.10), 'ground_cornice': (0.58, 5.75), 'ground': (0.0, 0.0)}


def _pt(s, d, z):
    x, y = PATH.at(s, d)
    return (x, y, z)


def landmark(name):
    parts = name.split('/')
    if parts[0] in ('top', 'ground'):
        f = FEATS[parts[1]]; s = (f['s0'] + f['s1']) / 2
        return _pt(s, 1.70, F.Z[21] + 1.72) if parts[0] == 'top' else _pt(s, 0.0, 0.0)
    if parts[0] == 'arc':      # arc/<SW|SE|Prow>/<d>/<z>: corner arc midpoint at offset d and height z
        f = FEATS[parts[1]]; return _pt((f['s0'] + f['s1']) / 2, float(parts[2]), float(parts[3]))
    if parts[0] == 'band':     # band/<SW|SE|Prow>/<name>: where a documented band crosses a corner
        f = FEATS[parts[1]]; d, z = BANDS[parts[2]]; return _pt((f['s0'] + f['s1']) / 2, d, z)
    if parts[0] == 'oriel':    # oriel/<side>/<pair>/hood: top of the hood, middle of the front face
        c = F.side_slots(PATH)[parts[1]][int(parts[2])]
        return _pt(c, 0.65 + 0.26, F.Z[15] + 0.46)
    if parts[0] == 'oculus':   # oculus over the Fifth/Broadway entrance (pair 4, 2nd story)
        c = F.side_slots(PATH)[parts[1]][4]
        return _pt(c, 0.0, (F.Z[2] + F.Z[3]) / 2 + .1)
    if parts[0] == 'win':
        side, pair, win, story, corner = parts[1], int(parts[2]), parts[3], int(parts[4]), parts[5]
        win = win if win == 'pair' else int(win)
        rows = [r for r in F.LAYOUT if r['story'] == story and r['tag'] == (side, pair, win)]
        if len(rows) != 1:
            raise KeyError(f'{name}: {len(rows)} matching openings')
        r = rows[0]; s0, s1, zb, zt = r['s0'], r['s1'], r['zb'], r['zt']
        return {'bl': _pt(s0, 0, zb), 'br': _pt(s1, 0, zb), 'tl': _pt(s0, 0, zt), 'tr': _pt(s1, 0, zt),
                'crown': _pt((s0 + s1) / 2, 0, zt), 'ct': _pt((s0 + s1) / 2, 0, zt), 'cb': _pt((s0 + s1) / 2, 0, zb)}[corner]
    raise KeyError(name)


if __name__ == '__main__':
    for n in sys.argv[1:]:
        print(n, [round(v, 3) for v in landmark(n)])
