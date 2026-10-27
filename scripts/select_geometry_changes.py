"""Cross-validated selection of geometry changes for build 6 (companion to refit_geometry.py).

For each parameter group: joint-fit only that group (priors as in refit_geometry.py) and measure
  A. per-photo held-out RMSE (camera solved on that photo's fit points; the build-5 protocol);
  B. leave-one-photo-out RMSE: geometry fitted WITHOUT photo p, p's camera solved on all its points.
A group is accepted only if it lowers the mean of B and of A without making any photo worse by
more than 2 px on B. Accepted groups are then fitted together and re-checked.
  python3 scripts/select_geometry_changes.py
"""
import json, os, sys
import numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import refit_geometry as R
from solve_photo_cameras import solve

TH4 = np.array([R.V4[k] for k in R.KEYS])
GROUPS = {'prow radius': ['r_prow'], 'SE corner radius': ['r_se'], 'SW corner radius': ['r_sw'],
          'Broadway bays': ['pitch_Broadway', 'prow_margin_Broadway'], 'Fifth bays': ['pitch_Fifth', 'prow_margin_Fifth'],
          'window/pier widths': ['ww', 'np'], 'lot shape': ['lot_fifth', 'lot_22nd', 'sw_angle_deg'],
          'shaft story height': ['h_shaft'], 'base story heights': ['z_ground', 'h_base', 'h_4'], 'crown heights': ['h_arcade', 'h_20']}


def fit(free, photos):
    idx = [R.KEYS.index(k) for k in free]
    if not idx:
        return TH4.copy()
    sizes = [7 if not R.CORR[p].get('focal_px') else 6 for p in photos]
    x0 = np.concatenate([TH4[idx]] + [R.cam_block(p, R.cams0()[p]) for p in photos])
    mu = np.array([R.PRIORS[k][0] for k in R.KEYS]); sd = np.array([R.PRIORS[k][1] for k in R.KEYS])
    def full(x):
        t = TH4.copy(); t[idx] = x[:len(idx)]; return t
    def resid(x):
        theta = full(x); lm = R.lm_of(theta); out = []; i = len(idx)
        for p, n in zip(photos, sizes):
            e = R.CORR[p]; Rm, C, f = R.unpack_cam(p, x[i:i + n]); i += n
            pts = [q for q in e['points'] if not q.get('holdout')]
            X = np.array([lm[q['name']] for q in pts]); uv = np.array([q['uv'] for q in pts], float)
            pr, depth = R.project(Rm, C, f, e['size'][0], e['size'][1], X)
            out += [(pr - uv).ravel(), 100 * np.minimum(depth, 1.0) - 100]
            if e.get('height_prior'):
                m, s = e['height_prior']; out.append([10 * (C[2] - m) / s])
        out.append(R.PX_PER_SIGMA * (theta - mu) / sd)
        P = R.params_of(theta); total = P['z_ground'] + 2 * P['h_base'] + P['h_4'] + 13 * P['h_shaft'] + 2 * P['h_arcade'] + P['h_20'] + 5.05
        out.append([R.PX_PER_SIGMA * (total - R.TOTAL[0]) / R.TOTAL[1]])
        return np.concatenate(out)
    sol = least_squares(resid, x0, loss='soft_l1', f_scale=8.0, xtol=1e-12, ftol=1e-12, gtol=1e-12, max_nfev=2000, diff_step=1e-7)
    return full(sol.x)


def all_points_entry(p):
    e = dict(R.CORR[p]); e['points'] = [dict(q, holdout=False) for q in e['points']]; return e


def evaluate(free):
    th = fit(free, R.PHOTOS); lm = R.lm_of(th)
    A = {p: solve(R.CORR[p], lm=lm, trials=12)['holdout_rmse_px'] for p in R.PHOTOS}
    B = {}
    for p in R.PHOTOS:
        th_p = fit(free, [q for q in R.PHOTOS if q != p])
        B[p] = solve(all_points_entry(p), lm=R.lm_of(th_p), trials=12)['fit_rmse_px']
    return th, A, B


if __name__ == '__main__':
    out = {}
    base_th, A0, B0 = evaluate([])
    out['baseline (build 4 geometry)'] = {'A': A0, 'B': B0}
    accepted = []
    for g, free in GROUPS.items():
        th, A, B = evaluate(free)
        dA = np.mean(list(A.values())) - np.mean(list(A0.values())); dB = np.mean(list(B.values())) - np.mean(list(B0.values()))
        worst = max(B[p] - B0[p] for p in R.PHOTOS)
        ok = dA < 0 and dB < 0 and worst <= 2.0
        out[g] = {'free': free, 'theta': {k: th[R.KEYS.index(k)] for k in free}, 'A': A, 'B': B,
                  'delta_mean_A_px': dA, 'delta_mean_B_px': dB, 'worst_photo_B_px': worst, 'accepted': bool(ok)}
        print('%-22s dA %+.2f dB %+.2f worst %+.2f %s %s' % (g, dA, dB, worst, 'ACCEPT' if ok else 'reject',
              {k: round(th[R.KEYS.index(k)], 3) for k in free}), flush=True)
        if ok:
            accepted += free
    th, A, B = evaluate(accepted)
    out['combined accepted'] = {'free': accepted, 'theta': dict(zip(R.KEYS, th.tolist())), 'A': A, 'B': B,
                                'delta_mean_A_px': np.mean(list(A.values())) - np.mean(list(A0.values())),
                                'delta_mean_B_px': np.mean(list(B.values())) - np.mean(list(B0.values()))}
    print('combined', accepted, 'dA %+.2f dB %+.2f' % (out['combined accepted']['delta_mean_A_px'], out['combined accepted']['delta_mean_B_px']))
    for p in R.PHOTOS:
        print('  %-16s A %5.1f -> %5.1f   B %5.1f -> %5.1f' % (p, A0[p], A[p], B0[p], B[p]))
    print('mean A %.2f -> %.2f   mean B %.2f -> %.2f' % (np.mean(list(A0.values())), np.mean(list(A.values())), np.mean(list(B0.values())), np.mean(list(B.values()))))
    json.dump(out, open(os.path.join(R.ROOT, 'docs/build6/geometry-selection.json'), 'w'), indent=2, default=float)
    final = dict(R.V4); final.update({k: float(v) for k, v in out['combined accepted']['theta'].items()} if accepted else {})
    json.dump({'params': final, 'accepted_groups': [g for g in GROUPS if out[g]['accepted']],
               'decision': 'Only parameter groups that lower both within-photo held-out error and leave-one-photo-out error '
                           '(no photo worse by more than 2 px) are applied; everything else stays at the build-4 value.',
               'source': 'scripts/select_geometry_changes.py'},
              open(os.path.join(R.ROOT, 'docs/build6/geometry-params.json'), 'w'), indent=2)
