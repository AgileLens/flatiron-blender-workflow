// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "FlatironNavigationMath",
    products: [.library(name: "FlatironNavigationMath", targets: ["FlatironNavigationMath"])],
    targets: [
        .target(name: "FlatironNavigationMath", path: "Sources",
                exclude: ["FlatironApp.swift", "FlatironImmersive.swift", "ViewerTracking.swift"],
                sources: ["NavigationMath.swift"]),
        .testTarget(name: "FlatironNavigationMathTests", dependencies: ["FlatironNavigationMath"], path: "Tests")
    ]
)
