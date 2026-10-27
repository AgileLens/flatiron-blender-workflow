"""Named landmarks for the parameterised generator (flatiron_v5). Same names as photo_landmarks.py.

compute(names, params) -> {name: (x, y, z)} using a layout-only build (~25 ms).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flatiron_v5 as F


def compute(names, params=None):
    F.configure(params)
    F.LAYOUT_ONLY = True
    try:
        path = F.build()
    finally:
        F.LAYOUT_ONLY = False
    feats = {f['name']: f for f in path.features}
    slots = F.side_slots(path)
    bands = {'cornice': (1.70, F.Z[21] + 1.72), 'c17': (0.55, F.Z[18] + 0.25), 'c4': (0.38, F.Z[5] + 0.15),
             'dentil3': (0.30, F.Z[4] + 0.10), 'ground_cornice': (0.58, F.Z[2] + .15), 'ground': (0.0, 0.0)}
    index = {}
    for r in F.LAYOUT:
        index[(r['story'], r['tag'])] = r

    def pt(s, d, z):
        x, y = path.at(s, d); return (x, y, z)

    def one(name):
        p = name.split('/')
        if p[0] in ('top', 'ground'):
            f = feats[p[1]]; s = (f['s0'] + f['s1']) / 2
            return pt(s, 1.70, F.Z[21] + 1.72) if p[0] == 'top' else pt(s, 0.0, 0.0)
        if p[0] == 'band':
            f = feats[p[1]]; d, z = bands[p[2]]; return pt((f['s0'] + f['s1']) / 2, d, z)
        if p[0] == 'arc':
            f = feats[p[1]]; return pt((f['s0'] + f['s1']) / 2, float(p[2]), float(p[3]))
        if p[0] == 'oriel':
            return pt(slots[p[1]][int(p[2])], 0.65 + 0.26, F.Z[15] + 0.46)
        if p[0] == 'oculus':
            return pt(slots[p[1]][4], 0.0, (F.Z[2] + F.Z[3]) / 2 + .1)
        if p[0] == 'win':
            side, pair, win, story, corner = p[1], int(p[2]), p[3], int(p[4]), p[5]
            r = index[(story, (side, pair, win if win == 'pair' else int(win)))]
            s0, s1, zb, zt = r['s0'], r['s1'], r['zb'], r['zt']
            return {'bl': pt(s0, 0, zb), 'br': pt(s1, 0, zb), 'tl': pt(s0, 0, zt), 'tr': pt(s1, 0, zt),
                    'crown': pt((s0 + s1) / 2, 0, zt), 'ct': pt((s0 + s1) / 2, 0, zt), 'cb': pt((s0 + s1) / 2, 0, zb)}[corner]
        raise KeyError(name)

    return {n: one(n) for n in names}


if __name__ == '__main__':
    import photo_landmarks
    names = sys.argv[1:] or ['top/Prow', 'win/Fifth/4/pair/18/crown', 'oculus/Broadway', 'band/SE/c17', 'win/Fifth/1/0/4/br']
    got = compute(names)
    for n in names:
        a, b = got[n], photo_landmarks.landmark(n)
        print(n, [round(v, 4) for v in a], 'max diff vs v4', round(max(abs(x - y) for x, y in zip(a, b)), 9))
