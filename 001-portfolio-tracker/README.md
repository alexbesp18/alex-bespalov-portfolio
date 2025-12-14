# Portfolio Tracker

A native macOS/iOS application for managing multiple investment portfolios with real-time allocation tracking, validation, and combined portfolio analytics.

## Key Features

- **Multi-Portfolio Management** - Create and manage unlimited portfolios with custom names and values
- **Allocation Validation** - Real-time validation ensuring holdings sum to exactly 100%
- **Combined Analytics** - View weighted allocation across all portfolios
- **Persistent Storage** - Automatic JSON-based data persistence
- **Native SwiftUI Interface** - Modern, responsive macOS/iOS design with sidebar navigation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PortfolioManagerApp                       │
│                         (@main)                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      ContentView                             │
│              (NavigationSplitView Layout)                    │
├────────────────────────┬────────────────────────────────────┤
│     SidebarView        │         Detail Views               │
│  - Portfolio List      │  - PortfolioDetailView             │
│  - Analytics Section   │  - CombinedPortfolioView           │
└────────────────────────┴────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    PortfolioStore                            │
│           (ObservableObject + Combine)                       │
│  - CRUD Operations                                           │
│  - Auto-save with debounce                                   │
│  - Combined portfolio calculation                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Models                             │
│  Portfolio ──────▶ [Holding]                                │
│  - name: String      - ticker: String                       │
│  - totalValue        - allocation: Double                   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- macOS 13.0+ / iOS 16.0+
- Xcode 15.0+
- Swift 5.9+

### Installation

```bash
# Clone the repository
git clone https://github.com/alexbesp18/portfolio-tracker
cd portfolio-tracker

# Build with Swift Package Manager
swift build

# Run the application
swift run PortfolioManager
```

### Opening in Xcode

```bash
# Generate Xcode project (optional)
open Package.swift
```

## Usage

### Creating a Portfolio

1. Click the **+** button in the sidebar toolbar
2. Enter portfolio name and total value
3. Add ticker symbols with allocation percentages
4. Ensure allocations sum to 100% (validation indicator will turn green)
5. Click **Save Changes**

### Viewing Combined Analytics

1. Click **Combined Portfolio** in the Analytics section
2. View weighted allocation across all portfolios
3. See dollar amounts calculated from total portfolio values

### Example Portfolio Configuration

```
Tech Growth Portfolio ($60,000)
├── AAPL: 60%  →  $36,000
└── MSFT: 40%  →  $24,000

Balanced Portfolio ($40,000)
├── AAPL: 50%  →  $20,000
├── GOOGL: 30% →  $12,000
└── MSFT: 20%  →  $8,000

Combined ($100,000)
├── AAPL: 56%  →  $56,000
├── MSFT: 32%  →  $32,000
└── GOOGL: 12% →  $12,000
```

## Project Structure

```
portfolio-tracker/
├── Package.swift              # Swift Package Manager manifest
├── README.md                  # This file
├── AUDIT_REPORT.md           # Code quality audit
├── CHANGES.md                # Changelog
│
├── Sources/
│   └── PortfolioManager/
│       ├── PortfolioManagerApp.swift   # App entry point
│       │
│       ├── Models/
│       │   ├── Holding.swift           # Ticker + allocation
│       │   ├── Portfolio.swift         # Portfolio with holdings
│       │   └── PortfolioData.swift     # Persistence wrapper
│       │
│       ├── Store/
│       │   └── PortfolioStore.swift    # State management
│       │
│       ├── Views/
│       │   ├── ContentView.swift       # Main layout
│       │   ├── SidebarView.swift       # Navigation sidebar
│       │   ├── PortfolioDetailView.swift
│       │   ├── PortfolioRow.swift
│       │   ├── HoldingRow.swift
│       │   └── CombinedPortfolioView.swift
│       │
│       └── Utilities/
│           └── CurrencyFormatter.swift # Currency formatting
│
└── Tests/
    └── PortfolioManagerTests/
        ├── PortfolioModelTests.swift
        ├── PortfolioStoreTests.swift
        └── CurrencyFormatterTests.swift
```

## Configuration

### Data Storage Location

Portfolio data is automatically saved to:
- **macOS:** `~/Library/Application Support/PortfolioManager/portfolios.json`
- **iOS:** App's Documents directory

### Default Values

New portfolios are created with:
- Default value: $50,000
- Default holdings: AAPL (50%), MSFT (50%)

## Technical Notes

### State Management

The app uses SwiftUI's `@Published` properties with Combine for reactive updates. The `PortfolioStore` automatically debounces saves (0.5s) to prevent excessive disk writes during rapid editing.

### Allocation Calculation

Combined portfolio allocation uses value-weighted averaging:

```swift
weightedAllocation = (holding.allocation / 100) × (portfolio.value / totalValue)
```

### Validation

Portfolio allocations must sum to exactly 100% (±0.01% tolerance) before saving is enabled.

## Testing

```bash
# Run all tests
swift test

# Run with verbose output
swift test --verbose
```

## Development

### Code Style

- Swift API Design Guidelines
- MARK comments for code organization
- Swift doc comments for public APIs
- `os.log` Logger for diagnostics

### Building for Release

```bash
swift build -c release
```

## License

MIT License - See LICENSE file for details.

## Author

Alex Bespalov - [GitHub](https://github.com/alexbesp18)
