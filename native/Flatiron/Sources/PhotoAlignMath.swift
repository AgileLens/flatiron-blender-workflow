import simd

/// Pure math for aligning the model to a solved reference-photo camera. Shared with the SwiftPM tests.
/// Blender (model source) is Z-up metres at full scale; the USDZ is Blender / 87 and RealityKit
/// loads its Z-up stage as Y-up, i.e. (x, y, z) -> (x, z, -y).
enum PhotoAlignMath {
    static func realityKit(fromBlender v: SIMD3<Float>) -> SIMD3<Float> { [v.x, v.z, -v.y] }

    /// Heading of a direction in the RealityKit horizontal plane, measured from +Z toward +X.
    static func yaw(of v: SIMD3<Float>) -> Float { atan2(v.x, v.z) }

    /// Walkaround: rotation about +Y that turns the photo camera's horizontal heading onto the
    /// viewer's current heading.
    static func alignmentYaw(cameraForward: SIMD3<Float>, viewerForward: SIMD3<Float>) -> Float {
        yaw(of: viewerForward) - yaw(of: cameraForward)
    }

    /// Walkaround: root position that puts the camera (root-local offset already scaled to metres)
    /// exactly at the viewer's head.
    static func rootPosition(head: SIMD3<Float>, cameraOffset: SIMD3<Float>, rotation: simd_quatf) -> SIMD3<Float> {
        head - rotation.act(cameraOffset)
    }

    /// Tabletop: yaw that makes the photo camera look along -Z, into the volume from its front.
    static func tabletopYaw(cameraForward: SIMD3<Float>) -> Float {
        .pi - yaw(of: cameraForward)
    }

    /// Orientation of a photo plane (generatePlane faces +Z) seen along `forward` with `up`.
    static func facingOrientation(right: SIMD3<Float>, up: SIMD3<Float>, forward: SIMD3<Float>) -> simd_quatf {
        simd_quatf(simd_float3x3(columns: (simd_normalize(right), simd_normalize(up), -simd_normalize(forward))))
    }
}
