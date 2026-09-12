# Flatiron Tabletop and Walkaround

An Agile Lens visionOS viewer for the procedural Flatiron model, with a bounded tabletop and mixed-immersion walkaround. Build 2 restores approximate source scale using the exporter's exact 87× inverse, places the viewer outside the narrow end, and bundles a winding/normal-only repair. The candidate compiled successfully with five navigation math tests passing; wearer testing is pending. The original build remains preserved separately.

## Quickstart

Run `xcodegen generate` in this directory. Build the FlatironTabletop scheme for visionOS using your own signing team and unique bundle identifier. This template uses `com.example.FlatironTabletop`, build 2. Pure math checks use `swift test` in this directory.

## Things to Try

1. Launch Flatiron Tabletop and select Enter full-scale walkaround. Wait for tracked-head placement.
2. Walk physically around the building, or enable pinch-and-pull movement and drag the building or floor. Release stops immediately.
3. Change movement gain from the native reference's 1× to 4× or 12× for longer travel. Half size and Double size preserve the viewer anchor; Return to start restores approximate full scale outside the narrow end.
4. Open tabletop for the original bounded inspection surface. In Files the new asset is copied as Flatiron Build 2.usdz, preserving the previous baseline and material candidate.
5. Retrieve build-specific launch, tabletop-load, immersive-load, first-placement, reset, scale and navigation-end JSON receipts from Documents. No receipt is a substitute for wearer appearance or interaction review.

## Navigation references

Native ACCVR: `ibrews/UnrealRealityKitBridge`, commit `09b573b6ed621b925f1ff80a3fd6ccdfa34b7971`, `Bridge/UEFrameworkShell/Sources/UEFrameworkShellApp.swift` lines244–261 and803–868. Fixed-holder targeted DragGesture updates the scene root with damping0.35. The parent holder never moves, so input cannot feed back from world movement. Native reference input-only collision targets use empty physics group/mask; Flatiron preserves that setting. Navigation releases hold output without consuming a final release-location sample or applying inertia.

Viewer pose follows `ibrews/UnRealityKit`, commit `e7ab49b546a366a3a387cf62fd53d1c0bc43eee6`, `Bridge/URKLiveLinkViewer/Sources/URKLaser.swift` URKHeadTracker: WorldTrackingProvider.queryDeviceAnchor at current host time, running provider and tracked anchor required. Missing pose pauses placement/scaling explicitly; rendering head anchors are not treated as measured camera transforms. Session/providers are stopped on exit and recreated for reentry.

Flatiron extensions: bounded movement gain1–12, per-input-event0.5m motion clamp, anchored scale buttons limited to1–200% of original scale, outside placement and recovery controls. No native two-hand scaling or Unreal WorldToMeters equivalence is claimed. Initial/reset/scale position receipts expose the applied head/root transforms.

## Asset provenance and preservation

Baseline source: https://github.com/AgileLens/flatiron-blender-workflow . The Blender export scaled its root1/87; restoring87 gives the original guessed dimensions, including roof and sidewalk, rather than forcing the overall bounds to87m. Original assumptions remain approximate.

Build2 USDZ SHA256 `78f55fbbdd2a05801a3f221c1bb1a33c4dc0794ebfa025d73a0e9fa5a6ef7777`. Normal-only repair reverses22,586 inward closed shells and2,478 inward planar medallions. Positions, transforms, materials, texture bytes and dimensions are unchanged; Apple usdchecker --arkit passes. Source construction used a mirrored facade basis with unchanged box winding; export preserved that source defect. Original baseline hash `e6d2a07fce2b001d430c2f3819daca27b60b0691170b20c50179635f78d8c4d8` remains in the immutable build1 archive and original public preview.

Native Xcode/signing baseline: `ibrews/m5-avp-gfx-probe` commit `22e87500a7e003238e99738ec7393a23e658ad80`. Original probe targets remain unchanged. Build1 compiled with Xcode26.6/17F113,xros26.5 on Sam, signed on MBP, installed on M5, and produced a verified native-load receipt; Alex then reported flipped normals and requested full-scale navigation. Build2 is the response to that feedback, not yet human-accepted.
