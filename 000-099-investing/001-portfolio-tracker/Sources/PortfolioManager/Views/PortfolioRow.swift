import SwiftUI

// MARK: - Portfolio Row

/// A row view displaying portfolio name and formatted value.
///
/// Used in the sidebar list to represent each portfolio.
public struct PortfolioRow: View {
    
    // MARK: - Properties
    
    /// The portfolio to display.
    let portfolio: Portfolio
    
    // MARK: - Body
    
    public var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(portfolio.name)
                .font(.headline)
            
            Text(portfolio.formattedValue)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Preview

#if DEBUG
struct PortfolioRow_Previews: PreviewProvider {
    static var previews: some View {
        PortfolioRow(portfolio: Portfolio(
            name: "Tech Growth",
            totalValue: 60000,
            holdings: [
                Holding(ticker: "AAPL", allocation: 60),
                Holding(ticker: "MSFT", allocation: 40)
            ]
        ))
        .padding()
    }
}
#endif

