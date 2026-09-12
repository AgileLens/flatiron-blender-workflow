import SwiftUI
import RealityKit
import Observation
import CryptoKit

@Observable @MainActor
final class FlatironExperience {
    enum Phase { case closed, opening, open }
    var phase: Phase = .closed
    private(set) var ready = false
    private(set) var positioned = false
    private(set) var error: String?
    private(set) var navigationEnabled = false
    private(set) var relativeScale: Float = 1
    private(set) var trackingNotice: String?
    var movementGain: Float = 1

    // The exporter explicitly multiplied by 1/87. Undo that exact transform;
    // do not normalize the roof/sidewalk bounds to a nominal building height.
    static let sourceToFullScale: Float = 87
    @ObservationIgnored let holder = Entity()
    @ObservationIgnored private let root = Entity()
    @ObservationIgnored private let tracking = ViewerTracking()
    @ObservationIgnored private let floorCatcher = Entity()
    @ObservationIgnored private let buildingTarget = Entity()
    @ObservationIgnored private var assetBounds: BoundingBox?
    @ObservationIgnored private var drag = WorldDrag()

    func install(in content: RealityViewContent) async {
        ready = false
        positioned = false
        error = nil
        navigationEnabled = false
        drag.end()
        holder.name = "FlatironFixedHolder"
        root.name = "FlatironImmersiveRoot"
        root.children.removeAll()
        root.transform = .identity
        root.isEnabled = false
        holder.children.removeAll()
        holder.addChild(root)
        content.add(holder)
        await tracking.start()
        do {
            guard let url = Bundle.main.url(forResource: "Flatiron", withExtension: "usdz") else {
                throw CocoaError(.fileNoSuchFile)
            }
            let model = try await Entity(contentsOf: url)
            let bounds = model.visualBounds(relativeTo: nil)
            guard bounds.extents.y.isFinite, bounds.extents.y > 0 else {
                throw CocoaError(.fileReadCorruptFile)
            }
            assetBounds = bounds
            root.addChild(model) // keep all imported transforms intact

            // Navigation target only: a cheap asset-bounds proxy avoids generating
            // expensive convex collisions for every decorative facade mesh.
            buildingTarget.name = "FlatironBuildingNavigationTarget"
            buildingTarget.position = bounds.center
            configureInput(buildingTarget, size: bounds.extents)
            root.addChild(buildingTarget)

            // ACCVR's fixed-holder floor catcher enables a world pull on empty
            // floor. In this floor-origin immersive scene, its top is at y=0.
            floorCatcher.name = "FlatironFloorNavigationTarget"
            floorCatcher.position = [0, -0.01, 0]
            configureInput(floorCatcher, size: [80, 0.02, 80])
            holder.addChild(floorCatcher)
            setNavigation(false)
            ready = true
            // Give the newly started provider a bounded chance to supply its
            // first measured pose. The building stays hidden until placement.
            for _ in 0..<40 {
                if tracking.pose() != nil { break }
                try await Task.sleep(for: .milliseconds(50))
            }
            reset()
            let hash = try SHA256.hash(data: Data(contentsOf: url)).map { String(format: "%02x", $0) }.joined()
            Receipt.write("immersive-loaded", [
                "assetSHA256": hash, "sourceToFullScale": Self.sourceToFullScale,
                "assetBoundsMeters": [bounds.extents.x, bounds.extents.y, bounds.extents.z],
                "addedToRealityView": true, "positioned": positioned,
                "scaleProvenance": "approximate source dimensions; export was 1/87",
                "navigationReference": "UnrealRealityKitBridge 09b573b fixed-holder root drag, damping 0.35"
            ])
        } catch {
            self.error = error.localizedDescription
            Receipt.write("immersive-failed", ["error": error.localizedDescription])
        }
    }

    private func configureInput(_ entity: Entity, size: SIMD3<Float>) {
        entity.components.set(InputTargetComponent())
        var collision = CollisionComponent(shapes: [.generateBox(size: size)], mode: .trigger)
        collision.filter = CollisionFilter(group: [], mask: [])
        entity.components.set(collision)
    }

    func setNavigation(_ enabled: Bool) {
        drag.end()
        navigationEnabled = enabled && ready && positioned
        buildingTarget.isEnabled = navigationEnabled
        floorCatcher.isEnabled = navigationEnabled
    }

    func reset() {
        guard let bounds = assetBounds else { return }
        drag.end()
        let factor = Self.sourceToFullScale
        guard let pose = tracking.pose() else {
            trackingNotice = "Waiting for head tracking. Choose Return to start when tracking resumes."
            Receipt.write("reset-paused", ["reason": "no tracked device anchor"])
            return
        }
        relativeScale = 1
        let viewer = SIMD3<Float>(pose.columns.3.x, pose.columns.3.y, pose.columns.3.z)
        let yaw = atan2(pose.columns.2.x, pose.columns.2.z)
        trackingNotice = nil
        // Blender +Y is the narrow nose; the USD Z-up -> RK Y-up conversion
        // puts it at -Z. Turn it toward the viewer and leave 8 m clear in front.
        root.orientation = simd_quatf(angle: yaw + .pi, axis: [0, 1, 0])
        root.scale = .init(repeating: factor)
        let relativePosition = SIMD3<Float>(bounds.center.x * factor, -bounds.min.y * factor, bounds.min.z * factor - 8)
        root.position = SIMD3<Float>(viewer.x, 0, viewer.z)
            + simd_quatf(angle: yaw, axis: [0, 1, 0]).act(relativePosition)
        if !positioned {
            Receipt.write("first-placement", ["viewerPosition": vector(viewer), "viewerYaw": yaw,
                "rootPosition": vector(root.position), "viewerPoseSource": "ARKitDeviceAnchor"])
        }
        positioned = true
        root.isEnabled = true
        Receipt.write("reset", ["rootPosition": vector(root.position), "sourceScale": factor,
            "viewerPosition": vector(viewer), "viewerYaw": yaw,
            "viewerPoseSource": "ARKitDeviceAnchor"])
    }

    func scale(by factor: Float) {
        guard ready, positioned else { return }
        drag.end()
        let next = min(max(relativeScale * factor, 0.01), 2)
        let ratio = next / relativeScale
        // Anchor at the viewer so scaling does not push them through the scene.
        guard let pose = tracking.pose() else {
            trackingNotice = "Head tracking is unavailable. Scaling is paused until tracking resumes."
            Receipt.write("scale-paused", ["reason": "no tracked device anchor"])
            return
        }
        trackingNotice = nil
        // The holder is identity and never moves: ARKit world == holder frame.
        let anchor = SIMD3<Float>(pose.columns.3.x, pose.columns.3.y, pose.columns.3.z)
        root.position = NavigationMath.scaledPosition(root.position, around: anchor, ratio: ratio)
        root.scale *= SIMD3<Float>(repeating: ratio)
        relativeScale = next
        Receipt.write("scale", ["relativeScale": next, "rootPosition": vector(root.position),
            "viewerPosition": vector(anchor), "viewerPoseSource": "ARKitDeviceAnchor"])
    }

    func dragChanged(start: SIMD3<Float>, current: SIMD3<Float>) {
        guard navigationEnabled, ready else { return }
        guard start.x.isFinite, start.y.isFinite, start.z.isFinite,
              current.x.isFinite, current.y.isFinite, current.z.isFinite else {
            drag.end()
            return
        }
        if !drag.active {
            drag.begin(root: root.position, hand: start, gain: movementGain)
        }
        root.position = drag.position(current: root.position, hand: current)
    }

    func endDrag() {
        guard drag.active else { return }
        drag.end()
        Receipt.write("navigation-ended", ["rootPosition": vector(root.position), "gain": movementGain])
    }

    func close() {
        setNavigation(false)
        tracking.stop()
        ready = false
        positioned = false
        phase = .closed
    }

    private func vector(_ value: SIMD3<Float>) -> [Float] { [value.x, value.y, value.z] }
}

struct FlatironImmersiveView: View {
    let experience: FlatironExperience
    var body: some View {
        RealityView { content in
            await experience.install(in: content)
        }
        .gesture(DragGesture().targetedToAnyEntity()
            .onChanged { value in
                experience.dragChanged(
                    start: value.convert(value.startLocation3D, from: .local, to: experience.holder),
                    current: value.convert(value.location3D, from: .local, to: experience.holder))
            }
            .onEnded { _ in
                // Unlike the bridge's throwable-object path, navigation must not
                // consume a final finger-release movement as a new world pull.
                experience.endDrag()
            })
        .onDisappear { experience.close() }
    }
}

struct FlatironControls: View {
    @Bindable var experience: FlatironExperience
    @Environment(\.openImmersiveSpace) private var openImmersiveSpace
    @Environment(\.dismissImmersiveSpace) private var dismissImmersiveSpace
    @Environment(\.openWindow) private var openWindow
    @State private var entryError: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Flatiron").font(.largeTitle).bold()
            Text("Walk around at approximate full scale, or inspect a tabletop model.")
                .foregroundStyle(.secondary)
            HStack {
                Button(experience.phase == .open ? "Exit walkaround" : "Enter full-scale walkaround") {
                    Task { await toggleImmersion() }
                }
                .disabled(experience.phase == .opening)
                Button("Open tabletop") { openWindow(id: "tabletop") }
            }
            if let error = entryError ?? experience.error { Text(error).foregroundStyle(.red) }
            if let notice = experience.trackingNotice { Text(notice).font(.caption).foregroundStyle(.secondary) }
            if experience.phase == .open && !experience.ready && experience.error == nil {
                ProgressView("Loading building…")
            }
            if experience.ready {
                Divider()
                Toggle("Enable pinch-and-pull movement", isOn: Binding(
                    get: { experience.navigationEnabled },
                    set: { experience.setNavigation($0) }))
                .disabled(!experience.positioned)
                Text("Look at the building or floor, pinch and pull to move in any direction. Release to stop.")
                    .font(.callout).foregroundStyle(.secondary)
                Picker("Movement gain", selection: $experience.movementGain) {
                    Text("1×").tag(Float(1))
                    Text("4×").tag(Float(4))
                    Text("12×").tag(Float(12))
                }
                .pickerStyle(.segmented)
                .onChange(of: experience.movementGain) { _, _ in experience.endDrag() }
                HStack {
                    Button("Half size") { experience.scale(by: 0.5) }.disabled(!experience.positioned)
                    Text("\(Int((experience.relativeScale * 100).rounded()))%")
                        .monospacedDigit().frame(minWidth: 52)
                    Button("Double size") { experience.scale(by: 2) }.disabled(!experience.positioned)
                    Button("Return to start") { experience.reset() }
                }
                Text("100% restores the model's original estimated dimensions. Return to start places you outside the narrow end.")
                    .font(.caption).foregroundStyle(.secondary)
            }
        }
        .padding(28)
        .frame(width: 560)
    }

    private func toggleImmersion() async {
        entryError = nil
        if experience.phase == .open {
            experience.setNavigation(false)
            await dismissImmersiveSpace()
            experience.close()
        } else {
            experience.phase = .opening
            switch await openImmersiveSpace(id: "flatiron-walkaround") {
            case .opened: experience.phase = .open
            case .userCancelled: experience.phase = .closed
            case .error:
                experience.phase = .closed
                entryError = "The walkaround could not open. Close another immersive experience and try again."
            @unknown default:
                experience.phase = .closed
                entryError = "The walkaround did not open. Try again."
            }
        }
    }
}
