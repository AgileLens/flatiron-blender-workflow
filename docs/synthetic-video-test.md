# Controlled video-to-geometry test

A rendered Unreal walkthrough is a useful first input for [ViPE](https://github.com/nv-tlabs/vipe). It makes camera and depth errors measurable against known ground truth. It does not establish performance on phone footage.

## Capture contract

- 20 seconds, 30 fps, 1920 × 1080, continuous translational movement with overlapping views and constant focal length. Avoid pure rotation, cuts, interface overlays, motion blur and auto-exposure shifts for the first controlled arm.
- Inference input: RGB video only. Hold camera transforms, intrinsics, depth and scene meshes in a separate evaluation directory; never give them to the reconstruction process.
- Keep frame IDs and timestamps exactly aligned, record camera-to-world/world-to-camera convention, axes and world units, and distinguish optical-axis depth from ray distance.
- Include foreground seat edges and a textured wall; retain glass/reflections as a separately scored difficult region.
- Pin the Unreal scene, renderer/settings and ViPE source/model revisions. Store caches, captures and model downloads on the chosen data volume.

## Run

Use ViPE's [upstream installation instructions](https://github.com/nv-tlabs/vipe/blob/main/docs/installation.md) on a CUDA host. Its current source instructions are `conda env create -f envs/cu128.yml`, `conda activate cu128`, `uv sync`, then `uv run vipe infer YOUR_VIDEO.mp4`. Review the selected pipeline and downloaded model terms; the repository's Unik3D component has a noncommercial share-alike license. An overall Apache source license does not cover every downloaded dependency.

## Evaluate

Report raw scale drift first, then camera-centre trajectory error with rigid alignment and with similarity alignment as separate results. Similarity alignment must not hide metric-scale failure. Report depth absolute relative error and edge/occlusion failures with an explicit valid-pixel mask. Evaluate disjoint held-out viewpoints for any reconstructed surface or view synthesis. Include a repeatable short headset head translation as a distinct acceptance step.

## Current internal application

The next nominated scene is a theater seat bay. Its capture is queued behind existing demo work; no ViPE reconstruction, benchmark score or headset success is claimed in this repository.
