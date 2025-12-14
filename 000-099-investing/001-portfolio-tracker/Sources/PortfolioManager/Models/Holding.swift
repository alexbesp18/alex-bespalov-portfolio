import Foundation

// MARK: - Holding Model

/// Represents a single holding within a portfolio.
///
/// A holding consists of a ticker symbol and an allocation percentage.
/// The allocation represents what percentage of the portfolio's total value
/// is invested in this particular security.
///
/// This type conforms to `Sendable` for safe use across concurrency domains.
///
/// Example:
/// ```swift
/// let appleHolding = Holding(ticker: "AAPL", allocation: 60.0)
/// ```
public struct Holding: Codable, Identifiable, Hashable, Sendable {
    
    // MARK: - Properties
    
    /// Unique identifier for the holding
    public var id = UUID()
    
    /// Stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL")
    public var ticker: String
    
    /// Allocation percentage (0-100) representing portion of portfolio
    public var allocation: Double
    
    // MARK: - Initialization
    
    /// Creates a new holding with the specified ticker and allocation.
    ///
    /// - Parameters:
    ///   - ticker: The stock ticker symbol. Defaults to empty string.
    ///   - allocation: The allocation percentage (0-100). Defaults to 0.0.
    public init(ticker: String = "", allocation: Double = 0.0) {
        self.ticker = ticker
        self.allocation = max(0, allocation) // Ensure non-negative
    }
}

// MARK: - Validation

extension Holding {
    
    /// Indicates whether the holding has a valid ticker symbol.
    public var hasValidTicker: Bool {
        !ticker.trimmingCharacters(in: .whitespaces).isEmpty
    }
    
    /// Indicates whether the allocation is within valid range (0-100).
    public var hasValidAllocation: Bool {
        allocation >= 0 && allocation <= 100
    }
    
    /// Indicates whether the holding is fully valid (has ticker and valid allocation).
    public var isValid: Bool {
        hasValidTicker && hasValidAllocation
    }
}
