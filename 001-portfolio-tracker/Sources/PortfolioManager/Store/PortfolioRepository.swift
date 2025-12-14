import Foundation
import os.log

// MARK: - Portfolio Repository Protocol

/// Protocol defining the interface for portfolio persistence.
///
/// Implementations provide storage and retrieval of portfolio data,
/// enabling dependency injection for testing and flexibility in
/// storage backends.
public protocol PortfolioRepository: Sendable {
    
    /// Loads portfolios from storage.
    ///
    /// - Returns: Array of persisted portfolios, or empty array if none exist.
    /// - Throws: `PortfolioError` if loading fails.
    func load() throws -> [Portfolio]
    
    /// Saves portfolios to storage.
    ///
    /// - Parameter portfolios: The portfolios to persist.
    /// - Throws: `PortfolioError` if saving fails.
    func save(_ portfolios: [Portfolio]) throws
    
    /// Indicates whether persisted data exists.
    var hasPersistedData: Bool { get }
}

// MARK: - File Portfolio Repository

/// File-based implementation of `PortfolioRepository`.
///
/// Persists portfolio data as JSON in the Application Support directory.
/// Thread-safe and designed for use with Swift concurrency.
public final class FilePortfolioRepository: PortfolioRepository, @unchecked Sendable {
    
    // MARK: - Properties
    
    /// Logger for diagnostics and error reporting.
    private let logger = Logger(subsystem: "com.portfolio.manager", category: "Repository")
    
    /// URL for the JSON persistence file.
    private let saveURL: URL
    
    /// File manager for file operations.
    private let fileManager: FileManager
    
    // MARK: - Initialization
    
    /// Creates a new file repository with default storage location.
    ///
    /// - Throws: `PortfolioError.storageUnavailable` if Application Support cannot be located.
    public init() throws {
        self.fileManager = FileManager.default
        
        guard let appSupport = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask).first else {
            throw PortfolioError.storageUnavailable
        }
        
        let appFolder = appSupport.appendingPathComponent("PortfolioManager")
        
        do {
            try fileManager.createDirectory(at: appFolder, withIntermediateDirectories: true)
        } catch {
            throw PortfolioError.directoryCreationFailed(underlying: error)
        }
        
        self.saveURL = appFolder.appendingPathComponent("portfolios.json")
        logger.debug("Repository initialized at: \(self.saveURL.path)")
    }
    
    /// Creates a repository with a custom storage URL.
    ///
    /// Primarily used for testing.
    ///
    /// - Parameter url: The file URL to use for storage.
    internal init(url: URL) {
        self.fileManager = FileManager.default
        self.saveURL = url
    }
    
    // MARK: - PortfolioRepository
    
    public var hasPersistedData: Bool {
        fileManager.fileExists(atPath: saveURL.path)
    }
    
    public func load() throws -> [Portfolio] {
        guard hasPersistedData else {
            logger.info("No persisted data found")
            return []
        }
        
        do {
            let data = try Data(contentsOf: saveURL)
            let decoded = try JSONDecoder().decode(PortfolioData.self, from: data)
            logger.info("Loaded \(decoded.portfolios.count) portfolios")
            return decoded.portfolios
        } catch {
            logger.error("Load failed: \(error.localizedDescription)")
            throw PortfolioError.loadFailed(underlying: error)
        }
    }
    
    public func save(_ portfolios: [Portfolio]) throws {
        do {
            let data = PortfolioData(portfolios: portfolios)
            let encoded = try JSONEncoder().encode(data)
            try encoded.write(to: saveURL, options: .atomic)
            logger.debug("Saved \(portfolios.count) portfolios")
        } catch {
            logger.error("Save failed: \(error.localizedDescription)")
            throw PortfolioError.saveFailed(underlying: error)
        }
    }
}

// MARK: - In-Memory Repository

/// In-memory implementation of `PortfolioRepository` for testing.
///
/// Does not persist data between sessions. Thread-safe using actor isolation.
public final class InMemoryPortfolioRepository: PortfolioRepository, @unchecked Sendable {
    
    // MARK: - Properties
    
    /// In-memory storage for portfolios.
    private var portfolios: [Portfolio] = []
    
    /// Lock for thread safety.
    private let lock = NSLock()
    
    /// Whether data has been saved at least once.
    private var _hasPersistedData = false
    
    // MARK: - Initialization
    
    /// Creates a new in-memory repository.
    ///
    /// - Parameter initialData: Optional initial portfolios.
    public init(initialData: [Portfolio] = []) {
        self.portfolios = initialData
        self._hasPersistedData = !initialData.isEmpty
    }
    
    // MARK: - PortfolioRepository
    
    public var hasPersistedData: Bool {
        lock.lock()
        defer { lock.unlock() }
        return _hasPersistedData
    }
    
    public func load() throws -> [Portfolio] {
        lock.lock()
        defer { lock.unlock() }
        return portfolios
    }
    
    public func save(_ portfolios: [Portfolio]) throws {
        lock.lock()
        defer { lock.unlock() }
        self.portfolios = portfolios
        self._hasPersistedData = true
    }
}

