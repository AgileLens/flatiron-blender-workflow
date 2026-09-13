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
        TurntableComponent.registerComponent()
        TurntableSystem.registerSystem()
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
    @State private var tabletop = FlatironTabletop()

    var body: some View {
        RealityView { content, attachments in
            await tabletop.install(in: content)
            if let controls = attachments.entity(for: "controls") {
                controls.position = [0, -0.52, 0.35]
                content.add(controls)
            }
        } attachments: {
            Attachment(id: "controls") {
                VStack(spacing: 8) {
                    Text("Tabletop controls").font(.title2).bold()
                    if let error = tabletop.error { Text(error).foregroundStyle(.red) }
                    else if !tabletop.ready { ProgressView("Loading Flatiron…") }
                    HStack {
                        Button("Smaller") { tabletop.scale(by: 0.8) }
                            .disabled(tabletop.relativeScale <= 0.25)
                        Text("\(Int((tabletop.relativeScale * 100).rounded()))%")
                            .monospacedDigit().frame(minWidth: 45)
                        Button("Larger") { tabletop.scale(by: 1.25) }
                            .disabled(tabletop.relativeScale >= 1.15)
                        Button("Reset") { tabletop.reset() }
                    }
                    HStack {
                        Button("Rotate left", systemImage: "arrow.counterclockwise") { tabletop.rotate(by: .pi / 8) }
                        Button("Rotate right", systemImage: "arrow.clockwise") { tabletop.rotate(by: -.pi / 8) }
                    }
                    Toggle("Slow turntable · 2 minutes per turn", isOn: Binding(
                        get: { tabletop.turntableEnabled },
                        set: { tabletop.setTurntable($0) }))
                    Text("Size is limited to fit this volume · Agile Lens")
                        .font(.caption).foregroundStyle(.secondary)
                }
                .disabled(!tabletop.ready)
                .padding(18)
                .glassBackgroundEffect()
            }
        }
        .onDisappear { tabletop.setTurntable(false) }
    }
}
