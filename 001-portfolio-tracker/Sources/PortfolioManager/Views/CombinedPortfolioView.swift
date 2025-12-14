import SwiftUI

// MARK: - Combined Portfolio View

/// Analytics view showing weighted allocation across all portfolios.
///
/// Displays:
/// - Total portfolio value across all portfolios
/// - Number of portfolios and unique tickers
/// - Weighted allocation breakdown by ticker
/// - Dollar amounts for each holding
public struct CombinedPortfolioView: View {
    
    // MARK: - Environment
    
    @EnvironmentObject var store: PortfolioStore
    
    // MARK: - Computed Properties
    
    /// Combined holdings with weighted allocations.
    var combinedHoldings: [CombinedHolding] {
        store.calculateCombinedPortfolio()
    }
    
    // MARK: - Body
    
    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                headerSection
                contentSection
            }
            .padding(24)
        }
        .background(Color(NSColor.textBackgroundColor))
    }
    
    // MARK: - Content Section
    
    /// Main content based on portfolio state.
    @ViewBuilder
    private var contentSection: some View {
        if store.portfolios.isEmpty {
            noPortfoliosView
        } else if combinedHoldings.isEmpty {
            emptyStateView
        } else {
            holdingsListSection
        }
    }
    
    // MARK: - Header Section
    
    /// Summary statistics header.
    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Combined Portfolio Analysis")
                .font(.largeTitle)
                .bold()
            
            HStack(spacing: 40) {
                statCard(title: "Total Portfolio Value", value: store.totalPortfolioValue.asCurrency)
                statCard(title: "Number of Portfolios", value: "\(store.portfolios.count)")
                statCard(title: "Unique Tickers", value: "\(combinedHoldings.count)")
            }
        }
    }
    
    /// Creates a statistics card with title and value.
    private func statCard(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
            
            Text(value)
                .font(.title2)
                .bold()
        }
    }
    
    // MARK: - Holdings List Section
    
    /// Table showing weighted holdings breakdown.
    private var holdingsListSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Weighted Holdings")
                .font(.title2)
                .bold()
            
            VStack(spacing: 0) {
                holdingsTableHeader
                Divider()
                holdingsTableRows
            }
            .background(Color(NSColor.textBackgroundColor))
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color(NSColor.separatorColor), lineWidth: 1)
            )
        }
    }
    
    /// Table header row.
    private var holdingsTableHeader: some View {
        HStack {
            Text("Ticker")
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(width: 100, alignment: .leading)
            
            Text("Allocation")
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(width: 120, alignment: .trailing)
            
            Text("Dollar Amount")
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(width: 150, alignment: .trailing)
            
            Spacer()
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(Color(NSColor.controlBackgroundColor))
    }
    
    /// Table rows for each holding.
    private var holdingsTableRows: some View {
        ForEach(combinedHoldings) { holding in
            VStack(spacing: 0) {
                HStack {
                    Text(holding.ticker)
                        .font(.system(.body, design: .monospaced))
                        .bold()
                        .frame(width: 100, alignment: .leading)
                        .accessibilityLabel("Ticker: \(holding.ticker)")
                    
                    Text(holding.formattedAllocation)
                        .frame(width: 120, alignment: .trailing)
                        .accessibilityLabel("Allocation: \(holding.formattedAllocation)")
                    
                    Text(holding.formattedDollarAmount)
                        .frame(width: 150, alignment: .trailing)
                        .foregroundColor(.green)
                        .accessibilityLabel("Value: \(holding.formattedDollarAmount)")
                    
                    Spacer()
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 12)
                .accessibilityElement(children: .combine)
                
                Divider()
            }
        }
    }
    
    // MARK: - Empty States
    
    /// View shown when portfolios exist but have no valid holdings.
    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "chart.pie")
                .font(.system(size: 64))
                .foregroundColor(.secondary)
                .accessibilityHidden(true)
            
            Text("No holdings found")
                .font(.title2)
            
            Text("Add tickers to your portfolios to see the combined allocation")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(50)
        .accessibilityElement(children: .combine)
    }
    
    /// View shown when no portfolios exist.
    private var noPortfoliosView: some View {
        VStack(spacing: 16) {
            Image(systemName: "folder.badge.plus")
                .font(.system(size: 64))
                .foregroundColor(.secondary)
                .accessibilityHidden(true)
            
            Text("No portfolios yet")
                .font(.title2)
            
            Text("Create your first portfolio using the + button in the sidebar")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(50)
        .accessibilityElement(children: .combine)
    }
}
