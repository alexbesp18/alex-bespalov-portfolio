import XCTest
@testable import PortfolioManager

/// Tests for PortfolioRepository implementations.
final class PortfolioRepositoryTests: XCTestCase {
    
    // MARK: - InMemoryPortfolioRepository Tests
    
    func testInMemoryRepositoryInitializesEmpty() throws {
        let repository = InMemoryPortfolioRepository()
        
        let portfolios = try repository.load()
        
        XCTAssertTrue(portfolios.isEmpty)
        XCTAssertFalse(repository.hasPersistedData)
    }
    
    func testInMemoryRepositoryInitializesWithData() throws {
        let initialData = [
            Portfolio(name: "Test", totalValue: 10000, holdings: [
                Holding(ticker: "AAPL", allocation: 100)
            ])
        ]
        let repository = InMemoryPortfolioRepository(initialData: initialData)
        
        let portfolios = try repository.load()
        
        XCTAssertEqual(portfolios.count, 1)
        XCTAssertTrue(repository.hasPersistedData)
    }
    
    func testInMemoryRepositorySaveAndLoad() throws {
        let repository = InMemoryPortfolioRepository()
        let portfolios = [
            Portfolio(name: "Saved", totalValue: 50000, holdings: [
                Holding(ticker: "MSFT", allocation: 100)
            ])
        ]
        
        try repository.save(portfolios)
        let loaded = try repository.load()
        
        XCTAssertEqual(loaded.count, 1)
        XCTAssertEqual(loaded.first?.name, "Saved")
        XCTAssertTrue(repository.hasPersistedData)
    }
    
    func testInMemoryRepositoryOverwritesOnSave() throws {
        let repository = InMemoryPortfolioRepository()
        
        // First save
        try repository.save([Portfolio(name: "First", totalValue: 1000, holdings: [])])
        
        // Second save should overwrite
        try repository.save([
            Portfolio(name: "Second", totalValue: 2000, holdings: []),
            Portfolio(name: "Third", totalValue: 3000, holdings: [])
        ])
        
        let loaded = try repository.load()
        
        XCTAssertEqual(loaded.count, 2)
        XCTAssertTrue(loaded.contains { $0.name == "Second" })
        XCTAssertTrue(loaded.contains { $0.name == "Third" })
        XCTAssertFalse(loaded.contains { $0.name == "First" })
    }
    
    func testInMemoryRepositoryThreadSafety() async throws {
        let repository = InMemoryPortfolioRepository()
        
        // Concurrent saves and loads
        await withTaskGroup(of: Void.self) { group in
            for i in 0..<50 {
                group.addTask {
                    let portfolios = [Portfolio(name: "Portfolio \(i)", totalValue: Double(i) * 1000, holdings: [])]
                    try? repository.save(portfolios)
                }
                group.addTask {
                    _ = try? repository.load()
                }
            }
        }
        
        // Should not crash and should have data
        let finalData = try repository.load()
        XCTAssertFalse(finalData.isEmpty)
    }
}

// MARK: - PortfolioError Tests

final class PortfolioErrorTests: XCTestCase {
    
    func testDirectoryCreationFailedError() {
        let underlyingError = NSError(domain: "test", code: 1, userInfo: nil)
        let error = PortfolioError.directoryCreationFailed(underlying: underlyingError)
        
        XCTAssertNotNil(error.errorDescription)
        XCTAssertNotNil(error.failureReason)
        XCTAssertNotNil(error.recoverySuggestion)
        XCTAssertTrue(error.errorDescription!.contains("directory"))
    }
    
    func testLoadFailedError() {
        let underlyingError = NSError(domain: "test", code: 2, userInfo: nil)
        let error = PortfolioError.loadFailed(underlying: underlyingError)
        
        XCTAssertNotNil(error.errorDescription)
        XCTAssertTrue(error.errorDescription!.contains("load"))
    }
    
    func testSaveFailedError() {
        let underlyingError = NSError(domain: "test", code: 3, userInfo: nil)
        let error = PortfolioError.saveFailed(underlying: underlyingError)
        
        XCTAssertNotNil(error.errorDescription)
        XCTAssertTrue(error.errorDescription!.contains("save"))
    }
    
    func testInvalidDataError() {
        let error = PortfolioError.invalidData(reason: "Corrupted JSON")
        
        XCTAssertNotNil(error.errorDescription)
        XCTAssertTrue(error.errorDescription!.contains("Corrupted JSON"))
    }
    
    func testStorageUnavailableError() {
        let error = PortfolioError.storageUnavailable
        
        XCTAssertNotNil(error.errorDescription)
        XCTAssertNotNil(error.failureReason)
        XCTAssertNotNil(error.recoverySuggestion)
    }
    
    func testErrorsSendable() {
        // Verify Sendable conformance compiles
        let error = PortfolioError.storageUnavailable
        Task {
            let _ = error // Use in async context
        }
    }
}

