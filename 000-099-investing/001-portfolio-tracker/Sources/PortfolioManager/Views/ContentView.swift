import SwiftUI

// MARK: - Content View

/// The main content view providing navigation split layout.
///
/// Displays a sidebar with portfolio list and analytics options,
/// alongside a detail view showing either portfolio details or
/// combined portfolio analysis.
public struct ContentView: View {
    
    // MARK: - Environment
    
    @EnvironmentObject var store: PortfolioStore
    
    // MARK: - State
    
    @State private var selectedPortfolio: Portfolio?
    @State private var showingCombinedView = false
    
    // MARK: - Body
    
    public var body: some View {
        NavigationSplitView {
            SidebarView(
                selectedPortfolio: $selectedPortfolio,
                showingCombinedView: $showingCombinedView
            )
        } detail: {
            detailContent
        }
        .frame(minWidth: 900, minHeight: 600)
    }
    
    // MARK: - Detail Content
    
    /// The detail view content based on current selection.
    @ViewBuilder
    private var detailContent: some View {
        if showingCombinedView {
            CombinedPortfolioView()
        } else if let portfolio = selectedPortfolio {
            PortfolioDetailView(portfolio: portfolio)
        } else {
            emptyStateView
        }
    }
    
    /// Placeholder view when no portfolio is selected.
    private var emptyStateView: some View {
        Text("Select a portfolio from the sidebar")
            .font(.title2)
            .foregroundColor(.secondary)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color(NSColor.textBackgroundColor))
    }
}

// MARK: - Preview

#if DEBUG
struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
            .environmentObject(PortfolioStore())
    }
}
#endif

