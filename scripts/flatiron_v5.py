"""Flatiron build-6 geometry (v5): the build-4 generator with photo-calibrated dimensions.

Identical construction to flatiron_v4.py; every dimension the reference-photo camera solves can
constrain is a named parameter (PARAMS). configure(params) applies a set, build(layout_only=True)
returns the opening layout in milliseconds for fitting (scripts/refit_geometry.py), and the
calibrated values live in docs/build6/geometry-params.json. With V4_PARAMS this reproduces build 4.

Original v4 notes follow.

Why a new generator: the original replay (flatiron_base.py + live_steps.json)
inset its wall body 12 cm (`ring(0,84.6,-.12,0)`) but laid glass, frames,
sills, rustication and relief at depths measured from the lot line, so 14,692
of 27,362 exported pieces hover 1-52 cm in front of the wall (see
docs/build4/audit-before-build3.json). It also used an isosceles 80 x 32 m
footprint and one identical window per 3.05 m bay on every floor.

This generator rebuilds the building from documented dimensions (REFERENCES)
and enforces two rules at the source:
  * every element is a closed, outward-wound solid (checked per element);
  * every facade element is mounted: its back face is embedded in the element
    it hangs from (core, pier, ring or panel). Nothing is placed by eye.
scripts/audit_attachment.py then verifies zero floating parts on the exported USDZ.

Run in Blender 5.2.1:  Blender -b --factory-startup --python scripts/flatiron_v4.py -- --out outputs/build4
Geometry-only self-check (no Blender):  python3 scripts/flatiron_v4.py --dry
"""
import math, json, sys, os, argparse
from bisect import bisect_right
from collections import defaultdict, Counter

FT = 0.3048
REFERENCES = {
    'site': 'Wikipedia "Flatiron Building" (Site): 197.5 ft Fifth Ave (west), 214.5 ft Broadway (east), '
            '86 ft 22nd St (south); scalene right triangle; all three corners rounded above ground.',
    'prow': 'Wikipedia (Superstructure): vertex only 6-6.5 ft (2 m) wide; Broadway/Fifth meet at about 25 degrees.',
    'height': 'Wikipedia (Architecture): originally 285-286 ft with 20 stories and an attic; penthouse added 1905.',
    'bays': 'Wikipedia (Facade): Fifth and Broadway 18 bays wide, 22nd St 8 bays, bays arranged in pairs; '
            'curved SW/SE corners with one rounded window per story; prow has three sash windows per story, '
            'the central one wider.',
    'columns': 'Wikipedia (Superstructure): perimeter columns 17 ft apart on Fifth, 18.5 ft on Broadway, 16 ft on 22nd St.',
    'base': 'Wikipedia (Base): three-story limestone base, openings two bays wide, two sash windows per opening on '
            'the 2nd/3rd stories; entrances at the centres of Fifth and Broadway and both ends of 22nd St; '
            'fluted engaged columns, oculus above the entrances, projecting cornice over the ground floor, '
            'dentil frieze above the 3rd story; prow has a pair of two-story columns.',
    'upper': 'Wikipedia (Upper stories): 4th story transitional with alternating wide/narrow piers and wreaths, '
             'roundel frieze and cornice above; meander frieze above the 6th; three trapezoidal oriels on the '
             '7th-14th stories of Fifth and Broadway, three windows per story each; 15th rusticated piers; '
             '16th arched windows with voussoirs under a cornice; 17th transitional with roundels and lions; '
             '18th-19th double-height double-width arcade with metal spandrels; 20th small square windows with '
             'triglyphs; cornice with dentils and brackets projecting about 5.5 ft; balustrade above.',
    'photos': 'Visual checks against the eight credited input photos in docs/photo-credits.md (paired windows, '
              'deep reveals, dark brown sash frames, oriel positions at pairs 2, 5 and 8 of 9).',
}

# ---------------------------------------------------------------- parameters
V4_PARAMS = {
    'lot_fifth': 197.5 * FT, 'lot_22nd': 86 * FT, 'sw_angle_deg': 90.0,
    'r_sw': 1.9, 'r_se': 1.7, 'r_prow': 1.05,
    'pitch_Fifth': 17 * FT + .35, 'pitch_Broadway': 18.5 * FT + .35, 'pitch_22nd': 16 * FT + .35,
    'prow_margin_Fifth': None, 'prow_margin_Broadway': None,     # None: centred (v4)
    'ww': 1.42, 'np': .85,
    'z_ground': 5.6, 'h_base': 4.2, 'h_4': 4.1, 'h_shaft': 3.95, 'h_arcade': 4.1, 'h_20': 3.65,
}
PARAMS = dict(V4_PARAMS)
LOT_FIFTH, LOT_22ND = PARAMS['lot_fifth'], PARAMS['lot_22nd']
R_SW, R_SE, R_PROW = PARAMS['r_sw'], PARAMS['r_se'], PARAMS['r_prow']
LAYOUT_ONLY = False
PAIRS = {'Fifth': 9, 'Broadway': 9, '22nd': 4}
ENTRANCE_PAIRS = {'Fifth': [4], 'Broadway': [4], '22nd': [0, 3]}
ORIEL_PAIRS = {'Fifth': [1, 4, 7], 'Broadway': [1, 4, 7]}
WW, NP = PARAMS['ww'], PARAMS['np']            # sash width, narrow pier within a pair
RECESS, EMBED = 0.30, 0.02                     # glass plane depth, mount overlap
D0 = -(RECESS + EMBED)                          # back of piers/spandrels (inside core)
Z = {}
ROOF = 0.0


def configure(params=None):
    """Apply a parameter set (missing keys keep V4_PARAMS values) and reset the geometry buffers."""
    global LOT_FIFTH, LOT_22ND, R_SW, R_SE, R_PROW, WW, NP, ROOF, G, LAYOUT
    PARAMS.clear(); PARAMS.update(V4_PARAMS); PARAMS.update(params or {})
    LOT_FIFTH, LOT_22ND = PARAMS['lot_fifth'], PARAMS['lot_22nd']
    R_SW, R_SE, R_PROW = PARAMS['r_sw'], PARAMS['r_se'], PARAMS['r_prow']
    WW, NP = PARAMS['ww'], PARAMS['np']
    Z.clear(); Z[1] = 0.0; Z[2] = PARAMS['z_ground']; Z[3] = Z[2] + PARAMS['h_base']; Z[4] = Z[3] + PARAMS['h_base']
    Z[5] = Z[4] + PARAMS['h_4']
    for n in range(6, 19):
        Z[n] = Z[5] + (n - 5) * PARAMS['h_shaft']             # 5th-17th stories
    Z[19] = Z[18] + PARAMS['h_arcade']; Z[20] = Z[19] + PARAMS['h_arcade']; Z[21] = Z[20] + PARAMS['h_20']
    ROOF = Z[21] + 2.05                                       # top of the main cornice
    G = Geometry(); LAYOUT = []


HOOD_STORIES = {2, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15}   # stories with room for a lintel under the next band

LIME, TERRA, MORTAR, GLASS, FRAME, ROOFM, WALK, ASPHALT = (
    'Warm limestone', 'Pale terracotta relief', 'Mortar shadow', 'Recessed blue charcoal glass',
    'Bronze window frames', 'Roof zinc', 'Sidewalk', 'Asphalt')
MATERIALS = {  # linear base colour, roughness, metallic; darker/warmer than the chalky v1 values
    LIME: ((.49, .45, .37), .62, 0), TERRA: ((.52, .48, .39), .58, 0), MORTAR: ((.27, .24, .19), .75, 0),
    GLASS: ((.035, .045, .05), .12, .15), FRAME: ((.105, .062, .035), .45, .1), ROOFM: ((.24, .27, .27), .7, 0),
    WALK: ((.43, .44, .42), .7, 0), ASPHALT: ((.115, .135, .15), .8, 0)}


# ---------------------------------------------------------------- vector helpers
def add(a, b): return (a[0] + b[0], a[1] + b[1])
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def mul(a, k): return (a[0] * k, a[1] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1]
def length(a): return math.hypot(a[0], a[1])
def unit(a):
    L = length(a); return (a[0] / L, a[1] / L)
def rnormal(t): return (t[1], -t[0])            # outward normal for a CCW boundary


class Path:
    """Piecewise-linear path with per-vertex outward normals; offset d is along the normal."""
    def __init__(self, pts, nrm, closed):
        self.p, self.n, self.closed = pts, nrm, closed
        self.s = [0.0]
        for i in range(1, len(pts)):
            self.s.append(self.s[-1] + length(sub(pts[i], pts[i - 1])))
        self.S = self.s[-1] + (length(sub(pts[0], pts[-1])) if closed else 0.0)
        self.features = []

    @staticmethod
    def line(a, b):
        n = rnormal(unit(sub(b, a)))
        return Path([a, b], [n, n], False)

    def _locate(self, s):
        if self.closed:
            s %= self.S
        else:
            s = min(max(s, 0.0), self.S)
        i = min(bisect_right(self.s, s) - 1, len(self.p) - 1)
        if not self.closed and i == len(self.p) - 1:
            i -= 1
        j = (i + 1) % len(self.p)
        s1 = self.s[j] if j > 0 else self.S
        u = (s - self.s[i]) / max(s1 - self.s[i], 1e-12)
        return i, j, u

    def at(self, s, d=0.0):
        i, j, u = self._locate(s)
        p = add(self.p[i], mul(sub(self.p[j], self.p[i]), u))
        n = unit(add(mul(self.n[i], 1 - u), mul(self.n[j], u)))
        return add(p, mul(n, d))

    def frame(self, s):
        i, j, u = self._locate(s)
        n = unit(add(mul(self.n[i], 1 - u), mul(self.n[j], u)))
        return self.at(s), (-n[1], n[0]), n

    def samples(self, s0, s1):
        out = [s0]
        if self.closed:
            for k in range(int(math.floor(s0 / self.S)), int(math.floor(s1 / self.S)) + 1):
                out += [v + k * self.S for v in self.s if s0 + 1e-6 < v + k * self.S < s1 - 1e-6]
        else:
            out += [v for v in self.s if s0 + 1e-6 < v < s1 - 1e-6]
        return sorted(out) + [s1]

    def feature_at(self, s):
        s %= self.S
        for f in self.features:
            if f['s0'] - 1e-6 <= s <= f['s1'] + 1e-6:
                return f
        return None


def lines_intersect(p, d, q, e):
    den = d[0] * e[1] - d[1] * e[0]
    t = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
    return add(p, mul(d, t))


def footprint(inset=0.0, segs=(10, 10, 14), trim_prow=0.0):
    """Closed CCW path of the lot triangle with filleted corners, optionally inset."""
    W, L = LOT_22ND, LOT_FIFTH
    a = math.radians(PARAMS['sw_angle_deg'])                     # angle between 22nd St and Fifth Ave
    C = [(-W / 2, -L / 2), (W / 2, -L / 2), (-W / 2 + L * math.cos(a), -L / 2 + L * math.sin(a))]   # SW, SE, prow
    radii = [R_SW, R_SE, R_PROW]
    if inset:
        lines = []
        for i in range(3):
            a, b = C[i], C[(i + 1) % 3]
            t = unit(sub(b, a)); lines.append((add(a, mul(rnormal(t), -inset)), t))
        C = [lines_intersect(*lines[i - 1], *lines[i]) for i in range(3)]
        radii = [max(r - inset, .35) for r in radii]
    if trim_prow:   # blunt the prow for set-back roof structures
        radii[2] = max(radii[2], trim_prow)
    names = ['SW', 'SE', 'Prow']; sides = ['22nd', 'Broadway', 'Fifth']
    pts, nrm, arcs = [], [], []
    for i, c in enumerate(C):
        a = unit(sub(C[i - 1], c)); b = unit(sub(C[(i + 1) % 3], c))
        ang = math.acos(max(-1, min(1, dot(a, b)))); r = radii[i]
        center = add(c, mul(unit(add(a, b)), r / math.sin(ang / 2)))
        start = add(c, mul(a, r / math.tan(ang / 2))); end = add(c, mul(b, r / math.tan(ang / 2)))
        sa = math.atan2(start[1] - center[1], start[0] - center[0])
        ea = math.atan2(end[1] - center[1], end[0] - center[0])
        while ea < sa:
            ea += 2 * math.pi
        i0 = len(pts)
        for j in range(segs[i] + 1):
            th = sa + (ea - sa) * j / segs[i]
            pts.append(add(center, (r * math.cos(th), r * math.sin(th)))); nrm.append((math.cos(th), math.sin(th)))
        arcs.append((names[i], i0, len(pts) - 1, r, center))
    path = Path(pts, nrm, True)
    for k, (name, i0, i1, r, center) in enumerate(arcs):
        path.features.append({'kind': 'arc', 'name': name, 's0': path.s[i0], 's1': path.s[i1], 'r': r})
        nxt = arcs[(k + 1) % 3][1]
        s0 = path.s[i1]; s1 = path.s[nxt] if nxt else path.S
        path.features.append({'kind': 'side', 'name': sides[k], 's0': s0, 's1': s1,
                              't': unit(sub(pts[nxt], pts[i1])), 'n': nrm[i1]})
    return path


def clip_y(poly, ymax):
    out = []
    for i in range(len(poly)):
        a, b = poly[i - 1], poly[i]
        ina, inb = a[1] <= ymax, b[1] <= ymax
        if ina != inb:
            u = (ymax - a[1]) / (b[1] - a[1]); out.append((a[0] + (b[0] - a[0]) * u, ymax))
        if inb:
            out.append(b)
    return out


def offset_convex(poly, delta):
    area = sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))
    if area < 0:
        poly = poly[::-1]
    lines = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        t = unit(sub(b, a)); lines.append((add(a, mul(rnormal(t), delta)), t))
    return [lines_intersect(*lines[i - 1], *lines[i]) for i in range(len(lines))]


# ---------------------------------------------------------------- solids
class Geometry:
    def __init__(self):
        self.v = defaultdict(list); self.f = defaultdict(list); self.count = Counter()

    def solid(self, mat, verts, faces, tag):
        vol = 0.0
        for f in faces:
            a = verts[f[0]]
            for k in range(1, len(f) - 1):
                b, c = verts[f[k]], verts[f[k + 1]]
                vol += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                        + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
        if abs(vol) < 1e-9:
            raise ValueError(f'degenerate solid {tag}')
        if vol < 0:
            faces = [tuple(reversed(f)) for f in faces]
        edges = Counter()
        for f in faces:
            for k in range(len(f)):
                edges[(f[k], f[(k + 1) % len(f)])] += 1
        for (a, b), c in edges.items():
            if c != 1 or edges.get((b, a)) != 1:
                raise ValueError(f'open or inconsistent solid {tag}')
        base = len(self.v[mat])
        self.v[mat].extend(verts)
        self.f[mat].extend(tuple(base + i for i in f) for f in faces)
        self.count[tag] += 1

    def sweep(self, mat, sections, tag, loop=False):
        k = len(sections[0]); verts = [p for sec in sections for p in sec]; faces = []
        m = len(sections)
        for a in range(m if loop else m - 1):
            b = (a + 1) % m
            for i in range(k):
                j = (i + 1) % k
                faces.append((a * k + i, a * k + j, b * k + j, b * k + i))
        if not loop:
            faces.append(tuple(reversed(range(k))))
            faces.append(tuple((m - 1) * k + i for i in range(k)))
        self.solid(mat, verts, faces, tag)

    def extrude(self, mat, bottom, top, tag):
        """Two matching convex rings; large caps are fan-triangulated around a centre vertex."""
        k = len(bottom); verts = list(bottom) + list(top); faces = []
        for i in range(k):
            j = (i + 1) % k
            faces.append((i, j, k + j, k + i))
        if k <= 4:
            faces += [tuple(reversed(range(k))), tuple(range(k, 2 * k))]
        else:
            cb = tuple(sum(p[c] for p in bottom) / k for c in range(3))
            ct = tuple(sum(p[c] for p in top) / k for c in range(3))
            verts += [cb, ct]
            for i in range(k):
                j = (i + 1) % k
                faces.append((2 * k, j, i)); faces.append((2 * k + 1, k + i, k + j))
        self.solid(mat, verts, faces, tag)


G = Geometry()
LAYOUT = []
configure()   # every opening with its side/pair/window/story tag; used by photo_landmarks.py


def P3(path, s, d, z):
    x, y = path.at(s, d); return (x, y, z)


def pblock(mat, path, s0, s1, d0, d1, zb, zt, tag='block'):
    """Block following the path between s0..s1; zb/zt may be callables of s (sloped arch strips)."""
    fb = zb if callable(zb) else (lambda s, v=zb: v)
    ft = zt if callable(zt) else (lambda s, v=zt: v)
    if s1 - s0 < 1e-4:
        return
    secs = []
    for s in path.samples(s0, s1):
        b, t = fb(s), ft(s)
        if t - b < 1e-3:
            t = b + 1e-3
        secs.append([P3(path, s, d0, b), P3(path, s, d1, b), P3(path, s, d1, t), P3(path, s, d0, t)])
    G.sweep(mat, secs, tag)


def szpoly(mat, path, poly, d0, d1, tag='piece'):
    G.extrude(mat, [P3(path, s, d0, z) for s, z in poly], [P3(path, s, d1, z) for s, z in poly], tag)


def xyprism(mat, poly, z0, z1, tag='prism'):
    G.extrude(mat, [(x, y, z0) for x, y in poly], [(x, y, z1) for x, y in poly], tag)


def ring(mat, path, z0, z1, d_in, d_out, tag='ring'):
    secs = [[P3(path, s, d_in, z0), P3(path, s, d_out, z0), P3(path, s, d_out, z1), P3(path, s, d_in, z1)]
            for s in path.s]
    G.sweep(mat, secs, tag, loop=True)


def slab(mat, path, z0, z1, d, tag='slab'):
    G.extrude(mat, [P3(path, s, d, z0) for s in path.s], [P3(path, s, d, z1) for s in path.s], tag)


def cylinder(mat, center, r, z0, z1, segs=16, tag='column'):
    circ = [(center[0] + r * math.cos(2 * math.pi * k / segs), center[1] + r * math.sin(2 * math.pi * k / segs))
            for k in range(segs)]
    xyprism(mat, circ, z0, z1, tag)


def roundel(mat, path, s, z, r_out, d0, d1, r_in=0.0, segs=16, tag='roundel'):
    """Disc (r_in=0) or wreath annulus in the facade plane at s; built in the tangent frame."""
    (px, py), t, n = path.frame(s)
    def pt(r, a, d):
        return (px + t[0] * r * math.cos(a) + n[0] * d, py + t[1] * r * math.cos(a) + n[1] * d, z + r * math.sin(a))
    angs = [2 * math.pi * k / segs for k in range(segs)]
    if r_in <= 0:
        G.extrude(mat, [pt(r_out, a, d0) for a in angs], [pt(r_out, a, d1) for a in angs], tag)
    else:
        secs = [[pt(r_in, a, d0), pt(r_out, a, d0), pt(r_out, a, d1), pt(r_in, a, d1)] for a in angs]
        G.sweep(mat, secs, tag, loop=True)


def on_straight(path, s0, s1):
    f0, f1 = path.feature_at(s0), path.feature_at(s1)
    return f0 is not None and f0 is f1 and f0['kind'] == 'side'


# ---------------------------------------------------------------- facade pieces
def pier(path, s0, s1, zb, zt, mat, style):
    """Wall between openings: dark core plus stone courses separated by channels."""
    if s1 - s0 < 0.02:
        return
    ch, h = {'rustic': (.07, .52), 'rustic_t': (.055, .48), 'course': (.035, .64), 'plain': (.04, 0)}[style]
    pblock(MORTAR, path, s0, s1, D0, -ch, zb, zt, 'pier core')
    if h == 0:
        pblock(mat, path, s0, s1, -ch - .015, 0, zb + .03, zt - .03, 'pier face')
        return
    n = max(1, round((zt - zb) / h)); step = (zt - zb) / n; g = .06 if style.startswith('rustic') else .045
    for j in range(n):
        pblock(mat, path, s0, s1, -ch - .015, 0, zb + j * step + g / 2, zb + (j + 1) * step - g / 2, 'pier course')


def sash(path, s0, s1, zb, zt, mat, sill=True, hood=True, meeting=True):
    pblock(GLASS, path, s0, s1, -RECESS - .01, -RECESS + .03, zb, zt, 'glass')
    fw = .085
    pblock(FRAME, path, s0 - .01, s0 + fw, -RECESS - .01, -.19, zb, zt, 'frame')
    pblock(FRAME, path, s1 - fw, s1 + .01, -RECESS - .01, -.19, zb, zt, 'frame')
    pblock(FRAME, path, s0 + fw, s1 - fw, -RECESS - .01, -.19, zt - fw, zt + .01, 'frame')
    pblock(FRAME, path, s0 + fw, s1 - fw, -RECESS - .01, -.19, zb - .01, zb + .11, 'frame')
    if meeting:
        zm = zb + (zt - zb) * .52
        pblock(FRAME, path, s0 + fw, s1 - fw, -RECESS - .01, -.215, zm - .035, zm + .035, 'meeting rail')
    if sill:
        pblock(mat, path, s0 - .09, s1 + .09, -RECESS - .01, .075, zb - .11, zb + .015, 'sill')
    if hood:
        pblock(mat, path, s0 - .12, s1 + .12, -.025, .055, zt + .05, zt + .26, 'lintel')


def arch_head(path, s0, s1, spring, mat, top, glass_bottom, frame=True, keystone_top=None):
    """Round head over an opening: arched spandrel strips, glass fan, frame and voussoir band."""
    r = (s1 - s0) / 2; c = (s0 + s1) / 2; K = 12
    arc = lambda s: spring + math.sqrt(max(r * r - (s - c) ** 2, 0.0))
    xs = [s0 + (s1 - s0) * k / K for k in range(K + 1)]
    for a, b in zip(xs, xs[1:]):
        za, zb_ = arc(a), arc(b)
        pblock(mat, path, a, b, D0, 0, lambda s, a=a, b=b, za=za, zb_=zb_: za + (zb_ - za) * (s - a) / (b - a), top, 'arch spandrel')
        pblock(GLASS, path, a, b, -RECESS - .01, -RECESS + .03, glass_bottom,
               lambda s, a=a, b=b, za=za, zb_=zb_: za + (zb_ - za) * (s - a) / (b - a) + .03, 'glass')
    angs = [math.pi * k / K for k in range(K + 1)]
    for a0, a1 in zip(angs, angs[1:]):
        if frame:
            q = [(c + r * math.cos(a0), spring + r * math.sin(a0)), (c + r * math.cos(a1), spring + r * math.sin(a1)),
                 (c + (r - .09) * math.cos(a1), spring + (r - .09) * math.sin(a1)),
                 (c + (r - .09) * math.cos(a0), spring + (r - .09) * math.sin(a0))]
            szpoly(FRAME, path, q, -RECESS - .01, -.19, 'arch frame')
        q = [(c + (r + .21) * math.cos(a0), spring + (r + .21) * math.sin(a0)),
             (c + (r + .21) * math.cos(a1), spring + (r + .21) * math.sin(a1)),
             (c + (r - .01) * math.cos(a1), spring + (r - .01) * math.sin(a1)),
             (c + (r - .01) * math.cos(a0), spring + (r - .01) * math.sin(a0))]
        szpoly(mat, path, q, -.03, .05, 'voussoir')
    kt = keystone_top if keystone_top is not None else spring + r + .36
    szpoly(mat, path, [(c - .15, spring + r - .06), (c + .15, spring + r - .06), (c + .21, kt), (c - .21, kt)],
           -.03, .09, 'keystone')
    return arc


def opening(path, o, story_top):
    s0, s1, kind, zb, zt, mat = o['s0'], o['s1'], o['kind'], o['zb'], o['zt'], o['mat']
    zf = o['zf']
    if kind == 'oriel':
        return
    if zb > zf + .01:
        pblock(mat, path, s0, s1, D0, 0, zf, zb, 'spandrel')
    if kind in ('sash', 'square'):
        sash(path, s0, s1, zb, zt, mat, meeting=kind == 'sash', hood=kind == 'sash' and o['hood'])
        pblock(mat, path, s0, s1, D0, 0, zt, story_top, 'spandrel')
    elif kind == 'twin':
        mid = (s0 + s1) / 2
        sash(path, s0, mid - .11, zb, zt, mat, sill=False, hood=False)
        sash(path, mid + .11, s1, zb, zt, mat, sill=False, hood=False)
        pblock(FRAME, path, mid - .12, mid + .12, -RECESS - .01, -.12, zb, zt, 'mullion')
        pblock(mat, path, s0 - .1, s1 + .1, -RECESS - .01, .08, zb - .12, zb + .015, 'sill')
        if o['hood']:
            pblock(mat, path, s0 - .14, s1 + .14, -.025, .06, zt + .05, zt + .3, 'lintel')
        pblock(mat, path, s0, s1, D0, 0, zt, story_top, 'spandrel')
    elif kind in ('store', 'door'):
        pblock(GLASS, path, s0, s1, -RECESS - .01, -RECESS + .03, zb, zt, 'glass')
        fw = .12
        for a, b in ((s0 - .01, s0 + fw), (s1 - fw, s1 + .01)):
            pblock(FRAME, path, a, b, -RECESS - .01, -.17, zb, zt, 'frame')
        pblock(FRAME, path, s0 + fw, s1 - fw, -RECESS - .01, -.17, zt - fw, zt + .01, 'frame')
        pblock(FRAME, path, s0 + fw, s1 - fw, -RECESS - .01, -.17, zb - .01, zb + .5 if kind == 'store' else zb + .12, 'kick panel')
        zr = zb + (zt - zb) * .74
        pblock(FRAME, path, s0 + fw, s1 - fw, -RECESS - .01, -.18, zr - .06, zr + .06, 'transom bar')
        mid = (s0 + s1) / 2
        pblock(FRAME, path, mid - .05, mid + .05, -RECESS - .01, -.18, zb + .12, zr - .06, 'mullion')
        pblock(mat, path, s0, s1, D0, 0, zt, story_top, 'spandrel')
    elif kind == 'arched':
        r = (s1 - s0) / 2; spring = zt - r
        sash(path, s0, s1, zb, spring, mat, hood=False)
        arch_head(path, s0, s1, spring, mat, story_top, spring - .02, keystone_top=story_top + .03)
    elif kind in ('arcade', 'arcade1'):
        r = (s1 - s0) / 2; spring = zt - r; z19 = Z[19]
        pblock(GLASS, path, s0, s1, -RECESS - .01, -RECESS + .03, zb, spring, 'glass')
        fw = .1
        pblock(FRAME, path, s0 - .01, s0 + fw, -RECESS - .01, -.18, zb, spring, 'frame')
        pblock(FRAME, path, s1 - fw, s1 + .01, -RECESS - .01, -.18, zb, spring, 'frame')
        pblock(FRAME, path, s0 + fw, s1 - fw, -RECESS - .01, -.18, zb - .01, zb + .12, 'frame')
        pblock(FRAME, path, s0 + fw, s1 - fw, -RECESS - .01, -.15, z19 - .38, z19 + .48, 'metal spandrel')
        pblock(FRAME, path, s0 + fw, s1 - fw, -RECESS - .01, -.19, spring - .05, spring + .05, 'transom bar')
        for k in ((1, 2) if kind == 'arcade' else ()):
            m = s0 + (s1 - s0) * k / 3
            pblock(FRAME, path, m - .05, m + .05, -RECESS - .01, -.19, zb + .1, spring + .02, 'mullion')
        for zz in ((zb + z19 - .38) / 2, (z19 + .48 + spring) / 2):
            pblock(FRAME, path, s0 + fw, s1 - fw, -RECESS - .01, -.21, zz - .03, zz + .03, 'meeting rail')
        pblock(mat, path, s0 - .1, s1 + .1, -RECESS - .01, .08, zb - .12, zb + .015, 'sill')
        arch_head(path, s0, s1, spring, mat, story_top, spring - .02, keystone_top=story_top + .03)
    elif kind == 'loggia':
        pblock(GLASS, path, s0, s1, -RECESS - .01, -RECESS + .03, zb, zt, 'glass')
        n = max(2, round((s1 - s0) / .6))
        for k in range(n + 1):
            m = s0 + (s1 - s0) * k / n
            pblock(FRAME, path, max(s0 - .01, m - .05), min(s1 + .01, m + .05), -RECESS - .01, -.18, zb, zt, 'mullion')
        for zz in (zb + .06, Z[19] - .1, Z[19] + .1, zt - .06):
            pblock(FRAME, path, s0, s1, -RECESS - .01, -.18, zz - .07, zz + .07, 'transom bar')
        pblock(mat, path, s0, s1, D0, 0, zt, story_top, 'spandrel')


# ---------------------------------------------------------------- building
def side_slots(path):
    """Window centres per side: nine/four pairs at documented column spacing, wider end piers."""
    slots = {}
    for f in path.features:
        if f['kind'] != 'side':
            continue
        L = f['s1'] - f['s0']; n = PAIRS[f['name']]
        P = PARAMS['pitch_' + f['name']]
        if L - n * P < 1.2:
            P = (L - 1.2) / n
        e = (L - n * P) / 2
        m = PARAMS.get('prow_margin_' + f['name'])
        if m is not None:            # margin at the prow end: start of Fifth, end of Broadway
            e = m if f['name'] == 'Fifth' else L - n * P - m
        slots[f['name']] = [f['s0'] + e + P * (k + .5) for k in range(n)]
    return slots


def build():
    path = footprint()
    feats = {f['name']: f for f in path.features}
    pairs = side_slots(path)
    story_top = lambda n: Z[20] if n == 18 else Z[n + 1]
    oriels = []
    stories = [n for n in range(1, 21) if n != 19]
    for n in stories:
        zf = Z[n]; top = story_top(n)
        mat = LIME if n <= 3 else TERRA
        if n == 1:
            zb, zt = .35, Z[2] - 1.15
        elif n in (2, 3):
            zb, zt = zf + .75, top - .6
        elif n == 4:
            zb, zt = zf + .7, top - .85
        elif n == 16:
            zb, zt = zf + .72, top - .42
        elif n == 17:
            zb, zt = zf + .8, top - .75
        elif n == 18:
            zb, zt = zf + .85, top - .42
        elif n == 20:
            zb, zt = zf + 1.0, zf + 2.05
        else:
            zb, zt = zf + .72, top - .55
        ops = []
        def add_op(s0, s1, kind, zb_=None, zt_=None, tag=None):
            LAYOUT.append({'story': n, 'tag': tag, 's0': s0, 's1': s1, 'kind': kind,
                           'zb': zb if zb_ is None else zb_, 'zt': zt if zt_ is None else zt_})
            ops.append({'s0': s0, 's1': s1, 'kind': kind, 'zb': zb if zb_ is None else zb_,
                        'zt': zt if zt_ is None else zt_, 'mat': mat, 'zf': zf, 'hood': n in HOOD_STORIES})
        for side, centres in pairs.items():
            for k, c in enumerate(centres):
                half = WW + NP / 2
                if n == 1:
                    add_op(c - half, c + half, 'door' if k in ENTRANCE_PAIRS[side] else 'store',
                           0.0 if k in ENTRANCE_PAIRS[side] else None, Z[2] - 1.4 if k in ENTRANCE_PAIRS[side] else None, (side, k, 'pair'))
                elif n == 2 and k in ENTRANCE_PAIRS[side] and side != '22nd':
                    pass   # oculus above the entrance: solid wall, ornament added below
                elif n in (2, 3):
                    add_op(c - half, c + half, 'twin', tag=(side, k, 'pair'))
                elif n == 18:
                    add_op(c - half, c + half, 'arcade', tag=(side, k, 'pair'))
                elif 7 <= n <= 14 and k in ORIEL_PAIRS.get(side, []):
                    add_op(c - half - .15, c + half + .15, 'oriel', tag=(side, k, 'pair'))
                    if n == 7:
                        oriels.append((side, c - half - .15, c + half + .15))
                else:
                    kind = 'arched' if n == 16 else 'square' if n == 20 else 'sash'
                    w = .95 if n == 20 else WW
                    for j, x in enumerate((c - (WW + NP) / 2, c + (WW + NP) / 2)):
                        add_op(x - w / 2, x + w / 2, kind, tag=(side, k, j))
        for name in ('SW', 'SE'):
            f = feats[name]; c = (f['s0'] + f['s1']) / 2
            w = 1.4 if n == 1 else .95 if n == 20 else 1.15
            kind = {1: 'door', 18: 'arcade1', 16: 'arched', 20: 'square'}.get(n, 'sash')
            add_op(c - w / 2, c + w / 2, kind, 0.0 if n == 1 else None, Z[2] - 1.4 if n == 1 else None, (name, 0, 0))
        f = feats['Prow']; c = (f['s0'] + f['s1']) / 2
        if n == 1:
            add_op(c - .7, c + .7, 'store', tag=('Prow', 0, 1))
        elif n == 18:
            add_op(f['s0'] + .22, f['s1'] - .22, 'loggia', zf + .25, top - .3, ('Prow', 0, 1))
        elif n == 20:
            add_op(c - .4, c + .4, 'square', tag=('Prow', 0, 1))
        else:
            kind = 'arched' if n == 16 else 'sash'
            for j, (x, w) in enumerate(((c - .93, .55), (c, .8), (c + .93, .55))):
                add_op(x - w / 2, x + w / 2, kind, tag=('Prow', 0, j))
        ops.sort(key=lambda o: o['s0'])
        if LAYOUT_ONLY:
            continue
        for o in ops:
            opening(path, o, top)
        # piers fill every gap between openings around the closed path
        style = ('rustic' if n <= 3 else 'plain' if n in (4, 16, 17, 18, 20) else
                 'rustic_t' if n == 15 else 'course')
        for a, b in zip(ops, ops[1:] + [dict(ops[0], s0=ops[0]['s0'] + path.S)]):
            s0, s1 = a['s1'], b['s0']
            if s1 - s0 < -1e-6:
                raise ValueError(f'overlapping openings on story {n} at s={s0:.2f}')
            pier(path, s0, s1, zf, top, mat, style)
            pier_ornament(path, n, s0, s1, zf, top, mat)
    if LAYOUT_ONLY:
        return path
    # oculus windows above the Fifth/Broadway entrances
    for side in ('Fifth', 'Broadway'):
        for k in ENTRANCE_PAIRS[side]:
            c = pairs[side][k]; zc = (Z[2] + Z[3]) / 2 + .1
            roundel(GLASS, path, c, zc, .62, -.03, .02, segs=20, tag='oculus glass')
            roundel(LIME, path, c, zc, .92, -.02, .13, r_in=.6, segs=20, tag='oculus frame')
            for x in (c - 1.12, c + 1.12):
                pblock(LIME, path, x - .14, x + .14, -.02, .24, zc - .55, zc + .3, 'console')
            # entrance: fluted engaged columns and entablature
            half = WW + NP / 2
            for x in (c - half - .27, c + half + .27):
                (px, py), t, nn = path.frame(x)
                cylinder(LIME, (px + nn[0] * .1, py + nn[1] * .1), .34, 0.0, Z[2] - 1.18, tag='engaged column')
            pblock(LIME, path, c - half - .75, c + half + .75, -.05, .45, Z[2] - 1.2, Z[2] - .25, 'entablature')
            for x in (c - 1.3, c, c + 1.3):
                roundel(LIME, path, x, Z[2] - .73, .2, .43, .52, tag='entablature roundel')
    building_rings(path)
    for side, a, b in oriels:
        oriel(path, a, b)
    prow_columns(path, feats['Prow'])
    roof_and_site(path)
    return path


def pier_ornament(path, n, s0, s1, zf, top, mat):
    w = s1 - s0; c = (s0 + s1) / 2
    if n not in (4, 17, 18, 20) or not on_straight(path, s0, s1):
        return
    wide = w > 1.25
    if n == 4:
        if wide:
            zc = (zf + top) / 2 - .15
            roundel(mat, path, c, zc, .56, -.01, .11, r_in=.36, tag='wreath')
            roundel(mat, path, c, zc, .3, -.01, .08, tag='wreath tablet')
        else:
            pblock(mat, path, c - .18, c + .18, -.01, .07, zf + .9, top - 1.2, 'pier panel')
            roundel(mat, path, c, top - 1.55, .17, .05, .13, tag='pier boss')
    elif n == 17:
        zc = (zf + top) / 2
        if wide:
            roundel(mat, path, c, zc, .42, -.01, .1, r_in=.26, tag='roundel')
            roundel(mat, path, c, zc, .24, -.01, .07, tag='roundel boss')
        else:
            pblock(mat, path, c - .17, c + .17, -.01, .1, zc - .22, zc + .2, "lion's head")
            roundel(mat, path, c, zc + .02, .13, .08, .17, tag="lion's head")
    elif n == 18 and wide:
        pw = min(.9, w - .3)
        spring = Z[20] - .42 - (2 * WW + NP) / 2
        pblock(mat, path, c - pw / 2, c + pw / 2, -.02, .12, zf + .25, spring - .25, 'pilaster')
        pblock(mat, path, c - pw / 2 - .15, c + pw / 2 + .15, -.02, .26, spring - .25, spring + .25, 'capital')
        roundel(mat, path, c, spring + 1.05, .45, -.01, .1, r_in=.28, tag='wreath')
        roundel(mat, path, c, spring + 1.05, .27, -.01, .08, tag='mask')
    elif n == 20:
        xs = [c] if w < 1.25 else [c - w / 4, c + w / 4]
        for x in xs:
            for dx in (-.14, 0, .14):
                pblock(mat, path, x + dx - .045, x + dx + .045, -.01, .08, zf + .75, zf + 2.3, 'triglyph')


def building_rings(path):
    core_in = D0 - .04
    slab(MORTAR, path, 0.0, ROOF, -RECESS, 'core')
    rings = [  # (z0, z1, projection, material)
        (Z[2] - 1.1, Z[2] - .85, .2, LIME), (Z[2] - .85, Z[2] - .35, .12, LIME), (Z[2] - .35, Z[2] - .15, .36, LIME), (Z[2] - .15, Z[2] + .15, .58, LIME),
        (Z[3] - .1, Z[3] + .08, .09, LIME),
        (Z[4] - .45, Z[4] - .15, .1, LIME), (Z[4] - .15, Z[4] + .1, .3, LIME),
        (Z[5] - .8, Z[5] - .28, .06, TERRA), (Z[5] - .28, Z[5] - .05, .22, TERRA), (Z[5] - .05, Z[5] + .15, .38, TERRA),
        (Z[7] - .5, Z[7] + .05, .05, TERRA), (Z[7] + .05, Z[7] + .3, .19, TERRA),
        (Z[15] - .1, Z[15] + .15, .14, TERRA), (Z[16] - .08, Z[16] + .1, .07, TERRA),
        (Z[17] - .05, Z[17] + .18, .2, TERRA), (Z[17] + .18, Z[17] + .36, .4, TERRA),
        (Z[18] - .3, Z[18] - .05, .25, TERRA), (Z[18] - .05, Z[18] + .25, .55, TERRA), (Z[18] + .25, Z[18] + .4, .35, TERRA),
        (Z[20] - .25, Z[20] + .05, .22, TERRA), (Z[20] + .05, Z[20] + .2, .12, TERRA),
        # main cornice (projects 1.70 m ~ 5.5 ft)
        (Z[21], Z[21] + .2, .2, TERRA), (Z[21] + .2, Z[21] + .45, .3, TERRA), (Z[21] + .45, Z[21] + .62, .48, TERRA),
        (Z[21] + 1.2, Z[21] + 1.72, 1.7, TERRA), (Z[21] + 1.72, Z[21] + 1.95, 1.62, TERRA), (Z[21] + 1.95, ROOF, 1.5, TERRA),
    ]
    for n in (6, 8, 9, 10, 11, 12, 13, 14):
        rings.append((Z[n] - .08, Z[n] + .1, .07, TERRA))
    for z0, z1, d, m in rings:
        ring(m, path, z0, z1, core_in, d, 'belt/cornice ring')
    # dentils above the 3rd story and under the main cornice; roundel frieze above the 4th
    def around(step, fn):
        n = int(path.S / step)
        for k in range(n):
            fn(path.S * (k + .5) / n)
    around(.26, lambda s: pblock(LIME, path, s - .065, s + .065, .08, .2, Z[4] - .42, Z[4] - .18, 'dentil'))
    around(.24, lambda s: pblock(TERRA, path, s - .06, s + .06, .28, .42, Z[21] + .22, Z[21] + .43, 'dentil'))
    around(.7, lambda s: roundel(TERRA, path, s, Z[5] - .54, .18, .02, .13, segs=12, tag='frieze roundel'))
    around(.95, lambda s: pblock(TERRA, path, s - .14, s + .14, .46, 1.55, Z[21] + .6, Z[21] + 1.22, 'modillion'))
    # meander (Greek key) approximated with raised key blocks
    def key(s):
        z0, z1 = Z[7] - .45, Z[7] - .02
        pblock(TERRA, path, s - .22, s + .2, .03, .1, z1 - .09, z1, 'meander')
        pblock(TERRA, path, s + .11, s + .2, .03, .1, z0 + .09, z1 - .09, 'meander')
        pblock(TERRA, path, s - .22, s + .2, .03, .1, z0, z0 + .09, 'meander')
        pblock(TERRA, path, s - .22, s - .13, .03, .1, z0 + .09, z0 + .27, 'meander')
    around(.5, key)
    # balustrade over the cornice
    ring(TERRA, path, ROOF, ROOF + .25, .1, .9, 'balustrade plinth')
    ring(TERRA, path, ROOF + .93, ROOF + 1.15, .42, .78, 'balustrade rail')
    around(.34, lambda s: pblock(TERRA, path, s - .07, s + .07, .53, .67, ROOF + .23, ROOF + .95, 'baluster'))
    around(6.0, lambda s: pblock(TERRA, path, s - .24, s + .24, .38, .82, ROOF + .23, ROOF + 1.19, 'balustrade die'))


def oriel(path, a, b):
    """Trapezoidal oriel over the 7th-14th stories with a window on each face per story."""
    (A, t, n) = path.frame(a); D = path.at(b)
    Wb = b - a; F, c = .65, 1.0
    w = lambda x, y: (A[0] + t[0] * x + n[0] * y, A[1] + t[1] * x + n[1] * y)
    k = .4 / F
    B, C = w(c, F), w(Wb - c, F)
    faces = [Path.line(w(-c * k, -F * k), B), Path.line(B, C), Path.line(C, w(Wb + c * k, -F * k))]
    widths = [.62, 1.25, .62]
    z0, z1 = Z[7], Z[15]
    for face, width in zip(faces, widths):
        vis0 = 0.0 if face is faces[1] else (face.S - math.hypot(c, F) if face is faces[0] else 0.0)
        vis1 = face.S if face is not faces[2] else math.hypot(c, F)
        mid = (vis0 + vis1) / 2
        for st in range(7, 15):
            zf, top = Z[st], Z[st + 1]
            zb, zt = zf + .72, top - .55
            s0, s1 = mid - width / 2, mid + width / 2
            pblock(TERRA, face, s0, s1, D0, 0, zf, zb, 'oriel spandrel')
            sash(face, s0, s1, zb, zt, TERRA, hood=False)
            pblock(TERRA, face, s0, s1, D0, 0, zt, top, 'oriel spandrel')
            pier(face, 0.0, s0, zf, top, TERRA, 'course')
            pier(face, s1, face.S, zf, top, TERRA, 'course')
    # mitred corner posts fill the wedge between face blocks at the two convex corners
    for P, fa, fb in ((B, faces[0], faces[1]), (C, faces[1], faces[2])):
        na, nb = fa.n[0], fb.n[0]
        m = unit(add(na, nb)); miter = -D0 / dot(m, na)
        xyprism(TERRA, [P, add(P, mul(na, D0)), add(P, mul(m, -miter)), add(P, mul(nb, D0))], z0, z1, 'oriel corner post')
    inner = [(face.at(0, -RECESS), unit(sub(face.p[1], face.p[0]))) for face in faces]
    base_line = (w(0, -.5), t)
    core = [lines_intersect(*inner[0], *base_line), lines_intersect(*inner[0], *inner[1]),
            lines_intersect(*inner[1], *inner[2]), lines_intersect(*inner[2], *base_line)]
    xyprism(MORTAR, core, z0, z1, 'oriel core')
    outline = [w(-c * k, -F * k), B, C, w(Wb + c * k, -F * k)]
    for st in range(8, 15):
        xyprism(TERRA, offset_convex(outline, .07), Z[st] - .08, Z[st] + .1, 'oriel band')
    base = offset_convex(outline, .06)
    low = [w(x_, y_ * .12 - .25) for x_, y_ in [(-c * k, -F * k), (c, F), (Wb - c, F), (Wb + c * k, -F * k)]]
    G.extrude(TERRA, [(x, y, z0 - .5) for x, y in offset_convex(low, .02)], [(x, y, z0 + .03) for x, y in base], 'oriel corbel')
    xyprism(TERRA, offset_convex(outline, .17), z1 - .03, z1 + .32, 'oriel hood')
    xyprism(TERRA, offset_convex(outline, .26), z1 + .32, z1 + .46, 'oriel hood')


def prow_columns(path, f):
    c = (f['s0'] + f['s1']) / 2
    for x in (c - .8, c + .8):
        (px, py), t, n = path.frame(x)
        cylinder(LIME, (px + n[0] * .15, py + n[1] * .15), .33, 0.0, Z[3], tag='prow column')
        xyprism(LIME, [(px + n[0] * .15 + dx, py + n[1] * .15 + dy) for dx, dy in ((-.45, -.45), (.45, -.45), (.45, .45), (-.45, .45))],
                Z[3] - .02, Z[3] + .4, 'prow column capital')
    for x in (c - .75, c + .75):
        (px, py), t, n = path.frame(x)
        ctr = (px + n[0] * .02, py + n[1] * .02)
        cylinder(TERRA, ctr, .28, Z[18] + .38, Z[20] - .23, tag='loggia column')
        xyprism(TERRA, [(ctr[0] + dx, ctr[1] + dy) for dx, dy in ((-.36, -.36), (.36, -.36), (.36, .36), (-.36, .36))],
                Z[20] - .6, Z[20] - .2, 'loggia capital')


def roof_and_site(path):
    slab(ROOFM, path, ROOF - .02, ROOF + .08, -RECESS - .05, 'roof')
    attic = footprint(inset=1.0, trim_prow=1.0)
    top = ROOF + 3.0     # attic: original 285 ft top
    slab(TERRA, attic, ROOF + .06, top, 0.0, 'attic')
    slab(ROOFM, attic, top - .02, top + .1, -.1, 'attic roof')
    # 1905 penthouse, set back over the broad southern part of the roof (extent estimated)
    ph = footprint(inset=4.0)
    poly = clip_y([ph.at(s) for s in ph.s], 8.0)
    xyprism(TERRA, poly, top + .08, top + 3.4, 'penthouse')
    xyprism(ROOFM, offset_convex(poly, .15), top + 3.38, top + 3.6, 'penthouse roof')
    slab(WALK, footprint(), -.3, 0.0, 3.2, 'sidewalk')
    xyprism(ASPHALT, [(-90, -90), (90, -90), (90, 90), (-90, 90)], -.46, -.3, 'asphalt')


def stats():
    return {'materials': {m: {'vertices': len(G.v[m]), 'faces': len(G.f[m])} for m in G.v},
            'vertices': sum(len(v) for v in G.v.values()), 'faces': sum(len(f) for f in G.f.values()),
            'elements': sum(G.count.values()), 'element_kinds': dict(G.count)}


def blender_main(out):
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for mname in G.v:
        col, rough, metal = MATERIALS[mname]
        m = bpy.data.materials.new(mname); m.use_nodes = True; m.diffuse_color = (*col, 1)
        bs = next(nd for nd in m.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED')
        bs.inputs['Base Color'].default_value = (*col, 1); bs.inputs['Roughness'].default_value = rough
        bs.inputs['Metallic'].default_value = metal
        mesh = bpy.data.meshes.new(mname); mesh.from_pydata(G.v[mname], [], G.f[mname]); mesh.update()
        ob = bpy.data.objects.new(mname, mesh); scene.collection.objects.link(ob); ob.data.materials.append(m)
    scene['reconstruction_status'] = 'Build-4 reference-guided approximation; documented dimensions, estimated details. Not a survey.'
    scene['references'] = json.dumps(REFERENCES)
    world = bpy.data.worlds.new('Soft blue sky'); world.use_nodes = True
    bg = next(nd for nd in world.node_tree.nodes if nd.type == 'BACKGROUND')
    bg.inputs[0].default_value = (.55, .68, .85, 1); bg.inputs[1].default_value = .45; scene.world = world
    os.makedirs(out, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, 'flatiron_v5.blend'))


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default='outputs/build6'); ap.add_argument('--dry', action='store_true')
    ap.add_argument('--v4', action='store_true', help='use the build-4 dimensions')
    args = ap.parse_args(argv)
    params_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'build6', 'geometry-params.json')
    if os.path.exists(params_file) and not args.v4:
        configure(json.load(open(params_file))['params'])
    p = build()
    st = stats(); st['footprint'] = [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in f.items() if k in ('name', 'kind', 's0', 's1', 'r')} for f in p.features]
    print(json.dumps({k: st[k] for k in ('vertices', 'faces', 'elements')}), flush=True)
    if not args.dry:
        blender_main(args.out)
        with open(os.path.join(args.out, 'flatiron_v5-stats.json'), 'w') as fh:
            json.dump(st, fh, indent=2)
        print('SAVED', os.path.join(args.out, 'flatiron_v5.blend'), flush=True)
