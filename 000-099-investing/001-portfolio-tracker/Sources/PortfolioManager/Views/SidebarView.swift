import SwiftUI

// MARK: - Sidebar View

/// Navigation sidebar displaying portfolio list and analytics options.
///
/// Provides:
/// - List of all portfolios with context menu for deletion
/// - Analytics section with combined portfolio view access
/// - Toolbar button to add new portfolios
public struct SidebarView: View {
    
    // MARK: - Environment
    
    @EnvironmentObject var store: PortfolioStore
    
    // MARK: - Bindings
    
    @Binding var selectedPortfolio: Portfolio?
    @Binding var showingCombinedView: Bool
    
    // MARK: - Body
    
    public var body: some View {
        List(selection: portfolioSelection) {
            portfoliosSection
            analyticsSection
        }
        .listStyle(SidebarListStyle())
        .frame(minWidth: 250)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                addButton
            }
        }
    }
    
    // MARK: - Portfolio Selection Binding
    
    /// Binding for managing portfolio selection state.
    private var portfolioSelection: Binding<Portfolio?> {
        Binding(
            get: { showingCombinedView ? nil : selectedPortfolio },
            set: { newValue in
                if newValue != nil {
                    showingCombinedView = false
                    selectedPortfolio = newValue
                }
            }
        )
    }
    
    // MARK: - Sections
    
    /// Section displaying the list of portfolios.
    private var portfoliosSection: some View {
        Section("Portfolios") {
            ForEach(store.portfolios) { portfolio in
                PortfolioRow(portfolio: portfolio)
                    .tag(portfolio as Portfolio?)
                    .contextMenu {
                        deleteButton(for: portfolio)
                    }
            }
        }
    }
    
    /// Section displaying analytics options.
    private var analyticsSection: some View {
        Section("Analytics") {
            Button(action: showCombinedView) {
                Label("Combined Portfolio", systemImage: "chart.pie.fill")
                    .foregroundColor(showingCombinedView ? .white : .primary)
            }
            .buttonStyle(PlainButtonStyle())
            .padding(.vertical, 4)
            .padding(.horizontal, 8)
            .background(showingCombinedView ? Color.accentColor : Color.clear)
            .cornerRadius(6)
        }
    }
    
    // MARK: - Buttons
    
    /// Button to add a new portfolio.
    private var addButton: some View {
        Button(action: addNewPortfolio) {
            Label("Add Portfolio", systemImage: "plus")
        }
    }
    
    /// Creates a delete button for a specific portfolio.
    private func deleteButton(for portfolio: Portfolio) -> some View {
        Button("Delete") {
            deletePortfolio(portfolio)
        }
    }
    
    // MARK: - Actions
    
    /// Adds a new portfolio and selects it.
    private func addNewPortfolio() {
        withAnimation {
            store.addPortfolio()
            selectedPortfolio = store.portfolios.last
            showingCombinedView = false
        }
    }
    
    /// Deletes the specified portfolio.
    private func deletePortfolio(_ portfolio: Portfolio) {
        withAnimation {
            if selectedPortfolio?.id == portfolio.id {
                selectedPortfolio = nil
            }
            store.deletePortfolio(portfolio)
        }
    }
    
    /// Shows the combined portfolio analytics view.
    private func showCombinedView() {
        showingCombinedView = true
        selectedPortfolio = nil
    }
}

