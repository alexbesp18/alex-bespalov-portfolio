import Foundation

// MARK: - Combined Holding Model

/// Represents a holding's weighted allocation across multiple portfolios.
///
/// Used for combined portfolio analytics, where holdings from multiple
/// portfolios are aggregated by ticker symbol with value-weighted allocations.
///
/// Example:
/// ```swift
/// // AAPL appears in two portfolios with different weights
/// let combined = CombinedHolding(
///     ticker: "AAPL",
///     allocation: 56.0,      // Weighted average
///     dollarAmount: 56000.0  // Total dollar exposure
/// )
/// ```
public struct CombinedHolding: Identifiable, Hashable, Sendable {
    
    // MARK: - Properties
    
    /// Unique identifier for the combined holding
    public let id: UUID
    
    /// Stock ticker symbol
    public let ticker: String
    
    /// Weighted allocation percentage across all portfolios (0-100)
    public let allocation: Double
    
    /// Total dollar amount invested in this ticker across all portfolios
    public let dollarAmount: Double
    
    // MARK: - Initialization
    
    /// Creates a new combined holding with the specified values.
    ///
    /// - Parameters:
    ///   - ticker: The stock ticker symbol.
    ///   - allocation: The weighted allocation percentage (0-100).
    ///   - dollarAmount: The total dollar amount across portfolios.
    public init(ticker: String, allocation: Double, dollarAmount: Double) {
        self.id = UUID()
        self.ticker = ticker
        self.allocation = allocation
        self.dollarAmount = dollarAmount
    }
}

// MARK: - Formatting

extension CombinedHolding {
    
    /// The allocation formatted as a percentage string.
    ///
    /// Example: "56.00%"
    public var formattedAllocation: String {
        String(format: "%.2f%%", allocation)
    }
    
    /// The dollar amount formatted as a currency string.
    ///
    /// Example: "$56,000.00"
    public var formattedDollarAmount: String {
        CurrencyFormatter.shared.format(dollarAmount)
    }
}

