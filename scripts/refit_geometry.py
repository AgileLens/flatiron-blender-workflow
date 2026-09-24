"""Refit the Flatiron model's dimensions from the solved reference-photo cameras (build 6).

Joint least squares over geometry parameters + every used photo's camera, on the build-5 FIT points
only (held-out points are never used). Guards against overfitting:
  * every parameter has a prior (surveyed lot dimensions tight, estimates looser), 1 sigma = 10 px;
  * leave-one-photo-out refits: a change that one photo alone drives is shrunk halfway and flagged;
  * each photo is also scored with geometry fitted WITHOUT it (true out-of-sample check).
Writes docs/build6/refit-report.json (diagnostic). The build-6 decision is made by
select_geometry_changes.py, which writes docs/build6/geometry-params.json.
  python3 scripts/refit_geometry.py
"""
import json, math, os, sys, time
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import landmarks_v5, flatiron_v5 as F
from solve_photo_cameras import solve, project

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CORR = json.load(open(os.path.join(ROOT, 'docs/build6/correspondences.json')))
CAMS5 = json.load(open(os.path.join(ROOT, 'docs/build5/photo-cameras.json')))   # as delivered in build 5
PHOTOS = [k for k, e in CORR.items() if isinstance(e, dict) and e.get('used') and e.get('points')]
NAMES = sorted({p['name'] for k in PHOTOS for p in CORR[k]['points']})

# v4 prow-end margins (centred layout) so the prior starts exactly at build 4
F.configure(); F.LAYOUT_ONLY = True; _path = F.build(); F.LAYOUT_ONLY = False
_feats = {f['name']: f for f in _path.features}; _slots = F.side_slots(_path)
def _margin(side):
    f = _feats[side]; P = F.PARAMS['pitch_' + side]; c = _slots[side]
    return (c[0] - P / 2 - f['s0']) if side == 'Fifth' else (f['s1'] - (c[-1] + P / 2))
V4 = dict(F.V4_PARAMS, prow_margin_Fifth=_margin('Fifth'), prow_margin_Broadway=_margin('Broadway'))
PRIORS = {  # name: (mean, sigma, why)
    'lot_fifth': (V4['lot_fifth'], .3, 'surveyed lot, 197.5 ft'), 'lot_22nd': (V4['lot_22nd'], .3, 'surveyed lot, 86 ft'),
    'sw_angle_deg': (90.0, 1.0, 'lot is a near-right triangle (89.3 deg from the three frontages)'),
    'r_prow': (V4['r_prow'], .6, 'prow about 2 m wide'), 'r_sw': (V4['r_sw'], .6, 'estimate'), 'r_se': (V4['r_se'], .6, 'estimate'),
    'pitch_Fifth': (V4['pitch_Fifth'], .3, '17 ft column spacing + 0.35 m'), 'pitch_Broadway': (V4['pitch_Broadway'], .3, '18.5 ft + 0.35 m'),
    'prow_margin_Fifth': (V4['prow_margin_Fifth'], 1.5, 'estimate (centred layout)'),
    'prow_margin_Broadway': (V4['prow_margin_Broadway'], 1.5, 'estimate (centred layout)'),
    'ww': (V4['ww'], .15, 'estimate'), 'np': (V4['np'], .15, 'estimate'),
    'z_ground': (V4['z_ground'], .4, 'estimate'), 'h_base': (V4['h_base'], .3, 'estimate'), 'h_4': (V4['h_4'], .3, 'estimate'),
    'h_shaft': (V4['h_shaft'], .15, '13 ft'), 'h_arcade': (V4['h_arcade'], .3, 'estimate'), 'h_20': (V4['h_20'], .3, 'estimate'),
}
KEYS = list(PRIORS)
_CAMS0 = None
def cams0():
    """Starting cameras: each photo re-solved on the build-4 geometry with the build-6 point set."""
    global _CAMS0
    if _CAMS0 is None:
        th = np.array([V4[k] for k in KEYS]); lm = landmarks_v5.compute(NAMES, params_of(th))
        _CAMS0 = {p: solve(CORR[p], lm=lm, trials=24) for p in PHOTOS}
    return _CAMS0
TOTAL = (86.9, 1.5)            # 285 ft to the top of the original attic (roof + 3 m in the model)
PX_PER_SIGMA = 10.0


def params_of(theta):
    return dict(zip(KEYS, map(float, theta)))


_cache = {}
def lm_of(theta):
    key = tuple(np.round(theta, 9))
    if key not in _cache:
        if len(_cache) > 4000:
            _cache.clear()
        _cache[key] = landmarks_v5.compute(NAMES, params_of(theta))
    return _cache[key]


def cam_block(photo, cam):
    e = CORR[photo]; R = np.array(cam['R_world_to_camera_rdf'])
    x = list(Rotation.from_matrix(R).as_rotvec()) + list(cam['C'])
    if not e.get('focal_px'):
        x.append(math.log(cam['focal_px']))
    return x


def unpack_cam(photo, x):
    e = CORR[photo]
    f = e['focal_px'] if e.get('focal_px') else math.exp(x[6])
    return Rotation.from_rotvec(x[:3]).as_matrix(), np.array(x[3:6]), f


def joint_fit(photos, theta0, cams0):
    sizes = [7 if not CORR[p].get('focal_px') else 6 for p in photos]
    x0 = np.concatenate([theta0] + [cam_block(p, cams0[p]) for p in photos])
    mu = np.array([PRIORS[k][0] for k in KEYS]); sd = np.array([PRIORS[k][1] for k in KEYS])

    def resid(x):
        theta = x[:len(KEYS)]; lm = lm_of(theta); out = []; i = len(KEYS)
        for p, n in zip(photos, sizes):
            e = CORR[p]; R, C, f = unpack_cam(p, x[i:i + n]); i += n
            fit = [q for q in e['points'] if not q.get('holdout')]
            X = np.array([lm[q['name']] for q in fit]); uv = np.array([q['uv'] for q in fit], float)
            pr, depth = project(R, C, f, e['size'][0], e['size'][1], X)
            out.append((pr - uv).ravel()); out.append(100 * np.minimum(depth, 1.0) - 100)
            if e.get('height_prior'):
                m, s = e['height_prior']; out.append([10 * (C[2] - m) / s])
        out.append(PX_PER_SIGMA * (theta - mu) / sd)
        P = params_of(theta); total = (P['z_ground'] + 2 * P['h_base'] + P['h_4'] + 13 * P['h_shaft'] + 2 * P['h_arcade'] + P['h_20'] + 2.05 + 3.0)
        out.append([PX_PER_SIGMA * (total - TOTAL[0]) / TOTAL[1]])
        return np.concatenate(out)

    sol = least_squares(resid, x0, loss='soft_l1', f_scale=8.0, xtol=1e-12, ftol=1e-12, gtol=1e-12, max_nfev=2000, diff_step=1e-7)
    return sol.x[:len(KEYS)], sol


def score(theta, photos=None):
    """Re-solve each photo's camera alone on its fit points against geometry theta (the build-5 protocol)."""
    lm = lm_of(np.asarray(theta)); rows = {}
    for p in photos or PHOTOS:
        r = solve(CORR[p], lm=lm, trials=12)
        rows[p] = {'fit_rmse_px': r['fit_rmse_px'], 'holdout_rmse_px': r['holdout_rmse_px'], 'all_rmse_px': r['all_rmse_px'], 'camera': r}
    return rows


if __name__ == '__main__':
    t0 = time.time()
    theta_v4 = np.array([V4[k] for k in KEYS])
    before = {p: {'fit_rmse_px': cams0()[p]['fit_rmse_px'], 'holdout_rmse_px': cams0()[p]['holdout_rmse_px']} for p in PHOTOS}
    theta_all, sol = joint_fit(PHOTOS, theta_v4, cams0())
    print('joint fit', round(time.time() - t0, 1), 's; cost', round(sol.cost, 1), flush=True)
    loo = {}
    for p in PHOTOS:
        others = [q for q in PHOTOS if q != p]
        th, _ = joint_fit(others, theta_v4, cams0())
        loo[p] = {'theta': th.tolist(), 'score': {k: v for k, v in score(th, [p])[p].items() if k != 'camera'}}
        print('LOO without', p, 'held-out', round(loo[p]['score']['holdout_rmse_px'], 1), flush=True)
    # guard: shrink and flag changes that a single photo drives
    final = theta_all.copy(); flags = {}
    for j, k in enumerate(KEYS):
        mu, sd, _ = PRIORS[k]; d = theta_all[j] - mu
        if abs(d) < 0.5 * sd:
            continue
        drivers = [p for p in PHOTOS if abs(loo[p]['theta'][j] - mu) < 0.5 * abs(d)]
        if len(drivers) == 1:
            final[j] = mu + 0.5 * d; flags[k] = f'driven by {drivers[0]} alone: change shrunk to half'
    after = score(final)
    after_unguarded = score(theta_all)
    report = {'photos': PHOTOS, 'keys': KEYS, 'priors': {k: {'mean': PRIORS[k][0], 'sigma': PRIORS[k][1], 'why': PRIORS[k][2]} for k in KEYS},
              'total_height_prior_m': TOTAL, 'px_per_sigma': PX_PER_SIGMA,
              'theta_v4': dict(zip(KEYS, theta_v4.tolist())), 'theta_joint': dict(zip(KEYS, theta_all.tolist())),
              'theta_final': dict(zip(KEYS, final.tolist())), 'flags': flags,
              'loo_theta': {p: dict(zip(KEYS, loo[p]['theta'])) for p in PHOTOS},
              'per_photo': {p: {'before': before[p],
                                'after': {k: v for k, v in after[p].items() if k != 'camera'},
                                'after_unguarded': {k: v for k, v in after_unguarded[p].items() if k != 'camera'},
                                'out_of_sample': loo[p]['score']} for p in PHOTOS},
              'seconds': round(time.time() - t0, 1)}
    os.makedirs(os.path.join(ROOT, 'docs/build6'), exist_ok=True)
    json.dump(report, open(os.path.join(ROOT, 'docs/build6/refit-report.json'), 'w'), indent=2)
    print('\n%-18s %8s %8s | %8s %8s | %8s' % ('photo', 'fit b5', 'hold b5', 'fit b6', 'hold b6', 'hold OOS'))
    for p in PHOTOS:
        b, a, o = before[p], after[p], loo[p]['score']
        print('%-18s %8.1f %8.1f | %8.1f %8.1f | %8.1f' % (p, b['fit_rmse_px'], b['holdout_rmse_px'], a['fit_rmse_px'], a['holdout_rmse_px'], o['holdout_rmse_px']))
    print('\nparam changes (v4 -> joint -> final):')
    for j, k in enumerate(KEYS):
        print('  %-22s %8.3f %8.3f %8.3f %s' % (k, theta_v4[j], theta_all[j], final[j], flags.get(k, '')))
