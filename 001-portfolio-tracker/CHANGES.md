# Changelog

All notable changes to the Portfolio Tracker project.

## [2.1.0] - 2025-12-12 (QA Optimization Pass)

### Type Safety & API Design
- **CombinedHolding Struct**: Replaced tuple return type with proper `CombinedHolding` struct
- **Sendable Conformance**: Added `Sendable` to all models for Swift 6 concurrency safety
- **Input Validation**: Added validation for negative `totalValue` and `allocation` values

### Architecture Improvements
- **PortfolioRepository Protocol**: Created protocol for dependency injection
- **FilePortfolioRepository**: Production implementation with safe error handling
- **InMemoryPortfolioRepository**: In-memory implementation for testing
- **Dependency Injection**: PortfolioStore now accepts repository via initializer

### Error Handling
- **PortfolioError Enum**: Custom error type with `LocalizedError` conformance
- **Safe Fallbacks**: Removed all force unwraps with proper error handling
- **Error State**: Added `lastError` property to PortfolioStore

### Performance
- **Cached Formatters**: CurrencyFormatter now caches all NumberFormatter instances
- **Thread Safety**: All formatters and repositories are thread-safe

### Testing
- **Isolated Tests**: Updated all tests to use `InMemoryPortfolioRepository`
- **New Test Files**: Added `PortfolioRepositoryTests.swift`
- **Sendable Tests**: Added tests verifying Swift concurrency conformance
- **Test Count**: 50+ test cases across 4 test files

### Accessibility
- **VoiceOver Labels**: Added accessibility labels to combined portfolio view

---

## [2.0.0] - 2025-12-12

### Restructured
- **Modular Architecture**: Split monolithic 673-line `PortfolioManager.swift` into organized modules:
  - `Models/` - Holding, Portfolio, PortfolioData, CombinedHolding
  - `Store/` - PortfolioStore, PortfolioRepository, PortfolioError
  - `Views/` - Individual view files for better maintainability
  - `Utilities/` - Reusable currency formatting

### Added
- **Comprehensive .gitignore** for Swift/Xcode/macOS projects
- **AUDIT_REPORT.md** documenting code quality assessment
- **Test Suite** with XCTest coverage for models, store, and utilities
- **Swift Documentation** (///) for all public APIs
- **Professional README** with architecture, installation, and usage

### Changed
- **Logging**: Replaced `print()` statements with Swift `Logger` (os.log)
- **Error Handling**: Custom PortfolioError type with LocalizedError
- **Package.swift**: Updated to support test target

### Fixed
- Removed .DS_Store from version control
- Ensured no hardcoded paths or secrets in codebase

### Technical Details

#### Before
```
Sources/
└── PortfolioManager.swift (673 lines)
```

#### After
```
Sources/
└── PortfolioManager/
    ├── PortfolioManagerApp.swift
    ├── Models/
    │   ├── Holding.swift
    │   ├── Portfolio.swift
    │   └── PortfolioData.swift
    ├── Store/
    │   └── PortfolioStore.swift
    ├── Views/
    │   ├── ContentView.swift
    │   ├── SidebarView.swift
    │   ├── PortfolioDetailView.swift
    │   ├── PortfolioRow.swift
    │   ├── HoldingRow.swift
    │   └── CombinedPortfolioView.swift
    └── Utilities/
        └── CurrencyFormatter.swift
```

---

## [1.0.0] - Initial Release

### Features
- Multiple portfolio management
- Ticker and allocation tracking
- Automatic allocation validation (must sum to 100%)
- Currency formatting
- Persistent JSON data storage
- Native macOS/iOS SwiftUI interface
- Combined portfolio analytics view

