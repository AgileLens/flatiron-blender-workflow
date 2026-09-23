import RealityKit
import simd

/// Optional visual motion. The fixed parent-space pivot prevents orbit drift.
struct TurntableComponent: Component {
    let localPivot: SIMD3<Float>
    let parentPivot: SIMD3<Float>
    let initialRotation: simd_quatf
    var angle: Float = 0
    /// Build 5: adjustable from the tabletop slider (default three degrees/second).
    var degreesPerSecond: Float = 3

    init(entity: Entity, localPivot: SIMD3<Float>) {
        self.localPivot = localPivot
        parentPivot = entity.position + entity.orientation.act(entity.scale * localPivot)
        initialRotation = entity.orientation
    }
}

struct TurntableSystem: System {
    static let query = EntityQuery(where: .has(TurntableComponent.self))
    init(scene: RealityKit.Scene) {}

    func update(context: SceneUpdateContext) {
        for entity in context.entities(matching: Self.query, updatingSystemWhen: .rendering) {
            guard var spin = entity.components[TurntableComponent.self] else { continue }
            // Do not jump after suspended rendering.
            let delta = Float(min(max(context.deltaTime, 0), 0.1))
            spin.angle = (spin.angle + delta * spin.degreesPerSecond * .pi / 180).truncatingRemainder(dividingBy: 2 * .pi)
            let rotation = simd_quatf(angle: spin.angle, axis: [0, 1, 0]) * spin.initialRotation
            entity.orientation = rotation
            entity.position = NavigationMath.positionForPivot(spin.parentPivot, local: spin.localPivot,
                                                              rotation: rotation, scale: entity.scale)
            entity.components.set(spin)
        }
    }
}
