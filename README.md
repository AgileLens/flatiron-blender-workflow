# Photo-guided Flatiron in Blender

An editable architectural approximation built with GPT-6 Astra, Codex and live Blender MCP. Includes the accepted scene and the successful construction steps. No hidden 3D generation endpoint or photogrammetry solver was used.

![Flatiron lit render](assets/preview.png)

[Watch the 29-second showcase](https://agilelens.github.io/flatiron-blender-workflow/flatiron-showcase.mp4)

## Quickstart

In Blender's Scripting workspace, open `scripts/rebuild.py` and run it. It clears the active scene, so use a new file. The script writes the rebuilt scene and two previews under `outputs/rebuild/`. Tested baseline: Blender 5.2.1 LTS on macOS, live GUI. Headless rendering crashed on the original Mac; a live GUI process worked.

The replay is deterministic procedural Python captured from the successful MCP calls. It does not rerun a language model or guarantee what a fresh model session will produce. The accepted `.blend` is the comparison control.

## Things to Try

1. **Open `assets/flatiron_supported.blend` in Blender 5.2.1 and orbit the model** — you should see the corrected facade winding and backed medallion rings; `flatiron_accepted.blend` remains the original comparison baseline.
2. **Run `scripts/rebuild.py` in a fresh Blender GUI scene** — it should write the deterministic baseline scene and two previews under `outputs/rebuild/`.
3. **Run `scripts/rebuild_supported.py` in another fresh scene** — it should write the winding-and-medallion-support candidate under `outputs/rebuild-supported/` without replacing the baseline.
4. **Adjust a dimension or facade parameter in `scripts/flatiron_base.py`, then replay** — the generated Blender geometry should reflect the changed parameter while remaining editable.
5. **Read `docs/token-receipt.md` before quoting the experiment cost** — you should be able to distinguish model output, cached input, and supervising-model usage rather than presenting one undifferentiated token total.

## Agent workflow

Install [Blender MCP](https://github.com/ahujasid/blender-mcp) following its upstream instructions. Use a disposable Blender scene. Give the agent photos plus: “Inspect the scene. Build an approximate massing and facade model. Preserve editable geometry. Inspect overview and close-up renders, revise visible defects, save the scene, and document guessed dimensions.”

Ask for one visible revision at a time. The render camera and interactive viewport are separate: moving `scene.camera` does not necessarily change `get_viewport_screenshot`. Inspect the actual output.

## Scope and limits

**Known issue in the v0.1.0 preview:** M5 wearer review exposed inward-facing normals on many generated facade primitives. Mesh auditing traced this to mirrored local coordinates in the procedural box helper; the USDZ export preserved the source winding. Corrected USDZ candidates now pass geometry and Apple USD/ARKit checks; headset visual review is pending. The original scene and release remain the comparison baseline.

Rounded triangular footprint, 22 facade intervals, repetitive windows, facade relief and cornice. Nominal 87 m height and 80 × 32 m unrounded footprint were rough prior-knowledge estimates, not photo measurements. Ornamental sculpture is simplified. This is a visual approximation, not a measured digital twin.

The original successful pass used Astra medium. Claude Sonnet 5 supervised the wider experiment; local Qwen3-Coder 30B supported separate research. See the receipt for boundaries and failed attempts.

## Credits and reuse

Code: MIT. Generated model: CC BY-SA 4.0. Photo-derived presentation media: CC BY-SA 4.0. [Reference photo credits](docs/photo-credits.md). No private session logs or FSLA production assets are included.

Maintained by **Agile Lens**.

## Verification

A fresh Blender GUI replay completed and matched every accepted mesh vertex, polygon and material assignment across all 12 meshes. Workbench preview pixels differ with display defaults; geometric equality is not pixel-identical rendering. The lit preview is a later presentation candidate, not the original accepted Workbench image.

The distributed scene has local render/image paths sanitized; the private archived original is retained separately. Tabletop USDZ import was checked in Blender at approximately 0.403 × 0.850 × 1.014 metres including roof and sidewalk. Native runtime model loading is verified; headset appearance remains unverified.

## Showcase media

[Open the native Quick Look page](https://agilelens.github.io/flatiron-blender-workflow/) on Apple Vision Pro, or download `docs/flatiron_tabletop_supported.usdz` to Files. The page image is a Cycles render; native lighting/materials can differ.

For the video recipe, run `scripts/setup_showcase.py` in Blender after the replay, then `scripts/export_and_orbit.py` and `scripts/render_comparisons.py`. Each assumes a fresh or deliberately selected candidate scene. Outputs stay in `outputs/`. Run `python scripts/download_references.py` for the credited photos, then `python scripts/build_showcase_video.py --photos outputs/references`. The video composer requires FFmpeg with libfreetype/drawtext and libx264; on macOS use `ffmpeg-full` and pass its full path with `--ffmpeg` if needed. A platform font can be set with `--font`.

The video is a reconstructed process presentation, not an original recording. The 12 fps rendered orbit is interpolated to 24 fps for playback. No new geometric frames are inferred by a language model.

## Native viewer and material candidate

[Build the native visionOS viewer](native/Flatiron/README.md). The template now includes the corrected model, mixed-immersion full-scale walkaround, pinch-and-pull movement, visible base-centered scaling, separate tabletop sizing, a slow turntable and reset. The controls compiled successfully and passed seven navigation math tests; headset review of this new candidate is pending. The original tabletop build loaded successfully on M5 and led to the normals report. The public template contains no signing credentials.

`material_candidate.py` adds portable 512² stone basecolor, roughness and normal maps without changing geometry. `compare_materials.py` renders actual re-imported baseline and candidate packages under matching light. The candidate passed Apple USD/ARKit validation and retained geometry/bounds. The visible difference is modest warmer stone and deeper glass; bright daylight remains pale. [Download the separate candidate](docs/flatiron_tabletop_materials.usdz). It has not received headset visual acceptance.

## Photo alignment checks

Our first real-photo alignment reduced held-out guide error from about 197 to 34 pixels, but camera-depth accuracy remains unverified. [Read the experiment limits and next geometry check](docs/photo-alignment.md) before treating a matching render as a calibrated reconstruction.

## Corrected winding candidate

[Corrected Blender scene](assets/flatiron_corrected.blend) · [Corrected baseline USDZ](docs/flatiron_tabletop_normals_fixed.usdz) · [Corrected textured USDZ](docs/flatiron_tabletop_materials_normals_fixed.usdz)

The repair reverses affected face winding and authored normals, with corner-indexed UVs reordered to preserve their vertex association. Positions, dimensions, materials and texture bytes stay unchanged. Double-sided rendering was already enabled; enabling it again would not repair the source geometry.

In a new Blender GUI scene, run `scripts/rebuild_corrected.py`. It applies the two determinant-aware generator fixes before replaying the original live steps and writes to `outputs/rebuild-corrected/`. The original generator and accepted scene remain unchanged. A full geometry replay verified all 12 meshes and 285,670 vertex positions unchanged, with no remaining diagnosed inward components; all 11 exported mesh index arrays match the directly repaired USDZ. The corrected Blender file was saved, reopened and checked with identical geometry fingerprints. A changed generator fails the source patch check rather than silently applying an unverified repair. The patch is also available as `scripts/flatiron_base_winding_fix.patch`.

The published showcase video depicts the earlier baseline. New native normals and immersive interaction need separate headset review.

## Facade support and visible scaling

[Supported Blender scene](assets/flatiron_supported.blend) · [Supported tabletop USDZ](docs/flatiron_tabletop_supported.usdz)

M5 review exposed a second issue: 1,062 raised medallion rings were zero-thickness strips in front of their support. The new candidate gives those rings backs and sidewalls while preserving every original front vertex, face and normal, the ring openings, all other meshes and materials. Rear attachment samples contact the support within 10 micrometres; rear face centres overlap it by approximately 2 mm. A matched grazing render confirms the joins ([before/after comparison](docs/facade-attachment-comparison.png)). A separate set of 354 thin ledge ornaments already intersects closed support solids and remains unchanged.

The candidate adds 33,984 vertices and 50,976 quads, bringing the USDZ to 25,634,073 bytes. Apple USD/ARKit validation passes. Source assumptions and simplified ornament remain approximate. This is a targeted attachment repair, not a claim that every feature matches the real building. The earlier textured experiment has not received this backing change.

Run `scripts/rebuild_supported.py` in a fresh Blender GUI scene. It applies the winding correction and exact-topology backing helper before the final previews/save, writing to `outputs/rebuild-supported/`. `rebuild_corrected.py` still produces the normals-only version; `rebuild.py` retains the original baseline. The backing helper requires NumPy (included in the tested Blender install) and deliberately accepts only this diagnosed ring topology. SceneAudit informed the contact checks; its private source is not included.

Native controls now resize around the building base rather than the viewer. Scaling around the viewer had changed size and viewing distance together, making the visible size change difficult to notice. Both tabletop and immersive views offer an optional 3°/second turntable; manual movement, scaling and reset stop it. No two-hand scale gesture is claimed.
