import Foundation

// MARK: - Portfolio Data Container

/// Container for persisting multiple portfolios to storage.
///
/// This struct wraps the portfolio array for JSON encoding/decoding,
/// providing a consistent structure for file-based persistence.
///
/// This type conforms to `Sendable` for safe use across concurrency domains.
public struct PortfolioData: Codable, Sendable {
    
    /// The collection of portfolios to persist
    public var portfolios: [Portfolio]
    
    /// Creates a new portfolio data container.
    ///
    /// - Parameter portfolios: The portfolios to store. Defaults to empty array.
    public init(portfolios: [Portfolio] = []) {
        self.portfolios = portfolios
    }
}

// MARK: - Default Data

extension PortfolioData {
    
    /// Sample portfolio data for first-time users or testing.
    ///
    /// Contains two example portfolios demonstrating typical usage:
    /// - Tech Growth: 60% AAPL, 40% MSFT
    /// - Balanced: 50% AAPL, 30% GOOGL, 20% MSFT
    public static var sampleData: PortfolioData {
        PortfolioData(portfolios: [
            Portfolio(
                name: "Tech Growth",
                totalValue: 60000,
                holdings: [
                    Holding(ticker: "AAPL", allocation: 60),
                    Holding(ticker: "MSFT", allocation: 40)
                ]
            ),
            Portfolio(
                name: "Balanced",
                totalValue: 40000,
                holdings: [
                    Holding(ticker: "AAPL", allocation: 50),
                    Holding(ticker: "GOOGL", allocation: 30),
                    Holding(ticker: "MSFT", allocation: 20)
                ]
            )
        ])
    }
}
