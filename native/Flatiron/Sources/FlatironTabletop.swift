import SwiftUI
import RealityKit
import Observation
import CryptoKit

@Observable @MainActor
final class FlatironTabletop {
    private(set) var ready = false
    private(set) var error: String?
    private(set) var relativeScale: Float = 1
    private(set) var turntableEnabled = false
    @ObservationIgnored private let root = Entity()

    func install(in content: RealityViewContent) async {
        ready = false
        error = nil
        setTurntable(false)
        root.children.removeAll()
        root.transform = .identity
        relativeScale = 1
        do {
            guard let url = Bundle.main.url(forResource: "Flatiron", withExtension: "usdz") else {
                throw CocoaError(.fileNoSuchFile)
            }
            let model = try await Entity(contentsOf: url)
            let bounds = model.visualBounds(relativeTo: nil)
            let horizontalDiagonal = (bounds.extents.x * bounds.extents.x + bounds.extents.z * bounds.extents.z).squareRoot()
            let largest = max(bounds.extents.y, horizontalDiagonal)
            guard largest.isFinite, largest > 0 else { throw CocoaError(.fileReadCorruptFile) }
            // The horizontal diagonal bounds every yaw angle. At 115%, the
            // largest extent is at most 1.035m inside the 1.2m volume.
            let scale: Float = 0.9 / largest
            model.scale *= SIMD3<Float>(repeating: scale)
            model.position = -bounds.center * scale
            root.addChild(model)
            content.add(root)
            let hash = try SHA256.hash(data: Data(contentsOf: url)).map { String(format: "%02x", $0) }.joined()
            Receipt.write("tabletop-loaded", ["assetSHA256": hash,
                "assetBoundsMeters": [bounds.extents.x, bounds.extents.y, bounds.extents.z],
                "displayScale": scale, "addedToRealityView": true])
            ready = true
        } catch {
            self.error = error.localizedDescription
            Receipt.write("tabletop-failed", ["error": error.localizedDescription])
        }
    }

    func scale(by factor: Float) {
        guard ready else { return }
        setTurntable(false)
        relativeScale = min(max(relativeScale * factor, 0.25), 1.15)
        root.scale = .init(repeating: relativeScale)
        Receipt.write("tabletop-scale", ["relativeScale": relativeScale, "surface": "tabletop",
            "pivot": "model center", "maximumExtentMeters": 0.9 * relativeScale])
    }

    func rotate(by angle: Float) {
        guard ready else { return }
        setTurntable(false)
        root.orientation = simd_quatf(angle: angle, axis: [0, 1, 0]) * root.orientation
    }

    func reset() {
        guard ready else { return }
        setTurntable(false)
        root.transform = .identity
        relativeScale = 1
        Receipt.write("tabletop-reset")
    }

    func setTurntable(_ enabled: Bool) {
        root.components.remove(TurntableComponent.self)
        turntableEnabled = enabled && ready
        if turntableEnabled { root.components.set(TurntableComponent(entity: root, localPivot: .zero)) }
        Receipt.write("tabletop-turntable", ["enabled": turntableEnabled, "degreesPerSecond": 3])
    }
}
