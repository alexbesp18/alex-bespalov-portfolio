import Foundation

// MARK: - Portfolio Model

/// Represents an investment portfolio containing multiple holdings.
///
/// A portfolio has a name, total value, and a collection of holdings.
/// The sum of all holding allocations should equal 100% for the portfolio
/// to be considered valid.
///
/// This type conforms to `Sendable` for safe use across concurrency domains.
///
/// Example:
/// ```swift
/// let portfolio = Portfolio(
///     name: "Tech Growth",
///     totalValue: 60000,
///     holdings: [
///         Holding(ticker: "AAPL", allocation: 60),
///         Holding(ticker: "MSFT", allocation: 40)
///     ]
/// )
/// ```
public struct Portfolio: Codable, Identifiable, Hashable, Sendable {
    
    // MARK: - Properties
    
    /// Unique identifier for the portfolio
    public var id = UUID()
    
    /// Display name for the portfolio
    public var name: String
    
    /// Total monetary value of the portfolio in USD (must be >= 0)
    public var totalValue: Double {
        didSet {
            // Ensure non-negative value
            if totalValue < 0 {
                totalValue = 0
            }
        }
    }
    
    /// Collection of holdings within this portfolio
    public var holdings: [Holding]
    
    // MARK: - Initialization
    
    /// Creates a new portfolio with the specified properties.
    ///
    /// - Parameters:
    ///   - name: The portfolio name. Defaults to "New Portfolio".
    ///   - totalValue: The total value in USD (must be >= 0). Defaults to 0.0.
    ///   - holdings: Array of holdings. If empty, creates one empty holding.
    public init(name: String = "New Portfolio", totalValue: Double = 0.0, holdings: [Holding] = []) {
        self.name = name
        self.totalValue = max(0, totalValue) // Ensure non-negative
        self.holdings = holdings.isEmpty ? [Holding()] : holdings
    }
    
    // MARK: - Computed Properties
    
    /// The sum of all holding allocations in this portfolio.
    ///
    /// A valid portfolio should have a total allocation of exactly 100%.
    public var totalAllocation: Double {
        holdings.reduce(0) { $0 + $1.allocation }
    }
    
    /// Indicates whether the portfolio allocations sum to exactly 100%.
    ///
    /// Uses a tolerance of 0.01% to account for floating-point precision.
    public var isValid: Bool {
        abs(totalAllocation - 100.0) < 0.01
    }
    
    /// The total value formatted as a currency string.
    ///
    /// Example: "$60,000.00"
    public var formattedValue: String {
        CurrencyFormatter.shared.format(totalValue)
    }
}

// MARK: - Holding Management

extension Portfolio {
    
    /// Returns holdings that have valid ticker symbols.
    public var validHoldings: [Holding] {
        holdings.filter { $0.hasValidTicker }
    }
    
    /// Calculates the dollar amount for a specific holding.
    ///
    /// - Parameter holding: The holding to calculate the value for.
    /// - Returns: The dollar value based on allocation percentage.
    public func dollarAmount(for holding: Holding) -> Double {
        (holding.allocation / 100.0) * totalValue
    }
}
