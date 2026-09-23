"""Solve a pinhole camera for each reference photo against the build-4 model (plain Python + SciPy).

OpenCV is not installed on the build machine; this is the same perspective-n-point problem
solved with scipy.optimize.least_squares (robust soft-L1 loss, several starts). Camera model:
q = R (X - C) with q = right/down/forward; u = f qx/qz + W/2, v = f qy/qz + H/2 (centred
principal point, square pixels, no distortion). Focal length comes from EXIF when the
Commons record has it, otherwise it is solved.

  python3 scripts/solve_photo_cameras.py docs/build5/correspondences.json docs/build5/photo-cameras.json
"""
import json, math, sys
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from photo_landmarks import landmark


def look_rotation(C, target):
    f = np.asarray(target, float) - C; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r)
    d = np.cross(f, r)
    return np.vstack([r, d, f])


def project(R, C, f, W, H, X):
    q = (np.asarray(X) - C) @ R.T
    return np.column_stack([f * q[:, 0] / q[:, 2] + W / 2, f * q[:, 1] / q[:, 2] + H / 2]), q[:, 2]


def solve(entry):
    W, H = entry['size']; pts = entry['points']
    X = np.array([landmark(p['name']) for p in pts]); uv = np.array([p['uv'] for p in pts], float)
    fit = np.array([not p.get('holdout', False) for p in pts])
    f_fixed = entry.get('focal_px')
    C0 = np.array(entry['init']['C'], float); R0 = look_rotation(C0, entry['init']['target'])
    f0 = f_fixed or entry['init'].get('focal_px', 1.2 * max(W, H))

    def unpack(x):
        R = Rotation.from_rotvec(x[:3]).as_matrix(); C = x[3:6]
        return R, C, (f_fixed if f_fixed else math.exp(x[6]))

    def resid(x):
        R, C, f = unpack(x)
        p, depth = project(R, C, f, W, H, X[fit])
        r = (p - uv[fit]).ravel()
        extra = []
        if entry.get('height_prior'):   # street-level photo: camera near eye height (1 sigma = 10 px)
            m, sd = entry['height_prior']; extra = [10 * (C[2] - m) / sd]
        return np.concatenate([r, 100 * np.minimum(depth, 1.0) - 100, extra])   # keep points in front

    best = None
    rng = np.random.default_rng(7)
    for trial in range(24):
        C = C0 + (rng.normal(0, 6, 3) if trial else 0)
        R = Rotation.from_matrix(look_rotation(C, np.array(entry['init']['target']) + (rng.normal(0, 4, 3) if trial else 0)))
        x0 = np.concatenate([R.as_rotvec(), C] + ([] if f_fixed else [[math.log(f0 * (1 if trial < 12 else rng.uniform(.6, 1.6)))]]))
        sol = least_squares(resid, x0, loss='soft_l1', f_scale=8.0, max_nfev=4000)
        if best is None or sol.cost < best.cost:
            best = sol
    R, C, f = unpack(best.x)
    proj, depth = project(R, C, f, W, H, X)
    err = np.linalg.norm(proj - uv, axis=1)
    rms = lambda m: float(np.sqrt(np.mean(err[m] ** 2))) if m.any() else None
    fwd = R[2]; yaw = math.degrees(math.atan2(fwd[0], fwd[1])); pitch = math.degrees(math.asin(-(-fwd[2])))
    return {'R_world_to_camera_rdf': R.tolist(), 'C': C.tolist(), 'focal_px': f, 'focal_source': 'EXIF' if f_fixed else 'solved',
            'size': [W, H], 'hfov_deg': math.degrees(2 * math.atan(W / 2 / f)), 'vfov_deg': math.degrees(2 * math.atan(H / 2 / f)),
            'heading_deg_from_north': yaw % 360, 'pitch_deg': math.degrees(math.asin(fwd[2])),
            'camera_height_m': float(C[2]), 'distance_to_prow_m': float(np.linalg.norm(C[:2] - np.array(landmark('ground/Prow'))[:2])),
            'fit_points': int(fit.sum()), 'holdout_points': int((~fit).sum()),
            'fit_rmse_px': rms(fit), 'holdout_rmse_px': rms(~fit), 'all_rmse_px': rms(np.ones_like(fit)),
            'rmse_percent_of_diagonal': float(np.sqrt(np.mean(err ** 2)) / math.hypot(W, H) * 100),
            'points': [{'name': p['name'], 'observed': p['uv'], 'projected': proj[i].round(1).tolist(),
                        'error_px': round(float(err[i]), 1), 'holdout': bool(p.get('holdout', False)), 'depth_m': round(float(depth[i]), 1)}
                       for i, p in enumerate(pts)]}


if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    data = json.load(open(src)); result = {}
    for photo, entry in data.items():
        if photo.startswith('_') or not entry.get('points'):
            continue
        r = solve(entry); r.update({k: entry[k] for k in ('used', 'why') if k in entry})
        result[photo] = r
        print(f"{photo}: fit {r['fit_rmse_px']:.1f}px holdout {r['holdout_rmse_px'] if r['holdout_rmse_px'] is None else round(r['holdout_rmse_px'],1)}px "
              f"f={r['focal_px']:.0f} ({r['focal_source']}) C={np.round(r['C'],1).tolist()} heading {r['heading_deg_from_north']:.0f} pitch {r['pitch_deg']:.1f}")
        for p in r['points']:
            print(f"    {p['error_px']:6.1f}{' H' if p['holdout'] else '  '} {p['name']}")
    json.dump(result, open(out, 'w'), indent=2)
