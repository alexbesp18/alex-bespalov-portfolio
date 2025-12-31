import Foundation

// MARK: - Currency Formatter

/// Utility for formatting monetary values as currency strings.
///
/// Provides consistent USD currency formatting throughout the application.
/// Uses a shared singleton instance for efficiency with cached formatters.
///
/// Example:
/// ```swift
/// let formatted = CurrencyFormatter.shared.format(50000.0)
/// // Returns "$50,000.00"
/// ```
public final class CurrencyFormatter: @unchecked Sendable {
    
    // MARK: - Shared Instance
    
    /// Shared singleton instance for currency formatting.
    public static let shared = CurrencyFormatter()
    
    // MARK: - Properties
    
    /// The underlying NumberFormatter configured for USD currency.
    private let formatter: NumberFormatter
    
    /// Cached compact formatter for whole number display.
    private let compactFormatter: NumberFormatter
    
    /// Cached formatter for decimal display.
    private let decimalFormatter: NumberFormatter
    
    // MARK: - Initialization
    
    /// Creates a new currency formatter configured for US dollars.
    private init() {
        // Standard formatter with 2 decimal places
        formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.locale = Locale(identifier: "en_US")
        formatter.maximumFractionDigits = 2
        formatter.minimumFractionDigits = 2
        
        // Compact formatter without decimals
        compactFormatter = NumberFormatter()
        compactFormatter.numberStyle = .currency
        compactFormatter.locale = Locale(identifier: "en_US")
        compactFormatter.maximumFractionDigits = 0
        compactFormatter.minimumFractionDigits = 0
        
        // Decimal formatter for fractional amounts
        decimalFormatter = NumberFormatter()
        decimalFormatter.numberStyle = .currency
        decimalFormatter.locale = Locale(identifier: "en_US")
        decimalFormatter.maximumFractionDigits = 2
        decimalFormatter.minimumFractionDigits = 2
    }
    
    // MARK: - Formatting
    
    /// Formats a numeric value as a USD currency string.
    ///
    /// - Parameter value: The monetary value to format.
    /// - Returns: A formatted currency string (e.g., "$50,000.00").
    public func format(_ value: Double) -> String {
        formatter.string(from: NSNumber(value: value)) ?? "$0.00"
    }
    
    /// Formats a numeric value as a compact currency string.
    ///
    /// Uses no decimal places for whole numbers, and 2 decimal places
    /// for fractional amounts. Efficiently reuses cached formatters.
    ///
    /// - Parameter value: The monetary value to format.
    /// - Returns: A formatted string (e.g., "$50,000" or "$1,234.56").
    public func formatCompact(_ value: Double) -> String {
        let isWholeNumber = value.truncatingRemainder(dividingBy: 1) == 0
        let selectedFormatter = isWholeNumber ? compactFormatter : decimalFormatter
        return selectedFormatter.string(from: NSNumber(value: value)) ?? "$0"
    }
}

// MARK: - Convenience Extensions

extension Double {
    
    /// Formats the value as a USD currency string.
    ///
    /// - Returns: A formatted currency string.
    public var asCurrency: String {
        CurrencyFormatter.shared.format(self)
    }
    
    /// Formats the value as a compact USD currency string.
    ///
    /// - Returns: A formatted currency string without trailing zeros.
    public var asCurrencyCompact: String {
        CurrencyFormatter.shared.formatCompact(self)
    }
}
