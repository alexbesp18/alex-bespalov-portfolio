import XCTest
@testable import PortfolioManager

/// Tests for Portfolio and Holding model types.
final class PortfolioModelTests: XCTestCase {
    
    // MARK: - Holding Tests
    
    func testHoldingInitializesWithDefaults() {
        let holding = Holding()
        
        XCTAssertEqual(holding.ticker, "")
        XCTAssertEqual(holding.allocation, 0.0)
        XCTAssertNotNil(holding.id)
    }
    
    func testHoldingInitializesWithValues() {
        let holding = Holding(ticker: "AAPL", allocation: 60.0)
        
        XCTAssertEqual(holding.ticker, "AAPL")
        XCTAssertEqual(holding.allocation, 60.0)
    }
    
    func testHoldingNegativeAllocationClampedToZero() {
        let holding = Holding(ticker: "AAPL", allocation: -10.0)
        
        XCTAssertEqual(holding.allocation, 0.0)
    }
    
    func testHoldingValidTicker() {
        let validHolding = Holding(ticker: "AAPL", allocation: 50.0)
        let emptyHolding = Holding(ticker: "", allocation: 50.0)
        let whitespaceHolding = Holding(ticker: "   ", allocation: 50.0)
        
        XCTAssertTrue(validHolding.hasValidTicker)
        XCTAssertFalse(emptyHolding.hasValidTicker)
        XCTAssertFalse(whitespaceHolding.hasValidTicker)
    }
    
    func testHoldingValidAllocation() {
        let validHolding = Holding(ticker: "AAPL", allocation: 50.0)
        let zeroHolding = Holding(ticker: "AAPL", allocation: 0.0)
        let maxHolding = Holding(ticker: "AAPL", allocation: 100.0)
        let overHolding = Holding(ticker: "AAPL", allocation: 150.0)
        
        XCTAssertTrue(validHolding.hasValidAllocation)
        XCTAssertTrue(zeroHolding.hasValidAllocation)
        XCTAssertTrue(maxHolding.hasValidAllocation)
        XCTAssertFalse(overHolding.hasValidAllocation) // Over 100 is invalid
    }
    
    func testHoldingHashable() {
        let holding1 = Holding(ticker: "AAPL", allocation: 50.0)
        let holding2 = Holding(ticker: "AAPL", allocation: 50.0)
        
        // Different UUIDs means they're not equal
        XCTAssertNotEqual(holding1, holding2)
        
        // Same holding should equal itself
        XCTAssertEqual(holding1, holding1)
    }
    
    func testHoldingSendable() {
        // This test verifies Sendable conformance compiles
        let holding = Holding(ticker: "AAPL", allocation: 50.0)
        Task {
            let _ = holding // Use in async context
        }
    }
    
    // MARK: - Portfolio Tests
    
    func testPortfolioInitializesWithDefaults() {
        let portfolio = Portfolio()
        
        XCTAssertEqual(portfolio.name, "New Portfolio")
        XCTAssertEqual(portfolio.totalValue, 0.0)
        XCTAssertEqual(portfolio.holdings.count, 1)
        XCTAssertNotNil(portfolio.id)
    }
    
    func testPortfolioInitializesWithValues() {
        let holdings = [
            Holding(ticker: "AAPL", allocation: 60.0),
            Holding(ticker: "MSFT", allocation: 40.0)
        ]
        let portfolio = Portfolio(name: "Tech", totalValue: 100000, holdings: holdings)
        
        XCTAssertEqual(portfolio.name, "Tech")
        XCTAssertEqual(portfolio.totalValue, 100000)
        XCTAssertEqual(portfolio.holdings.count, 2)
    }
    
    func testPortfolioNegativeValueClampedToZero() {
        let portfolio = Portfolio(name: "Test", totalValue: -5000, holdings: [])
        
        XCTAssertEqual(portfolio.totalValue, 0.0)
    }
    
    func testPortfolioEmptyHoldingsCreatesDefault() {
        let portfolio = Portfolio(name: "Empty", totalValue: 50000, holdings: [])
        
        XCTAssertEqual(portfolio.holdings.count, 1)
        XCTAssertEqual(portfolio.holdings[0].ticker, "")
    }
    
    func testPortfolioTotalAllocation() {
        let holdings = [
            Holding(ticker: "AAPL", allocation: 60.0),
            Holding(ticker: "MSFT", allocation: 40.0)
        ]
        let portfolio = Portfolio(name: "Tech", totalValue: 100000, holdings: holdings)
        
        XCTAssertEqual(portfolio.totalAllocation, 100.0)
    }
    
    func testPortfolioIsValidWhenSumsTo100() {
        let validHoldings = [
            Holding(ticker: "AAPL", allocation: 60.0),
            Holding(ticker: "MSFT", allocation: 40.0)
        ]
        let validPortfolio = Portfolio(name: "Valid", totalValue: 100000, holdings: validHoldings)
        
        let invalidHoldings = [
            Holding(ticker: "AAPL", allocation: 60.0),
            Holding(ticker: "MSFT", allocation: 30.0)
        ]
        let invalidPortfolio = Portfolio(name: "Invalid", totalValue: 100000, holdings: invalidHoldings)
        
        XCTAssertTrue(validPortfolio.isValid)
        XCTAssertFalse(invalidPortfolio.isValid)
    }
    
    func testPortfolioIsValidWithTolerance() {
        // 99.995% should be valid (within 0.01 tolerance)
        let holdingsNearlyValid = [
            Holding(ticker: "AAPL", allocation: 59.995),
            Holding(ticker: "MSFT", allocation: 40.0)
        ]
        let nearlyValidPortfolio = Portfolio(name: "Nearly", totalValue: 100000, holdings: holdingsNearlyValid)
        
        XCTAssertTrue(nearlyValidPortfolio.isValid)
    }
    
    func testPortfolioFormattedValue() {
        let portfolio = Portfolio(name: "Test", totalValue: 50000.0, holdings: [])
        
        XCTAssertEqual(portfolio.formattedValue, "$50,000.00")
    }
    
    func testPortfolioDollarAmountForHolding() {
        let holding = Holding(ticker: "AAPL", allocation: 60.0)
        let portfolio = Portfolio(name: "Test", totalValue: 100000, holdings: [holding])
        
        let amount = portfolio.dollarAmount(for: holding)
        
        XCTAssertEqual(amount, 60000.0)
    }
    
    func testPortfolioValidHoldings() {
        let holdings = [
            Holding(ticker: "AAPL", allocation: 50.0),
            Holding(ticker: "", allocation: 30.0),
            Holding(ticker: "MSFT", allocation: 20.0)
        ]
        let portfolio = Portfolio(name: "Mixed", totalValue: 100000, holdings: holdings)
        
        let validHoldings = portfolio.validHoldings
        
        XCTAssertEqual(validHoldings.count, 2)
        XCTAssertTrue(validHoldings.contains { $0.ticker == "AAPL" })
        XCTAssertTrue(validHoldings.contains { $0.ticker == "MSFT" })
    }
    
    func testPortfolioSendable() {
        // This test verifies Sendable conformance compiles
        let portfolio = Portfolio(name: "Test", totalValue: 50000, holdings: [])
        Task {
            let _ = portfolio // Use in async context
        }
    }
    
    // MARK: - PortfolioData Tests
    
    func testPortfolioDataSampleData() {
        let sampleData = PortfolioData.sampleData
        
        XCTAssertEqual(sampleData.portfolios.count, 2)
        XCTAssertTrue(sampleData.portfolios[0].isValid)
        XCTAssertTrue(sampleData.portfolios[1].isValid)
    }
    
    func testPortfolioDataSendable() {
        // This test verifies Sendable conformance compiles
        let data = PortfolioData.sampleData
        Task {
            let _ = data // Use in async context
        }
    }
    
    // MARK: - Codable Tests
    
    func testHoldingEncodesAndDecodes() throws {
        let original = Holding(ticker: "AAPL", allocation: 60.0)
        
        let encoder = JSONEncoder()
        let data = try encoder.encode(original)
        
        let decoder = JSONDecoder()
        let decoded = try decoder.decode(Holding.self, from: data)
        
        XCTAssertEqual(decoded.ticker, original.ticker)
        XCTAssertEqual(decoded.allocation, original.allocation)
    }
    
    func testPortfolioEncodesAndDecodes() throws {
        let holdings = [
            Holding(ticker: "AAPL", allocation: 60.0),
            Holding(ticker: "MSFT", allocation: 40.0)
        ]
        let original = Portfolio(name: "Test", totalValue: 100000, holdings: holdings)
        
        let encoder = JSONEncoder()
        let data = try encoder.encode(original)
        
        let decoder = JSONDecoder()
        let decoded = try decoder.decode(Portfolio.self, from: data)
        
        XCTAssertEqual(decoded.name, original.name)
        XCTAssertEqual(decoded.totalValue, original.totalValue)
        XCTAssertEqual(decoded.holdings.count, original.holdings.count)
    }
    
    func testPortfolioDataEncodesAndDecodes() throws {
        let original = PortfolioData.sampleData
        
        let encoder = JSONEncoder()
        let data = try encoder.encode(original)
        
        let decoder = JSONDecoder()
        let decoded = try decoder.decode(PortfolioData.self, from: data)
        
        XCTAssertEqual(decoded.portfolios.count, original.portfolios.count)
    }
}
