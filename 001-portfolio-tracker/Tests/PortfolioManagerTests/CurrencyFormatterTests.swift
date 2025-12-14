import XCTest
@testable import PortfolioManager

/// Tests for currency formatting utilities.
final class CurrencyFormatterTests: XCTestCase {
    
    // MARK: - Standard Formatting Tests
    
    func testFormatWholeNumber() {
        let result = CurrencyFormatter.shared.format(50000.0)
        
        XCTAssertEqual(result, "$50,000.00")
    }
    
    func testFormatWithCents() {
        let result = CurrencyFormatter.shared.format(1234.56)
        
        XCTAssertEqual(result, "$1,234.56")
    }
    
    func testFormatZero() {
        let result = CurrencyFormatter.shared.format(0.0)
        
        XCTAssertEqual(result, "$0.00")
    }
    
    func testFormatSmallAmount() {
        let result = CurrencyFormatter.shared.format(0.99)
        
        XCTAssertEqual(result, "$0.99")
    }
    
    func testFormatLargeAmount() {
        let result = CurrencyFormatter.shared.format(1000000.0)
        
        XCTAssertEqual(result, "$1,000,000.00")
    }
    
    func testFormatNegativeAmount() {
        let result = CurrencyFormatter.shared.format(-500.0)
        
        XCTAssertTrue(result.contains("500"))
        XCTAssertTrue(result.contains("-") || result.contains("("))
    }
    
    // MARK: - Compact Formatting Tests
    
    func testFormatCompactWholeNumber() {
        let result = CurrencyFormatter.shared.formatCompact(50000.0)
        
        XCTAssertEqual(result, "$50,000")
    }
    
    func testFormatCompactWithCents() {
        let result = CurrencyFormatter.shared.formatCompact(1234.56)
        
        XCTAssertEqual(result, "$1,234.56")
    }
    
    func testFormatCompactZero() {
        let result = CurrencyFormatter.shared.formatCompact(0.0)
        
        XCTAssertEqual(result, "$0")
    }
    
    // MARK: - Double Extension Tests
    
    func testDoubleAsCurrency() {
        let value: Double = 12345.67
        
        XCTAssertEqual(value.asCurrency, "$12,345.67")
    }
    
    func testDoubleAsCurrencyZero() {
        let value: Double = 0.0
        
        XCTAssertEqual(value.asCurrency, "$0.00")
    }
    
    func testDoubleAsCurrencyCompact() {
        let wholeValue: Double = 50000.0
        let fractionalValue: Double = 1234.56
        
        XCTAssertEqual(wholeValue.asCurrencyCompact, "$50,000")
        XCTAssertEqual(fractionalValue.asCurrencyCompact, "$1,234.56")
    }
    
    // MARK: - Singleton Tests
    
    func testSharedInstanceIsSame() {
        let formatter1 = CurrencyFormatter.shared
        let formatter2 = CurrencyFormatter.shared
        
        XCTAssertTrue(formatter1 === formatter2)
    }
    
    // MARK: - Precision Tests
    
    func testRoundingBehavior() {
        // Should round to 2 decimal places
        let result1 = CurrencyFormatter.shared.format(100.999)
        let result2 = CurrencyFormatter.shared.format(100.991)
        
        XCTAssertEqual(result1, "$101.00")
        XCTAssertEqual(result2, "$100.99")
    }
    
    func testVerySmallFraction() {
        let result = CurrencyFormatter.shared.format(0.001)
        
        XCTAssertEqual(result, "$0.00")
    }
    
    // MARK: - Thread Safety Tests
    
    func testFormatterIsThreadSafe() async {
        // Run multiple concurrent formatting operations
        await withTaskGroup(of: String.self) { group in
            for i in 0..<100 {
                group.addTask {
                    return CurrencyFormatter.shared.format(Double(i) * 1000)
                }
            }
            
            var results: [String] = []
            for await result in group {
                results.append(result)
            }
            
            XCTAssertEqual(results.count, 100)
        }
    }
}
