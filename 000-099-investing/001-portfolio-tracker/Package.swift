// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "PortfolioManager",
    platforms: [
        .macOS(.v13),
        .iOS(.v16)
    ],
    products: [
        .executable(
            name: "PortfolioManager",
            targets: ["PortfolioManager"]
        )
    ],
    targets: [
        .executableTarget(
            name: "PortfolioManager",
            path: "Sources/PortfolioManager"
        ),
        .testTarget(
            name: "PortfolioManagerTests",
            dependencies: ["PortfolioManager"],
            path: "Tests/PortfolioManagerTests"
        )
    ]
)
