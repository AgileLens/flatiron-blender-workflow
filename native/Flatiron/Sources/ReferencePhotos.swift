import SwiftUI
import RealityKit
import Observation
import UIKit

/// One bundled reference photo, its licence and (when solved) its camera against the model.
struct ReferencePhoto: Decodable, Identifiable {
    struct Camera: Decodable {
        let positionBlender: [Float]
        let rightBlender: [Float]
        let upBlender: [Float]
        let forwardBlender: [Float]
        let hfovDeg: Float
        let vfovDeg: Float
        let headingDeg: Float
        let pitchDeg: Float
        let heightM: Float
        let anchorBlender: [Float]
        let anchorUV: [Float]
        let anchorUpUV: [Float]
        let fitRMSEpx: Float
        let holdoutRMSEpx: Float
        let imageSizePx: [Float]
        let focalSource: String

        var position: SIMD3<Float> { PhotoAlignMath.realityKit(fromBlender: v(positionBlender)) }
        var right: SIMD3<Float> { PhotoAlignMath.realityKit(fromBlender: v(rightBlender)) }
        var up: SIMD3<Float> { PhotoAlignMath.realityKit(fromBlender: v(upBlender)) }
        var forward: SIMD3<Float> { PhotoAlignMath.realityKit(fromBlender: v(forwardBlender)) }
        var aspect: Float { imageSizePx[0] / imageSizePx[1] }
        private func v(_ a: [Float]) -> SIMD3<Float> { [a[0], a[1], a[2]] }
    }

    let id: String
    let file: String
    let title: String
    let author: String
    let license: String
    let licenseURL: String
    let sourceURL: String
    let credit: String
    let used: Bool
    let note: String
    let bayNote: String
    let camera: Camera?

    var url: URL? {
        let name = (file as NSString).deletingPathExtension
        return Bundle.main.url(forResource: name, withExtension: "jpg")
            ?? Bundle.main.url(forResource: name, withExtension: "jpg", subdirectory: "Photos")
    }
}

@Observable @MainActor
final class PhotoLibrary {
    private(set) var photos: [ReferencePhoto] = []
    private(set) var index = 0
    private(set) var loadError: String?
    var overlayOpacity: Float = 0.5
    @ObservationIgnored private var textures: [String: TextureResource] = [:]

    init() {
        let url = Bundle.main.url(forResource: "photos", withExtension: "json")
            ?? Bundle.main.url(forResource: "photos", withExtension: "json", subdirectory: "Photos")
        struct Manifest: Decodable { let photos: [ReferencePhoto] }
        do {
            guard let url else { throw CocoaError(.fileNoSuchFile) }
            photos = try JSONDecoder().decode(Manifest.self, from: Data(contentsOf: url)).photos
        } catch {
            loadError = "Reference photos unavailable: \(error.localizedDescription)"
        }
    }

    var current: ReferencePhoto? { photos.isEmpty ? nil : photos[index] }
    func select(_ newIndex: Int) {
        guard !photos.isEmpty else { return }
        index = min(max(newIndex, 0), photos.count - 1)
    }

    func step(_ delta: Int) {
        guard !photos.isEmpty else { return }
        index = (index + delta + photos.count) % photos.count
    }

    func image(for photo: ReferencePhoto) -> UIImage? {
        photo.url.flatMap { UIImage(contentsOfFile: $0.path) }
    }

    func texture(for photo: ReferencePhoto) async throws -> TextureResource {
        if let cached = textures[photo.id] { return cached }
        guard let url = photo.url else { throw CocoaError(.fileNoSuchFile) }
        let texture = try await TextureResource(contentsOf: url)
        textures[photo.id] = texture
        return texture
    }

    /// A flat, unlit photo quad (faces +Z) whose opacity can be faded.
    static func overlayEntity(texture: TextureResource, width: Float, height: Float, opacity: Float) -> ModelEntity {
        var material = UnlitMaterial()
        material.color = .init(tint: .white, texture: .init(texture))
        let entity = ModelEntity(mesh: .generatePlane(width: width, height: height), materials: [material])
        entity.name = "ReferencePhotoOverlay"
        entity.components.set(OpacityComponent(opacity: opacity))
        return entity
    }
}

struct PhotoPanel: View {
    @Bindable var library: PhotoLibrary
    let experience: FlatironExperience
    let tabletop: FlatironTabletop
    @State private var status: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Reference photos").font(.headline)
            if let error = library.loadError { Text(error).foregroundStyle(.red) }
            if let photo = library.current {
                if let image = library.image(for: photo) {
                    Image(uiImage: image).resizable().scaledToFit()
                        .frame(maxWidth: .infinity, maxHeight: 250)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                }
                HStack {
                    Button("Previous", systemImage: "chevron.left") { library.step(-1); status = nil }
                    Text("\(library.index + 1) of \(library.photos.count)").monospacedDigit()
                    Button("Next", systemImage: "chevron.right") { library.step(1); status = nil }
                }
                Text(photo.title).font(.callout).lineLimit(2)
                Text("Photo: \(photo.credit)").font(.caption)
                HStack(spacing: 16) {
                    if let url = URL(string: photo.sourceURL) { Link("Source", destination: url).font(.caption) }
                    if let url = URL(string: photo.licenseURL) { Link(photo.license, destination: url).font(.caption) }
                }
                if let camera = photo.camera, photo.used {
                    Text(String(format: "Camera solve: %.0f px fit, %.0f px held-out error · %.0f m up, looking %.0f° %@",
                                camera.fitRMSEpx, camera.holdoutRMSEpx, camera.heightM,
                                abs(camera.pitchDeg), camera.pitchDeg >= 0 ? "up" : "down"))
                        .font(.caption).foregroundStyle(.secondary)
                    if photo.bayNote.hasPrefix("ASSUMED") {
                        Text("Position along Fifth Avenue is assumed: the three oriels look identical.")
                            .font(.caption).foregroundStyle(.orange)
                    } else if photo.bayNote.hasPrefix("PINNED") {
                        Text("Oriel identified as the centre one by cross-checks with photo 07 (moderate confidence).")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    HStack {
                        Button("Align walkaround") { Task { status = await experience.align(to: photo, library: library) } }
                            .disabled(!(experience.ready && experience.positioned))
                        Button("Align tabletop") { Task { status = await tabletop.align(to: photo, library: library) } }
                            .disabled(!(tabletop.ready && tabletop.isOpen))
                    }
                    Text("Walkaround moves you to where the photographer stood, facing the same way. Tabletop turns the model so the photo's view faces you.")
                        .font(.caption).foregroundStyle(.secondary)
                } else {
                    Text("No camera solve for this photo, so Align is unavailable. \(photo.note)")
                        .font(.caption).foregroundStyle(.secondary)
                }
                HStack {
                    Text("Photo overlay")
                    Slider(value: $library.overlayOpacity, in: 0...1)
                        .onChange(of: library.overlayOpacity) { _, value in
                            experience.setOverlayOpacity(value)
                            tabletop.setOverlayOpacity(value)
                        }
                    Button("Hide") { experience.clearAlignment(); tabletop.clearAlignment(); status = nil }
                }
                if let status { Text(status).font(.caption).foregroundStyle(.secondary) }
            }
        }
    }
}
