// Shared by the app and the focused SwiftPM tests. No rendering dependency.
enum NavigationMath {
    /// Preserve the local point underneath an anchor when uniformly scaling a root.
    static func scaledPosition(_ position: SIMD3<Float>, around anchor: SIMD3<Float>, ratio: Float) -> SIMD3<Float> {
        anchor + (position - anchor) * ratio
    }

    static func boundedStep(_ delta: SIMD3<Float>, maximum: Float) -> SIMD3<Float> {
        let length = (delta.x * delta.x + delta.y * delta.y + delta.z * delta.z).squareRoot()
        return length > maximum && length > 0 ? delta * (maximum / length) : delta
    }
}

struct WorldDrag {
    private(set) var active = false
    private var rootStart = SIMD3<Float>.zero
    private var handStart = SIMD3<Float>.zero
    private var gain: Float = 1

    mutating func begin(root: SIMD3<Float>, hand: SIMD3<Float>, gain: Float) {
        rootStart = root
        handStart = hand
        self.gain = min(max(gain, 1), 12)
        active = true
    }

    func position(current: SIMD3<Float>, hand: SIMD3<Float>) -> SIMD3<Float> {
        guard active else { return current }
        // Native ACCVR precedent: fixed-holder hand delta; moving the root cannot
        // feed back into input. Damping 0.35 is the device-reviewed reference.
        let target = rootStart + (hand - handStart) * gain
        return current + NavigationMath.boundedStep((target - current) * 0.35, maximum: 0.5)
    }

    mutating func end() {
        // Hold the output immediately. No tail sample, velocity, or inertial tick.
        active = false
    }
}
