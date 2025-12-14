import SwiftUI
import Foundation
import Combine
import os.log

// MARK: - Portfolio Store

/// Central state management for portfolio data.
///
/// `PortfolioStore` is an observable object that manages the collection of portfolios,
/// handles persistence through a repository, and provides combined portfolio calculations.
///
/// Features:
/// - Automatic persistence with debounced saves
/// - CRUD operations for portfolios
/// - Combined portfolio analytics
/// - Dependency injection for testability
///
/// Example:
/// ```swift
/// @StateObject private var store = PortfolioStore()
///
/// // Add a new portfolio
/// store.addPortfolio()
///
/// // Get combined allocations
/// let combined = store.calculateCombinedPortfolio()
/// ```
@MainActor
public final class PortfolioStore: ObservableObject {
    
    // MARK: - Published Properties
    
    /// The collection of portfolios managed by this store.
    @Published public var portfolios: [Portfolio] = []
    
    /// The last error that occurred, if any.
    @Published public private(set) var lastError: PortfolioError?
    
    // MARK: - Private Properties
    
    /// Logger for diagnostics and error reporting.
    private let logger = Logger(subsystem: "com.portfolio.manager", category: "PortfolioStore")
    
    /// Repository for portfolio persistence.
    private let repository: PortfolioRepository
    
    /// Combine subscriptions for auto-save functionality.
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Initialization
    
    /// Creates a new portfolio store with the default file repository.
    ///
    /// Falls back to in-memory storage if file repository fails to initialize.
    public convenience init() {
        do {
            let repository = try FilePortfolioRepository()
            self.init(repository: repository)
        } catch {
            // Fallback to in-memory if file storage unavailable
            let logger = Logger(subsystem: "com.portfolio.manager", category: "PortfolioStore")
            logger.warning("File repository unavailable, using in-memory storage: \(error.localizedDescription)")
            self.init(repository: InMemoryPortfolioRepository(initialData: PortfolioData.sampleData.portfolios))
        }
    }
    
    /// Creates a new portfolio store with a custom repository.
    ///
    /// Enables dependency injection for testing.
    ///
    /// - Parameter repository: The repository to use for persistence.
    public init(repository: PortfolioRepository) {
        self.repository = repository
        loadPortfolios()
        setupAutoSave()
    }
    
    // MARK: - Auto-Save Setup
    
    /// Configures automatic saving when portfolios change.
    private func setupAutoSave() {
        $portfolios
            .debounce(for: .seconds(0.5), scheduler: RunLoop.main)
            .sink { [weak self] _ in
                self?.savePortfolios()
            }
            .store(in: &cancellables)
    }
    
    // MARK: - CRUD Operations
    
    /// Adds a new portfolio with default values.
    ///
    /// Creates a portfolio named "Portfolio N" with $50,000 value
    /// and default holdings of 50% AAPL and 50% MSFT.
    public func addPortfolio() {
        let newPortfolio = Portfolio(
            name: "Portfolio \(portfolios.count + 1)",
            totalValue: 50000.0,
            holdings: [
                Holding(ticker: "AAPL", allocation: 50.0),
                Holding(ticker: "MSFT", allocation: 50.0)
            ]
        )
        portfolios.append(newPortfolio)
        logger.info("Added new portfolio: \(newPortfolio.name)")
    }
    
    /// Deletes the specified portfolio from the store.
    ///
    /// - Parameter portfolio: The portfolio to delete.
    public func deletePortfolio(_ portfolio: Portfolio) {
        let name = portfolio.name
        portfolios.removeAll { $0.id == portfolio.id }
        logger.info("Deleted portfolio: \(name)")
    }
    
    /// Updates an existing portfolio with new values.
    ///
    /// - Parameter portfolio: The portfolio with updated values.
    public func updatePortfolio(_ portfolio: Portfolio) {
        if let index = portfolios.firstIndex(where: { $0.id == portfolio.id }) {
            portfolios[index] = portfolio
            logger.debug("Updated portfolio: \(portfolio.name)")
        }
    }
    
    // MARK: - Analytics
    
    /// Calculates the combined allocation across all portfolios.
    ///
    /// Computes value-weighted allocation for each unique ticker symbol
    /// across all portfolios.
    ///
    /// - Returns: Array of `CombinedHolding` sorted by allocation in descending order.
    public func calculateCombinedPortfolio() -> [CombinedHolding] {
        let totalValue = totalPortfolioValue
        guard totalValue > 0 else { return [] }
        
        var combinedHoldings: [String: Double] = [:]
        
        for portfolio in portfolios {
            let portfolioWeight = portfolio.totalValue / totalValue
            for holding in portfolio.holdings where !holding.ticker.isEmpty {
                let weightedAllocation = (holding.allocation / 100.0) * portfolioWeight
                combinedHoldings[holding.ticker, default: 0] += weightedAllocation
            }
        }
        
        return combinedHoldings.map { ticker, allocation in
            CombinedHolding(
                ticker: ticker,
                allocation: allocation * 100,
                dollarAmount: allocation * totalValue
            )
        }.sorted { $0.allocation > $1.allocation }
    }
    
    /// The total value across all portfolios.
    public var totalPortfolioValue: Double {
        portfolios.reduce(0) { $0 + $1.totalValue }
    }
    
    // MARK: - Persistence
    
    /// Loads portfolios from the repository.
    ///
    /// If no data exists or loading fails, loads sample data for first-time users.
    private func loadPortfolios() {
        do {
            let loaded = try repository.load()
            if loaded.isEmpty && !repository.hasPersistedData {
                logger.info("No existing data found, loading sample portfolios")
                portfolios = PortfolioData.sampleData.portfolios
            } else {
                portfolios = loaded
                logger.info("Loaded \(self.portfolios.count) portfolios from storage")
            }
            lastError = nil
        } catch let error as PortfolioError {
            logger.error("Failed to load portfolios: \(error.localizedDescription)")
            lastError = error
            portfolios = PortfolioData.sampleData.portfolios
        } catch {
            logger.error("Unexpected load error: \(error.localizedDescription)")
            lastError = .loadFailed(underlying: error)
            portfolios = PortfolioData.sampleData.portfolios
        }
    }
    
    /// Saves portfolios to the repository.
    private func savePortfolios() {
        do {
            try repository.save(portfolios)
            logger.debug("Saved \(self.portfolios.count) portfolios to storage")
            lastError = nil
        } catch let error as PortfolioError {
            logger.error("Failed to save portfolios: \(error.localizedDescription)")
            lastError = error
        } catch {
            logger.error("Unexpected save error: \(error.localizedDescription)")
            lastError = .saveFailed(underlying: error)
        }
    }
    
    /// Clears the last error state.
    public func clearError() {
        lastError = nil
    }
}
