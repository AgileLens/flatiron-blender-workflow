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
    private(set) var turntableDegreesPerSecond: Float = 3
    private(set) var alignedPhotoID: String?
    var isOpen = false
    /// Build 5: the building stands on this floor plane of the 1.2 m volume. Resizing and the
    /// turntable pivot about the building's base centre here, so it stays on the table.
    static let floorY: Float = -0.55
    @ObservationIgnored private let root = Entity()
    @ObservationIgnored private let stage = Entity()
    @ObservationIgnored private var model: Entity?
    @ObservationIgnored private var photoOverlay: ModelEntity?
    @ObservationIgnored private var alignedPhoto: ReferencePhoto?

    func install(in content: RealityViewContent) async {
        ready = false
        error = nil
        setTurntable(false)
        clearAlignment()
        root.children.removeAll()
        root.transform = Transform(translation: [0, Self.floorY, 0])
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
            // The horizontal diagonal bounds every yaw angle. At 115% the building is at most
            // 1.035 m tall from the floor at y=-0.55, so its top stays inside the 1.2 m volume.
            let scale: Float = 0.9 / largest
            model.scale *= SIMD3<Float>(repeating: scale)
            // Base centre (not the bounding-box centre) at the root origin: the ground-level pivot.
            model.position = -SIMD3<Float>(bounds.center.x, bounds.min.y, bounds.center.z) * scale
            self.model = model
            root.addChild(model)
            stage.children.removeAll()
            stage.addChild(root)
            content.add(stage)
            let hash = try SHA256.hash(data: Data(contentsOf: url)).map { String(format: "%02x", $0) }.joined()
            Receipt.write("tabletop-loaded", ["assetSHA256": hash,
                "assetBoundsMeters": [bounds.extents.x, bounds.extents.y, bounds.extents.z],
                "assetBoundsMin": [bounds.min.x, bounds.min.y, bounds.min.z],
                "displayScale": scale, "addedToRealityView": true, "pivot": "building base centre on floor y=-0.55"])
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
        if let photo = alignedPhoto { placeOverlay(for: photo) }
        Receipt.write("tabletop-scale", ["relativeScale": relativeScale, "surface": "tabletop",
            "pivot": "building base centre on the volume floor", "floorY": Self.floorY,
            "maximumExtentMeters": 0.9 * relativeScale])
    }

    func rotate(by angle: Float) {
        guard ready else { return }
        setTurntable(false)
        clearAlignment()
        root.orientation = simd_quatf(angle: angle, axis: [0, 1, 0]) * root.orientation
    }

    func reset() {
        guard ready else { return }
        setTurntable(false)
        clearAlignment()
        root.transform = Transform(translation: [0, Self.floorY, 0])
        relativeScale = 1
        Receipt.write("tabletop-reset")
    }

    func setTurntable(_ enabled: Bool) {
        root.components.remove(TurntableComponent.self)
        turntableEnabled = enabled && ready
        if turntableEnabled {
            clearAlignment()
            var spin = TurntableComponent(entity: root, localPivot: .zero)
            spin.degreesPerSecond = turntableDegreesPerSecond
            root.components.set(spin)
        }
        Receipt.write("tabletop-turntable", ["enabled": turntableEnabled, "degreesPerSecond": turntableDegreesPerSecond])
    }

    /// Build 5 speed slider: changes the running turntable in place (no restart, no jump).
    func setTurntableSpeed(_ degreesPerSecond: Float) {
        turntableDegreesPerSecond = min(max(degreesPerSecond, 1), 30)
        if var spin = root.components[TurntableComponent.self] {
            spin.degreesPerSecond = turntableDegreesPerSecond
            root.components.set(spin)
        }
    }

    func recordTurntableSpeed() {
        Receipt.write("tabletop-turntable-speed", ["degreesPerSecond": turntableDegreesPerSecond,
                                                   "secondsPerTurn": 360 / turntableDegreesPerSecond])
    }

    /// A volume cannot see the viewer's head, so instead of moving the viewer we turn the upright
    /// model so the photo camera's heading points into the volume from its front, and lay the photo
    /// over it at the model's scale, anchored at a solved landmark.
    func align(to photo: ReferencePhoto, library: PhotoLibrary) async -> String {
        guard ready, let camera = photo.camera else { return "Align needs a solved photo and an open tabletop." }
        let texture: TextureResource
        do { texture = try await library.texture(for: photo) } catch { return "Photo could not load: \(error.localizedDescription)" }
        setTurntable(false)
        clearAlignment()
        root.orientation = simd_quatf(angle: PhotoAlignMath.tabletopYaw(cameraForward: camera.forward), axis: [0, 1, 0])
        alignedPhoto = photo
        alignedPhotoID = photo.id
        let overlay = PhotoLibrary.overlayEntity(texture: texture, width: 1, height: 1, opacity: library.overlayOpacity)
        stage.addChild(overlay)
        photoOverlay = overlay
        placeOverlay(for: photo)
        Receipt.write("tabletop-align", ["photo": photo.id, "rootYaw": PhotoAlignMath.tabletopYaw(cameraForward: camera.forward),
                                         "relativeScale": relativeScale, "overlayPosition": [overlay.position.x, overlay.position.y, overlay.position.z],
                                         "overlayScale": [overlay.scale.x, overlay.scale.y],
                                         "assumedEye": [Self.assumedEye.x, Self.assumedEye.y, Self.assumedEye.z]])
        let look = camera.pitchDeg >= 0 ? "from below" : "from above"
        return String(format: "Aligned to %@: the photo's view now faces you (taken %.0f m up, %@). Fade the overlay to compare.",
                      photo.id, camera.heightM, look)
    }

    /// Assumed viewing eye for the overlay, in volume coordinates: about 1.3 m in front of the volume
    /// centre, slightly above it (a volume cannot report the viewer's head pose).
    static let assumedEye = SIMD3<Float>(0, 0.15, 1.3)

    /// Size and place the photo quad so a solved landmark and a point 10 m above it line up, seen
    /// from the assumed eye, with the model's own landmark positions. The quad sits just in front of
    /// the model's nearest point, facing the viewer, so the building never hides it.
    private func placeOverlay(for photo: ReferencePhoto) {
        guard let overlay = photoOverlay, let camera = photo.camera, let model else { return }
        func volumePoint(_ blender: SIMD3<Float>) -> SIMD3<Float> {
            let asset = PhotoAlignMath.realityKit(fromBlender: blender) / 87
            let rootLocal = model.position + model.scale.x * asset
            return root.position + root.orientation.act(root.scale.x * rootLocal)
        }
        let eye = Self.assumedEye
        let planeZ = min(root.visualBounds(relativeTo: stage).max.z + 0.03, 0.55)
        func onPlane(_ a: SIMD3<Float>) -> SIMD3<Float> { eye + (a - eye) * ((planeZ - eye.z) / (a.z - eye.z)) }
        let anchor = SIMD3<Float>(camera.anchorBlender[0], camera.anchorBlender[1], camera.anchorBlender[2])
        let p1 = onPlane(volumePoint(anchor)), p2 = onPlane(volumePoint(anchor + [0, 0, 10]))
        let dv = camera.anchorUV[1] - camera.anchorUpUV[1]
        guard dv > 1e-4 else { return }
        let height = (p2.y - p1.y) / dv
        let width = height * camera.aspect
        overlay.scale = [width, height, 1]
        overlay.position = [p1.x + (0.5 - camera.anchorUV[0]) * width, p1.y + (camera.anchorUV[1] - 0.5) * height, planeZ]
    }

    func setOverlayOpacity(_ value: Float) {
        photoOverlay?.components.set(OpacityComponent(opacity: value))
    }

    func clearAlignment() {
        photoOverlay?.removeFromParent()
        photoOverlay = nil
        alignedPhoto = nil
        alignedPhotoID = nil
    }
}
