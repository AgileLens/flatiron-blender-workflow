import SwiftUI
import RealityKit
import CryptoKit

enum Receipt {
    static var build: String { Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "unknown" }
    static func write(_ stage: String, _ values: [String: Any] = [:]) {
        var result = values
        result["stage"] = stage
        result["timestamp"] = ISO8601DateFormatter().string(from: Date())
        result["bundle"] = Bundle.main.bundleIdentifier ?? "unknown"
        result["build"] = build
        if let data = try? JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]) {
            // Build-specific names preserve the reviewed build 1 evidence.
            try? data.write(to: URL.documentsDirectory.appendingPathComponent("flatiron-build\(build)-\(stage).json"), options: .atomic)
        }
    }
}

@main
struct FlatironApp: App {
    @State private var experience = FlatironExperience()

    init() {
        Receipt.write("launched")
        if let source = Bundle.main.url(forResource: "Flatiron", withExtension: "usdz") {
            let destination = URL.documentsDirectory.appendingPathComponent("Flatiron Build \(Receipt.build).usdz")
            if !FileManager.default.fileExists(atPath: destination.path) {
                try? FileManager.default.copyItem(at: source, to: destination)
            }
        }
    }

    var body: some SwiftUI.Scene {
        WindowGroup("Flatiron", id: "controls") {
            FlatironControls(experience: experience)
        }
        .windowResizability(.contentSize)

        WindowGroup("Flatiron Tabletop", id: "tabletop") { FlatironView() }
            .windowStyle(.volumetric)
            .defaultSize(width: 1.2, height: 1.2, depth: 1.2, in: .meters)

        ImmersiveSpace(id: "flatiron-walkaround") {
            FlatironImmersiveView(experience: experience)
        }
        .immersionStyle(selection: .constant(.mixed), in: .mixed)
    }
}

struct FlatironView: View {
    @State private var angle: Float = 0
    @State private var loadError: String?
    @State private var loaded = false

    var body: some View {
        RealityView { content, attachments in
            do {
                guard let url = Bundle.main.url(forResource: "Flatiron", withExtension: "usdz") else {
                    throw CocoaError(.fileNoSuchFile)
                }
                let model = try await Entity(contentsOf: url)
                let bounds = model.visualBounds(relativeTo: nil)
                let largest = max(bounds.extents.x, max(bounds.extents.y, bounds.extents.z))
                guard largest.isFinite, largest > 0 else { throw CocoaError(.fileReadCorruptFile) }
                let scale: Float = 0.9 / largest
                model.scale *= SIMD3<Float>(repeating: scale)
                model.position = -bounds.center * scale
                let root = Entity()
                root.name = "flatiron-root"
                root.addChild(model)
                content.add(root)
                var meshes = 0
                @MainActor func count(_ entity: Entity) {
                    if entity.components.has(ModelComponent.self) { meshes += 1 }
                    for child in entity.children { count(child) }
                }
                count(model)
                let hash = try SHA256.hash(data: Data(contentsOf: url)).map { String(format: "%02x", $0) }.joined()
                Receipt.write("tabletop-loaded", ["meshEntities": meshes, "assetSHA256": hash,
                    "assetBoundsMeters": [bounds.extents.x, bounds.extents.y, bounds.extents.z],
                    "displayScale": scale, "addedToRealityView": true])
                loaded = true
            } catch {
                loadError = error.localizedDescription
                Receipt.write("tabletop-failed", ["error": error.localizedDescription])
            }
            if let controls = attachments.entity(for: "controls") {
                controls.position = [0, -0.52, 0.35]
                content.add(controls)
            }
        } update: { content, _ in
            content.entities.first(where: { $0.name == "flatiron-root" })?.orientation = simd_quatf(angle: angle, axis: [0, 1, 0])
        } attachments: {
            Attachment(id: "controls") {
                VStack(spacing: 8) {
                    Text("Flatiron Tabletop").font(.title2).bold()
                    if let loadError { Text(loadError).foregroundStyle(.red) }
                    else if !loaded { ProgressView("Loading Flatiron…") }
                    HStack {
                        Button("Rotate left", systemImage: "arrow.counterclockwise") { angle += .pi / 8 }
                        Button("Reset") { angle = 0 }
                        Button("Rotate right", systemImage: "arrow.clockwise") { angle -= .pi / 8 }
                    }
                    Text("Walk around the model · Agile Lens").font(.caption).foregroundStyle(.secondary)
                }
                .padding(18)
                .glassBackgroundEffect()
            }
        }
    }
}
