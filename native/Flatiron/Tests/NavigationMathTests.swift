import XCTest
import simd
@testable import FlatironNavigationMath

final class NavigationMathTests: XCTestCase {
    func testUniformScalePreservesChosenWorldAnchor() {
        let position = SIMD3<Float>(3, -4, -20)
        let anchor = SIMD3<Float>(2, 1.7, 5)
        let oldScale: Float = 87
        let ratio: Float = 0.5
        let localAnchor = (anchor - position) / oldScale
        let nextPosition = NavigationMath.scaledPosition(position, around: anchor, ratio: ratio)
        assertVector(nextPosition + localAnchor * oldScale * ratio, equals: anchor)
    }

    func testObjectScalePreservesRotatedBaseCenterAndReducesHeight() {
        let localBase = SIMD3<Float>(0.02, -0.003, 0.15)
        let rotation = simd_quatf(angle: 1.1, axis: [0, 1, 0])
        let scale = SIMD3<Float>(repeating: 87)
        let position = SIMD3<Float>(5, 0.261, -40)
        let fixedBase = position + rotation.act(localBase * scale)
        let ratio: Float = 0.5
        let next = NavigationMath.scaledPosition(position, around: fixedBase, ratio: ratio)
        assertVector(next + rotation.act(localBase * scale * ratio), equals: fixedBase)
        let roof = localBase + SIMD3<Float>(0, 1, 0)
        let oldRoof = position + rotation.act(roof * scale)
        let newRoof = next + rotation.act(roof * scale * ratio)
        XCTAssertEqual(newRoof.y - fixedBase.y, (oldRoof.y - fixedBase.y) * ratio, accuracy: 0.0001)
    }

    func testTurntableKeepsOffsetPivotFixedOverRepeatedFullTurns() {
        let pivot = SIMD3<Float>(3, 0, -40)
        let local = SIMD3<Float>(0.02, -0.003, 0.15)
        let scale = SIMD3<Float>(repeating: 21.75)
        let initial = simd_quatf(angle: 0.73, axis: [0, 1, 0])
        for step in 0...2400 {
            let rotation = simd_quatf(angle: Float(step) * .pi / 300, axis: [0, 1, 0]) * initial
            let position = NavigationMath.positionForPivot(pivot, local: local, rotation: rotation, scale: scale)
            assertVector(position + rotation.act(local * scale), equals: pivot)
        }
    }

    func testReleaseHoldsOutputEvenWhenFingerMoves() {
        var drag = WorldDrag()
        drag.begin(root: .zero, hand: .zero, gain: 4)
        let last = drag.position(current: .zero, hand: [0.2, 0.1, 0])
        drag.end()
        for _ in 0..<120 {
            assertVector(drag.position(current: last, hand: [10, -10, 10]), equals: last)
        }
    }

    func testRegrabRebaselinesWithoutJump() {
        var drag = WorldDrag()
        drag.begin(root: .zero, hand: .zero, gain: 1)
        let prior = drag.position(current: .zero, hand: [1, 0, 0])
        drag.end()
        let newHand = SIMD3<Float>(12, 3, -7)
        drag.begin(root: prior, hand: newHand, gain: 12)
        assertVector(drag.position(current: prior, hand: newHand), equals: prior)
    }

    func testFixedFrameDragConvergesWithoutFeedbackRunaway() {
        var drag = WorldDrag()
        drag.begin(root: .zero, hand: .zero, gain: 1)
        var position = SIMD3<Float>.zero
        for _ in 0..<120 { position = drag.position(current: position, hand: [1, 2, 3]) }
        assertVector(position, equals: [1, 2, 3])
    }

    func testTrackingSpikeHasBoundedStep() {
        var drag = WorldDrag()
        drag.begin(root: .zero, hand: .zero, gain: 12)
        let position = drag.position(current: .zero, hand: [1000, 1000, 1000])
        let length = (position.x * position.x + position.y * position.y + position.z * position.z).squareRoot()
        XCTAssertEqual(length, 0.5, accuracy: 0.00001)
    }

    private func assertVector(_ value: SIMD3<Float>, equals expected: SIMD3<Float>, file: StaticString = #filePath, line: UInt = #line) {
        XCTAssertEqual(value.x, expected.x, accuracy: 0.0001, file: file, line: line)
        XCTAssertEqual(value.y, expected.y, accuracy: 0.0001, file: file, line: line)
        XCTAssertEqual(value.z, expected.z, accuracy: 0.0001, file: file, line: line)
    }
}
