import Foundation

/// Main-actor state can change while a photo texture is loading. Only the latest
/// request may commit; Hide, navigation, reset and exit invalidate pending work.
@MainActor
final class PhotoAlignmentRequest {
    private var generation = UUID()

    func invalidate() { generation = UUID() }

    func load<Value>(_ operation: () async throws -> Value) async throws -> Value? {
        invalidate()
        let request = generation
        do {
            let value = try await operation()
            guard generation == request, !Task.isCancelled else { return nil }
            return value
        } catch {
            // A stale failure must not replace a newer alignment's status either.
            guard generation == request, !Task.isCancelled else { return nil }
            throw error
        }
    }
}
