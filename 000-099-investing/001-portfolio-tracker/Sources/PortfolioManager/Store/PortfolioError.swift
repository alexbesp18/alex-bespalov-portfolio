import Foundation

// MARK: - Portfolio Error

/// Errors that can occur during portfolio operations.
///
/// Provides detailed error information for persistence, validation,
/// and data operations with localized descriptions.
public enum PortfolioError: LocalizedError, Sendable {
    
    /// Failed to create the application support directory.
    case directoryCreationFailed(underlying: Error)
    
    /// Failed to read portfolio data from storage.
    case loadFailed(underlying: Error)
    
    /// Failed to write portfolio data to storage.
    case saveFailed(underlying: Error)
    
    /// Portfolio data is invalid or corrupted.
    case invalidData(reason: String)
    
    /// The storage location could not be determined.
    case storageUnavailable
    
    // MARK: - LocalizedError
    
    public var errorDescription: String? {
        switch self {
        case .directoryCreationFailed(let error):
            return "Failed to create storage directory: \(error.localizedDescription)"
        case .loadFailed(let error):
            return "Failed to load portfolios: \(error.localizedDescription)"
        case .saveFailed(let error):
            return "Failed to save portfolios: \(error.localizedDescription)"
        case .invalidData(let reason):
            return "Invalid portfolio data: \(reason)"
        case .storageUnavailable:
            return "Portfolio storage location is unavailable"
        }
    }
    
    public var failureReason: String? {
        switch self {
        case .directoryCreationFailed:
            return "The application support directory could not be created."
        case .loadFailed:
            return "The portfolio data file could not be read."
        case .saveFailed:
            return "The portfolio data could not be written to disk."
        case .invalidData:
            return "The stored data does not match the expected format."
        case .storageUnavailable:
            return "The system could not locate the Application Support directory."
        }
    }
    
    public var recoverySuggestion: String? {
        switch self {
        case .directoryCreationFailed, .storageUnavailable:
            return "Check disk permissions and available storage space."
        case .loadFailed, .invalidData:
            return "The application will use default sample data."
        case .saveFailed:
            return "Try again or restart the application."
        }
    }
}

