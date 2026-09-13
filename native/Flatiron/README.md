# Flatiron tabletop and immersive viewer

A SwiftUI/RealityKit viewer for the procedural Flatiron building. Inspect a tabletop or enter a mixed-immersion walkaround at the model's approximate original scale. This build3 candidate includes corrected normals and backed medallions, visible resizing and an optional slow turntable. Controls passed seven math tests and a visionOS source-check build; latest device/wearer verification is separate.

## Quickstart

Run `xcodegen generate` in this directory, select your own signing team and unique bundle identifier, and build the FlatironTabletop scheme for visionOS. The template uses `com.example.FlatironTabletop`, deployment target visionOS2.0. No signing credentials are included. Run `swift test` here for the shared navigation math tests.

## Things to Try

1. Launch the app and choose Enter full-scale walkaround. Initial placement waits for a tracked headset pose.
2. Enable pinch-and-pull movement, look at the building or floor, and pinch/drag to travel. Release stops movement; gain options are1x,4x and12x.
3. Use Half size/Double size to visibly resize around the building base. Return to start restores the approximate original scale outside the narrow end.
4. Open tabletop and use its separate Smaller/Larger controls; sizing is bounded to fit the volume.
5. Enable Slow turntable for one rotation every two minutes. Movement, scaling, reset or exit stops rotation.

## Implementation and checks

The native ACCVR interaction precedent uses a fixed parent frame and moves the scene root with damping0.35. Moving the scene therefore cannot feed back into the hand input. Flatiron adds bounded movement gain, base-centered object scaling and a RealityKit System for optional turntable motion. Tests cover release stop, re-grab, movement bounds, scale pivots and rotation without orbit drift.

Initial/reset placement uses ARKit WorldTrackingProvider device-anchor poses. Missing tracking pauses placement explicitly; resizing an already placed building does not require a fresh pose. Immersive size ranges from1% to200% of the estimated original; tabletop sizing ranges from25% to115% of its normalized size, with the horizontal diagonal included in volume-fit calculations. Two-hand scaling is not implemented.

The USDZ exporter reduced source dimensions by1/87; full scale restores exactly87x, rather than inferring height from bounds. Dimensions are artistic estimates, not survey measurements. The bundled supported-model SHA256 is `c37f707c7423b468d0b7744912cad908808155794bd3d344e4ee04fc35b06582`. See the root README for geometry validation and preserved earlier variants.

Build-specific load, placement, scale and turntable JSON receipts are written to the app's Documents folder. They prove applied state, not wearer appearance or interaction acceptance.
