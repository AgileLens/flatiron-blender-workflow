import XCTest
import simd
@testable import FlatironNavigationMath

final class PhotoAlignMathTests: XCTestCase {
    // Solved photo 02 camera (Blender, full scale), rounded.
    let cameraBlender = SIMD3<Float>(-2.5, 98.6, 1.8)
    let forwardBlender = simd_normalize(SIMD3<Float>(-0.12, -0.88, 0.45))

    func testBlenderToRealityKitIsAProperRotation() {
        let m = simd_float3x3(columns: (PhotoAlignMath.realityKit(fromBlender: [1, 0, 0]),
                                        PhotoAlignMath.realityKit(fromBlender: [0, 1, 0]),
                                        PhotoAlignMath.realityKit(fromBlender: [0, 0, 1])))
        XCTAssertEqual(simd_determinant(m), 1, accuracy: 1e-6)
        // Blender up (+Z) is RealityKit up (+Y); the prow (+Y) goes to -Z.
        XCTAssertEqual(PhotoAlignMath.realityKit(fromBlender: [0, 0, 1]), [0, 1, 0])
        XCTAssertEqual(PhotoAlignMath.realityKit(fromBlender: [0, 1, 0]), [0, 0, -1])
    }

    func testWalkaroundAlignPutsCameraAtHeadFacingViewerHeading() {
        let head = SIMD3<Float>(0.4, 1.62, -0.3)
        let viewerForward = simd_normalize(SIMD3<Float>(0.6, -0.1, -0.8))
        let camRK = PhotoAlignMath.realityKit(fromBlender: cameraBlender)
        let fwdRK = PhotoAlignMath.realityKit(fromBlender: forwardBlender)
        let yaw = PhotoAlignMath.alignmentYaw(cameraForward: fwdRK, viewerForward: viewerForward)
        let q = simd_quatf(angle: yaw, axis: [0, 1, 0])
        let root = PhotoAlignMath.rootPosition(head: head, cameraOffset: camRK, rotation: q)
        let cameraWorld = root + q.act(camRK)
        XCTAssertEqual(simd_distance(cameraWorld, head), 0, accuracy: 1e-4)
        let f = q.act(fwdRK)
        XCTAssertEqual(PhotoAlignMath.yaw(of: f), PhotoAlignMath.yaw(of: viewerForward), accuracy: 1e-4)
        // Pitch is preserved: the street photo still looks up after alignment.
        XCTAssertEqual(f.y, fwdRK.y, accuracy: 1e-5)
        XCTAssertGreaterThan(f.y, 0)
    }

    func testTabletopYawPointsCameraIntoTheVolume() {
        let fwdRK = PhotoAlignMath.realityKit(fromBlender: forwardBlender)
        let q = simd_quatf(angle: PhotoAlignMath.tabletopYaw(cameraForward: fwdRK), axis: [0, 1, 0])
        let f = q.act(fwdRK)
        let horizontal = simd_normalize(SIMD3<Float>(f.x, 0, f.z))
        XCTAssertEqual(horizontal.z, -1, accuracy: 1e-5)
    }

    func testPhotoPlaneFacesBackAlongCameraForward() {
        let right = simd_normalize(SIMD3<Float>(0.8, 0, 0.6))
        let forward = simd_normalize(SIMD3<Float>(-0.6 * 0.9, 0.44, 0.8 * 0.9))
        let up = simd_normalize(simd_cross(right, forward))
        let q = PhotoAlignMath.facingOrientation(right: right, up: up, forward: forward)
        XCTAssertEqual(simd_dot(q.act([0, 0, 1]), -forward), 1, accuracy: 1e-4)
        XCTAssertEqual(simd_dot(q.act([1, 0, 0]), right), 1, accuracy: 1e-4)
    }
}
