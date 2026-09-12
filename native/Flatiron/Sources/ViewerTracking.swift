import ARKit
import QuartzCore
import simd

/// Native UnRealityKit precedent: URKLaser.swift / URKHeadTracker at e7ab49b.
/// DeviceAnchor exposes a tracked world pose; render-only head anchoring is not
/// used as a substitute for a measured camera position.
@MainActor
final class ViewerTracking {
    private let session = ARKitSession()
    private var provider: WorldTrackingProvider?
    private var eventTask: Task<Void, Never>?

    func start() async {
        stop()
        guard WorldTrackingProvider.isSupported else {
            Receipt.write("tracking-unavailable", ["reason": "WorldTrackingProvider unsupported"])
            return
        }
        let authorization = await session.requestAuthorization(for: WorldTrackingProvider.requiredAuthorizations)
        guard authorization.values.allSatisfy({ $0 == .allowed }) else {
            Receipt.write("tracking-unavailable", ["reason": "authorization unavailable"])
            return
        }
        let next = WorldTrackingProvider()
        provider = next
        eventTask = Task { [session] in
            for await event in session.events {
                if Task.isCancelled { break }
                Receipt.write("tracking-event", ["event": String(describing: event)])
            }
        }
        do { try await session.run([next]) }
        catch {
            Receipt.write("tracking-unavailable", ["reason": error.localizedDescription])
            provider = nil
        }
    }

    func pose() -> simd_float4x4? {
        guard let provider, provider.state == .running,
              let anchor = provider.queryDeviceAnchor(atTimestamp: CACurrentMediaTime()),
              anchor.isTracked else { return nil }
        let pose = anchor.originFromAnchorTransform
        guard (0..<4).allSatisfy({ column in (0..<4).allSatisfy({ pose[column][$0].isFinite }) }) else { return nil }
        return pose
    }

    func stop() {
        eventTask?.cancel()
        eventTask = nil
        session.stop()
        provider = nil
    }
}
