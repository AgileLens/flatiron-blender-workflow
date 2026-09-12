# Checking a photo-guided model

A closer image match is useful for presentation, but it does not by itself establish accurate camera position or building dimensions. Our first real-photo test makes that distinction visible.

## What we tested

We used the Chris06 2013 reference photograph (input 02 in [the photo manifest](photo-sources.json)), at 1608 × 1577 pixels. The approximate procedural model stayed fixed. Fourteen manually estimated facade-band/outline guides were frozen before fitting: eight for fitting and six held out for evaluation. These are approximate guides, not surveyed landmarks.

| Camera candidate | Training RMSE, pixels | Held-out RMSE, pixels |
|---|---:|---:|
| Adapted presentation camera | 189.5 | 196.7 |
| Fitted camera, centered principal point | 34.0 | 33.7 |
| Fitted camera, free principal point | 21.9 | 39.9 |

The free-principal fit lowered training error but increased held-out error and hit parameter bounds. The centered fit is the presentation candidate. The guides lie on two coplanar rails, so this test does not validate depth. Perturbing training guides by four pixels moved fitted camera centers by as much as 10.07 metres in the model's guessed coordinate scale. That sensitivity prevents treating the fit as a measured physical camera.

## The next geometry check

1. Select identifiable, fixed points such as window-frame corners or cornice intersections. Avoid silhouettes on rounded surfaces: the visible contour can move with viewpoint.
2. Match points on at least two differently oriented faces and at several heights. Inspect every match; repetitive windows make plausible but wrong matches easy.
3. Record each image coordinate, corresponding model point, image dimensions, confidence and uncertainty. Establish a measured dimension before making metric claims.
4. Freeze a fitting set and a separate evaluation set. Include points at differing depths in the evaluation set. Do not repeatedly tune against the same held-out points.
5. Keep geometry fixed for the first camera fit. Compare constrained intrinsics against more flexible fits, check residual patterns, and perturb annotations to measure sensitivity.
6. Render the fitted camera in Blender and verify that its projected points agree numerically with the fitting code. Then inspect the actual rendered facade, including features that were never used as guides.
7. If geometry is revised, version it as a new candidate and evaluate on fresh points or a second photograph. Preserve the original approximation as the comparison control.

Report image alignment, depth validation and metric accuracy separately. An attractive render can be a successful presentation result while measured reconstruction remains unverified.
