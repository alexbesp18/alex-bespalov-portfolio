import SwiftUI

// MARK: - Holding Row

/// An editable row view for a single holding within a portfolio.
///
/// Provides text fields for ticker symbol and allocation percentage,
/// with automatic uppercase conversion for tickers and a delete button.
public struct HoldingRow: View {
    
    // MARK: - Bindings
    
    /// Binding to the holding being edited.
    @Binding var holding: Holding
    
    /// Focus state binding for managing field focus.
    @FocusState.Binding var focusedField: PortfolioDetailView.Field?
    
    /// Closure called when the delete button is pressed.
    let onDelete: () -> Void
    
    // MARK: - Body
    
    public var body: some View {
        HStack(spacing: 16) {
            tickerField
            allocationField
            deleteButton
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 4)
    }
    
    // MARK: - Ticker Field
    
    /// Text field for entering the ticker symbol.
    private var tickerField: some View {
        TextField("TICKER", text: $holding.ticker)
            .textFieldStyle(RoundedBorderTextFieldStyle())
            .frame(width: 150)
            .focused($focusedField, equals: .ticker(holding.id))
            .onChange(of: holding.ticker) { _, newValue in
                holding.ticker = newValue.uppercased()
            }
    }
    
    // MARK: - Allocation Field
    
    /// Text field for entering the allocation percentage.
    private var allocationField: some View {
        HStack {
            TextField("0", value: $holding.allocation, format: .number)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .frame(width: 80)
                .focused($focusedField, equals: .allocation(holding.id))
                .multilineTextAlignment(.trailing)
            
            Text("%")
                .foregroundColor(.secondary)
        }
    }
    
    // MARK: - Delete Button
    
    /// Button to delete this holding.
    private var deleteButton: some View {
        Button(action: onDelete) {
            Image(systemName: "trash")
                .foregroundColor(.red)
        }
        .buttonStyle(.plain)
    }
}

