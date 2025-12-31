import SwiftUI

// MARK: - Portfolio Detail View

/// Detailed editing view for a single portfolio.
///
/// Allows users to:
/// - Edit portfolio name and total value
/// - Add, edit, and delete holdings
/// - View real-time allocation validation
/// - Save or reset changes
public struct PortfolioDetailView: View {
    
    // MARK: - Field Enum
    
    /// Focus field identifiers for keyboard navigation.
    public enum Field: Hashable {
        case name
        case value
        case ticker(UUID)
        case allocation(UUID)
    }
    
    // MARK: - Environment
    
    @EnvironmentObject var store: PortfolioStore
    
    // MARK: - Properties
    
    /// The original portfolio (before edits).
    let portfolio: Portfolio
    
    // MARK: - State
    
    @State private var editedPortfolio: Portfolio
    @FocusState private var focusedField: Field?
    
    // MARK: - Initialization
    
    /// Creates a detail view for the specified portfolio.
    ///
    /// - Parameter portfolio: The portfolio to display and edit.
    public init(portfolio: Portfolio) {
        self.portfolio = portfolio
        self._editedPortfolio = State(initialValue: portfolio)
    }
    
    // MARK: - Body
    
    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                headerSection
                holdingsSection
                validationSection
                actionButtons
            }
            .padding(24)
        }
        .background(Color(NSColor.textBackgroundColor))
        .onChange(of: portfolio) { _, newValue in
            editedPortfolio = newValue
        }
    }
    
    // MARK: - Header Section
    
    /// Section displaying portfolio name and value fields.
    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Portfolio Details")
                .font(.largeTitle)
                .bold()
            
            HStack(spacing: 20) {
                nameField
                valueField
            }
        }
    }
    
    /// Text field for editing portfolio name.
    private var nameField: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Portfolio Name")
                .font(.caption)
                .foregroundColor(.secondary)
            
            TextField("Portfolio Name", text: $editedPortfolio.name)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .focused($focusedField, equals: .name)
                .frame(width: 250)
        }
    }
    
    /// Text field for editing portfolio total value.
    private var valueField: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Total Value")
                .font(.caption)
                .foregroundColor(.secondary)
            
            HStack {
                Text("$")
                TextField("0", value: $editedPortfolio.totalValue, format: .number)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .focused($focusedField, equals: .value)
                    .frame(width: 150)
            }
        }
    }
    
    // MARK: - Holdings Section
    
    /// Section for managing portfolio holdings.
    private var holdingsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            holdingsSectionHeader
            holdingsTable
        }
    }
    
    /// Header with title and add button.
    private var holdingsSectionHeader: some View {
        HStack {
            Text("Holdings")
                .font(.title2)
                .bold()
            
            Spacer()
            
            Button(action: addHolding) {
                Label("Add Ticker", systemImage: "plus.circle.fill")
            }
            .buttonStyle(.plain)
            .foregroundColor(.accentColor)
        }
    }
    
    /// Table displaying holdings with column headers.
    private var holdingsTable: some View {
        VStack(spacing: 12) {
            // Column headers
            HStack {
                Text("Ticker Symbol")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .frame(width: 150, alignment: .leading)
                
                Text("Allocation (%)")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .frame(width: 120, alignment: .leading)
                
                Text("")
                    .frame(width: 30)
            }
            .padding(.horizontal, 12)
            
            // Holding rows
            ForEach(editedPortfolio.holdings.indices, id: \.self) { index in
                HoldingRow(
                    holding: $editedPortfolio.holdings[index],
                    focusedField: $focusedField,
                    onDelete: { deleteHolding(at: index) }
                )
            }
        }
        .padding(12)
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
    }
    
    // MARK: - Validation Section
    
    /// Section displaying allocation validation status.
    private var validationSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Total Allocation:")
                    .font(.headline)
                
                Text("\(editedPortfolio.totalAllocation, specifier: "%.1f")%")
                    .font(.headline)
                    .foregroundColor(editedPortfolio.isValid ? .green : .red)
                
                validationIcon
            }
            
            if !editedPortfolio.isValid {
                Text("Allocations must sum to exactly 100%")
                    .font(.caption)
                    .foregroundColor(.red)
            }
        }
        .padding()
        .background(editedPortfolio.isValid ? Color.green.opacity(0.1) : Color.red.opacity(0.1))
        .cornerRadius(8)
    }
    
    /// Icon indicating validation status.
    private var validationIcon: some View {
        Group {
            if editedPortfolio.isValid {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.green)
            } else {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(.red)
            }
        }
    }
    
    // MARK: - Action Buttons
    
    /// Reset and save action buttons.
    private var actionButtons: some View {
        HStack(spacing: 12) {
            Button("Reset") {
                editedPortfolio = portfolio
            }
            .buttonStyle(.bordered)
            
            Spacer()
            
            Button("Save Changes") {
                saveChanges()
            }
            .buttonStyle(.borderedProminent)
            .disabled(!editedPortfolio.isValid || !hasChanges)
        }
    }
    
    // MARK: - Computed Properties
    
    /// Indicates whether the edited portfolio differs from the original.
    private var hasChanges: Bool {
        editedPortfolio != portfolio
    }
    
    // MARK: - Actions
    
    /// Adds a new empty holding to the portfolio.
    private func addHolding() {
        withAnimation {
            editedPortfolio.holdings.append(Holding())
        }
    }
    
    /// Deletes the holding at the specified index.
    private func deleteHolding(at index: Int) {
        withAnimation {
            editedPortfolio.holdings.remove(at: index)
            if editedPortfolio.holdings.isEmpty {
                editedPortfolio.holdings.append(Holding())
            }
        }
    }
    
    /// Saves changes to the store if validation passes.
    private func saveChanges() {
        if editedPortfolio.isValid {
            store.updatePortfolio(editedPortfolio)
        }
    }
}

