import XCTest
@testable import FlatironNavigationMath

@MainActor
final class PhotoAlignmentRequestTests: XCTestCase {
    /// Explicit rendezvous: no sleeps, texture cache, device or scheduler timing assumptions.
    private final class DeferredPhoto {
        let started = AsyncStream<Void>.makeStream()
        var completion: CheckedContinuation<Int, Error>?

        func load() async throws -> Int {
            try await withCheckedThrowingContinuation { continuation in
                completion = continuation
                started.continuation.yield(())
                started.continuation.finish()
            }
        }

        func waitUntilLoading() async {
            for await _ in started.stream { break }
        }
    }

    func testHideOrResetWhileLoadingDoesNotRestoreOverlay() async throws {
        let request = PhotoAlignmentRequest()
        let photo = DeferredPhoto()
        let pending = Task { try await request.load { try await photo.load() } }
        await photo.waitUntilLoading()
        request.invalidate() // Same entry point used by both scenes' clearAlignment.
        photo.completion?.resume(returning: 2)
        let result = try await pending.value
        XCTAssertNil(result)
    }

    func testNewerAlignmentWinsEvenWhenOlderPhotoFinishesLast() async throws {
        let request = PhotoAlignmentRequest()
        let older = DeferredPhoto(), newer = DeferredPhoto()
        let first = Task { try await request.load { try await older.load() } }
        await older.waitUntilLoading()
        let second = Task { try await request.load { try await newer.load() } }
        await newer.waitUntilLoading()
        newer.completion?.resume(returning: 8)
        let latest = try await second.value
        XCTAssertEqual(latest, 8)
        older.completion?.resume(returning: 2)
        let stale = try await first.value
        XCTAssertNil(stale)
    }

    func testStaleLoadFailureDoesNotReplaceNewerStatus() async throws {
        let request = PhotoAlignmentRequest()
        let photo = DeferredPhoto()
        let pending = Task { try await request.load { try await photo.load() } }
        await photo.waitUntilLoading()
        request.invalidate()
        photo.completion?.resume(throwing: CocoaError(.fileReadCorruptFile))
        let result = try await pending.value
        XCTAssertNil(result)
    }

    func testCancelledTaskCannotApplyTextureEvenIfLoaderIgnoresCancellation() async throws {
        let request = PhotoAlignmentRequest()
        let photo = DeferredPhoto()
        let pending = Task { try await request.load { try await photo.load() } }
        await photo.waitUntilLoading()
        pending.cancel()
        photo.completion?.resume(returning: 2)
        let result = try await pending.value
        XCTAssertNil(result)
    }

    func testCurrentLoadFailureIsStillReported() async {
        let request = PhotoAlignmentRequest()
        do {
            let _: Int? = try await request.load { throw CocoaError(.fileReadCorruptFile) }
            XCTFail("A current load failure must reach the photo panel")
        } catch {
            XCTAssertEqual((error as NSError).code, CocoaError.fileReadCorruptFile.rawValue)
        }
    }
}
