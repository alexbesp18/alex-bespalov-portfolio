import XCTest
@testable import PortfolioManager

/// Tests for PortfolioStore state management.
///
/// Uses `InMemoryPortfolioRepository` for isolated testing without
/// affecting user data or file system.
@MainActor
final class PortfolioStoreTests: XCTestCase {
    
    // MARK: - Properties
    
    var store: PortfolioStore!
    var repository: InMemoryPortfolioRepository!
    
    // MARK: - Setup
    
    override func setUp() async throws {
        try await super.setUp()
        repository = InMemoryPortfolioRepository()
        store = PortfolioStore(repository: repository)
    }
    
    override func tearDown() async throws {
        store = nil
        repository = nil
        try await super.tearDown()
    }
    
    // MARK: - Initialization Tests
    
    func testStoreInitializesWithSampleDataWhenEmpty() {
        // Given an empty repository
        let emptyRepo = InMemoryPortfolioRepository()
        
        // When creating a store
        let testStore = PortfolioStore(repository: emptyRepo)
        
        // Then it should have sample data
        XCTAssertFalse(testStore.portfolios.isEmpty)
        XCTAssertEqual(testStore.portfolios.count, 2) // Sample data has 2 portfolios
    }
    
    func testStoreInitializesWithPersistedData() throws {
        // Given a repository with existing data
        let existingPortfolios = [
            Portfolio(name: "Existing", totalValue: 10000, holdings: [
                Holding(ticker: "TEST", allocation: 100)
            ])
        ]
        let repoWithData = InMemoryPortfolioRepository(initialData: existingPortfolios)
        
        // When creating a store
        let testStore = PortfolioStore(repository: repoWithData)
        
        // Then it should load the existing data
        XCTAssertEqual(testStore.portfolios.count, 1)
        XCTAssertEqual(testStore.portfolios.first?.name, "Existing")
    }
    
    // MARK: - CRUD Tests
    
    func testAddPortfolio() {
        let initialCount = store.portfolios.count
        
        store.addPortfolio()
        
        XCTAssertEqual(store.portfolios.count, initialCount + 1)
    }
    
    func testAddedPortfolioHasCorrectDefaults() {
        // Clear existing portfolios
        while !store.portfolios.isEmpty {
            store.deletePortfolio(store.portfolios.first!)
        }
        
        store.addPortfolio()
        
        let newPortfolio = store.portfolios.first!
        
        XCTAssertEqual(newPortfolio.name, "Portfolio 1")
        XCTAssertEqual(newPortfolio.totalValue, 50000.0)
        XCTAssertEqual(newPortfolio.holdings.count, 2)
        XCTAssertTrue(newPortfolio.isValid)
    }
    
    func testDeletePortfolio() {
        let initialCount = store.portfolios.count
        guard let portfolioToDelete = store.portfolios.first else {
            XCTFail("No portfolios to delete")
            return
        }
        
        store.deletePortfolio(portfolioToDelete)
        
        XCTAssertEqual(store.portfolios.count, initialCount - 1)
        XCTAssertFalse(store.portfolios.contains { $0.id == portfolioToDelete.id })
    }
    
    func testUpdatePortfolio() {
        guard var portfolioToUpdate = store.portfolios.first else {
            XCTFail("No portfolios to update")
            return
        }
        
        let newName = "Updated Portfolio"
        portfolioToUpdate.name = newName
        
        store.updatePortfolio(portfolioToUpdate)
        
        let updated = store.portfolios.first { $0.id == portfolioToUpdate.id }
        XCTAssertEqual(updated?.name, newName)
    }
    
    func testUpdateNonExistentPortfolioDoesNothing() {
        let nonExistentPortfolio = Portfolio(name: "Non-existent", totalValue: 1000, holdings: [])
        let initialCount = store.portfolios.count
        
        store.updatePortfolio(nonExistentPortfolio)
        
        XCTAssertEqual(store.portfolios.count, initialCount)
    }
    
    // MARK: - Analytics Tests
    
    func testTotalPortfolioValue() {
        // Clear and add known portfolios
        while !store.portfolios.isEmpty {
            store.deletePortfolio(store.portfolios.first!)
        }
        
        // Add portfolios with known values
        store.addPortfolio() // $50,000
        store.addPortfolio() // $50,000
        
        XCTAssertEqual(store.totalPortfolioValue, 100000.0)
    }
    
    func testCalculateCombinedPortfolioEmpty() {
        // Clear all portfolios
        while !store.portfolios.isEmpty {
            store.deletePortfolio(store.portfolios.first!)
        }
        
        let combined = store.calculateCombinedPortfolio()
        
        XCTAssertTrue(combined.isEmpty)
    }
    
    func testCalculateCombinedPortfolioReturnsCombinedHoldings() {
        let combined = store.calculateCombinedPortfolio()
        
        // Should return CombinedHolding structs
        XCTAssertFalse(combined.isEmpty)
        
        // Verify it's the correct type with expected properties
        if let first = combined.first {
            XCTAssertFalse(first.ticker.isEmpty)
            XCTAssertGreaterThan(first.allocation, 0)
            XCTAssertGreaterThan(first.dollarAmount, 0)
            XCTAssertNotNil(first.id)
        }
    }
    
    func testCalculateCombinedPortfolioSumsTo100() {
        let combined = store.calculateCombinedPortfolio()
        
        guard !combined.isEmpty else { return }
        
        // Total allocation should sum to approximately 100
        let totalAllocation = combined.reduce(0.0) { $0 + $1.allocation }
        XCTAssertEqual(totalAllocation, 100.0, accuracy: 0.01)
    }
    
    func testCombinedPortfolioSortedByAllocation() {
        let combined = store.calculateCombinedPortfolio()
        
        guard combined.count > 1 else { return }
        
        for i in 0..<(combined.count - 1) {
            XCTAssertGreaterThanOrEqual(combined[i].allocation, combined[i + 1].allocation)
        }
    }
    
    func testCombinedPortfolioDollarAmounts() {
        let combined = store.calculateCombinedPortfolio()
        let totalValue = store.totalPortfolioValue
        
        for item in combined {
            let expectedAmount = (item.allocation / 100.0) * totalValue
            XCTAssertEqual(item.dollarAmount, expectedAmount, accuracy: 0.01)
        }
    }
    
    // MARK: - Persistence Tests
    
    func testPortfoliosAreSavedToRepository() async throws {
        // Add a new portfolio
        store.addPortfolio()
        
        // Wait for debounced save
        try await Task.sleep(nanoseconds: 600_000_000) // 0.6 seconds
        
        // Verify it was saved
        let saved = try repository.load()
        XCTAssertEqual(saved.count, store.portfolios.count)
    }
    
    // MARK: - Error Handling Tests
    
    func testStoreHasNoErrorInitially() {
        XCTAssertNil(store.lastError)
    }
    
    func testClearErrorResetsState() {
        // This test verifies the clearError method works
        store.clearError()
        XCTAssertNil(store.lastError)
    }
}

// MARK: - CombinedHolding Tests

final class CombinedHoldingTests: XCTestCase {
    
    func testCombinedHoldingInitialization() {
        let holding = CombinedHolding(ticker: "AAPL", allocation: 56.0, dollarAmount: 56000.0)
        
        XCTAssertEqual(holding.ticker, "AAPL")
        XCTAssertEqual(holding.allocation, 56.0)
        XCTAssertEqual(holding.dollarAmount, 56000.0)
        XCTAssertNotNil(holding.id)
    }
    
    func testCombinedHoldingFormattedAllocation() {
        let holding = CombinedHolding(ticker: "AAPL", allocation: 56.78, dollarAmount: 56780.0)
        
        XCTAssertEqual(holding.formattedAllocation, "56.78%")
    }
    
    func testCombinedHoldingFormattedDollarAmount() {
        let holding = CombinedHolding(ticker: "AAPL", allocation: 56.0, dollarAmount: 56000.0)
        
        XCTAssertEqual(holding.formattedDollarAmount, "$56,000.00")
    }
    
    func testCombinedHoldingIdentifiable() {
        let holding1 = CombinedHolding(ticker: "AAPL", allocation: 50.0, dollarAmount: 50000.0)
        let holding2 = CombinedHolding(ticker: "AAPL", allocation: 50.0, dollarAmount: 50000.0)
        
        // Each holding should have a unique ID
        XCTAssertNotEqual(holding1.id, holding2.id)
    }
    
    func testCombinedHoldingHashable() {
        let holding1 = CombinedHolding(ticker: "AAPL", allocation: 50.0, dollarAmount: 50000.0)
        let holding2 = CombinedHolding(ticker: "MSFT", allocation: 50.0, dollarAmount: 50000.0)
        
        var set = Set<CombinedHolding>()
        set.insert(holding1)
        set.insert(holding2)
        
        XCTAssertEqual(set.count, 2)
    }
}
