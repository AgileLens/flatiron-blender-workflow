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
    @State private var tabletop = FlatironTabletop()
    @State private var library = PhotoLibrary()

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
            FlatironControls(experience: experience, tabletop: tabletop, library: library)
        }
        .windowResizability(.contentSize)

        WindowGroup("Flatiron Tabletop", id: "tabletop") { FlatironView(tabletop: tabletop) }
            .windowStyle(.volumetric)
            .defaultSize(width: 1.2, height: 1.2, depth: 1.2, in: .meters)

        ImmersiveSpace(id: "flatiron-walkaround") {
            FlatironImmersiveView(experience: experience)
        }
        .immersionStyle(selection: .constant(.mixed), in: .mixed)
    }
}

struct FlatironView: View {
    let tabletop: FlatironTabletop

    var body: some View {
        RealityView { content, attachments in
            await tabletop.install(in: content)
            if let controls = attachments.entity(for: "controls") {
                controls.position = [0, -0.52, 0.55]
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
                    Toggle("Turntable", isOn: Binding(
                        get: { tabletop.turntableEnabled },
                        set: { tabletop.setTurntable($0) }))
                    HStack {
                        Text("Speed")
                        Slider(value: Binding(get: { tabletop.turntableDegreesPerSecond },
                                              set: { tabletop.setTurntableSpeed($0) }),
                               in: 1...30, onEditingChanged: { editing in if !editing { tabletop.recordTurntableSpeed() } })
                            .frame(width: 220)
                        Text(String(format: "%.0f°/s · %.0f s per turn", tabletop.turntableDegreesPerSecond,
                                    360 / tabletop.turntableDegreesPerSecond))
                            .monospacedDigit().font(.caption)
                    }
                    Text("Resizing keeps the building standing on the table · Agile Lens")
                        .font(.caption).foregroundStyle(.secondary)
                }
                .disabled(!tabletop.ready)
                .padding(18)
                .glassBackgroundEffect()
            }
        }
        .onAppear { tabletop.isOpen = true }
        .onDisappear { tabletop.setTurntable(false); tabletop.clearAlignment(); tabletop.isOpen = false }
    }
}
