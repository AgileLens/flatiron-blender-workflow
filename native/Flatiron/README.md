# Flatiron Tabletop for visionOS

A small SwiftUI/RealityKit volume that loads the bundled USDZ, centers it at 90cm maximum extent, provides rotation controls, and copies the model to its Files-accessible Documents folder.

1. Install Xcode and XcodeGen.
2. Set a unique bundle identifier in `project.yml`, then run `xcodegen generate` in this directory.
3. Open the generated project, choose your development team under Signing, select your Vision Pro, and build/run.
4. Open Flatiron Tabletop, or its USDZ in Files.

For command-line signing, pass `DEVELOPMENT_TEAM=YOUR_TEAM_ID` to your `xcodebuild` command. No credentials or provisioning files are included. This public template uses an example bundle ID and no preset signing team.

The original target compiled with Xcode26.6 and xros26.5 and installed on an M5 Vision Pro. Its first automated launch was blocked by the headset passcode; on-device model appearance is not yet verified. The public template has only signing/team identifiers changed from that compiled source. Deployment target: visionOS2.0.

The app writes launch/load/error JSON receipts to Documents. A successful load receipt proves scene insertion, not human visual acceptance or performance. For material comparison, also download the separate `docs/flatiron_tabletop_materials.usdz` from the repository.
