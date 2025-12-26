# Portfolio Analyzer & Withdrawal Optimizer

A comprehensive React-based portfolio analysis tool that helps investors track, analyze, and optimize their investment portfolio including Bitcoin, stocks, options, mining operations, and debt management.

## Key Features

- **Multi-Asset Portfolio Tracking**: Monitor BTC cold storage, growth stocks, MSTR stock, and BTC mining operations in one unified dashboard
- **Advanced Options Analysis**: Track and value options positions (calls/puts) with Black-Scholes approximation and projection modeling
- **Mining Profitability Calculator**: Calculate mining revenue, profit margins, and breakeven prices with network difficulty growth modeling
- **Risk Analysis**: Comprehensive risk metrics including concentration risk, options exposure, and crypto exposure analysis
- **Withdrawal Strategy Optimization**: Smart recommendations for sustainable monthly withdrawals while preserving core assets
- **Debt Management**: Track credit card debt, calculate payoff strategies (avalanche vs snowball), and compare debt payoff vs investment returns
- **Interactive Visualizations**: Real-time charts showing portfolio allocation, risk metrics, and projection scenarios
- **Data Export/Import**: Save and load portfolio configurations as JSON files

## Architecture

The application is built as a single-page React application with the following structure:

```
portfolio-analyzer/
├── src/
│   ├── components/
│   │   ├── PortfolioAnalyzer.js    # Main component (1,724 lines)
│   │   └── ErrorBoundary.js         # Error handling component
│   ├── utils/
│   │   └── logger.js                # Environment-aware logging utility
│   ├── App.js                       # Root component
│   └── index.js                      # Application entry point
├── public/                          # Static assets
└── package.json                     # Dependencies and scripts
```

**Key Technologies:**
- **React 19**: Modern React with hooks for state management
- **TailwindCSS**: Utility-first CSS framework for styling
- **Recharts**: Charting library for data visualization
- **Lucide React**: Icon library

## Quick Start

### Prerequisites

- Node.js 16+ and npm (or yarn)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

```bash
# Clone the repository
git clone https://github.com/alexbesp18/portfolio-analyzer
cd portfolio-analyzer

# Install dependencies
npm install

# Copy environment template (optional)
cp .env.example .env

# Start development server
npm start
```

The application will open at `http://localhost:3000`

### Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Usage

### Overview Tab

The overview tab provides a high-level view of your portfolio:
- **Total Portfolio Value**: Sum of all asset values
- **Allocation Pie Chart**: Visual breakdown of asset allocation
- **Risk Metrics**: Options exposure, crypto exposure, and concentration risks

### Assets Tab

Manage your core assets:
- **BTC Cold Storage**: Track quantity and cost basis
- **Growth Stocks**: Monitor portfolio value and gains/losses
- **MSTR Stock**: Track shares, cost basis, and current value

### Options Tab

Track your options positions:
- Add/edit/delete options contracts
- View current value, intrinsic value, and profit/loss
- Filter by underlying asset (IBIT, MSTR, NVDA)
- See options categorized by expiry timeframe

### Mining Tab

Analyze mining operations:
- Configure multiple mining providers
- Set hashrate, power consumption, and electricity rates
- View projected BTC mined, revenue, and profitability
- Adjust network parameters (hashrate, difficulty growth)

### Projections Tab

Set price projections for different timeframes:
- **3 Months, 6 Months, 1 Year, 2 Years, 3 Years**
- View options value projections at each timeframe
- See how portfolio value changes with price movements

### Withdrawals Tab

Plan sustainable withdrawals:
- Set monthly withdrawal target
- Configure risk tolerance (conservative, moderate, aggressive)
- Get 12-month withdrawal plan recommendations
- See impact analysis on portfolio value

### Debt Tab

Manage and optimize debt payoff:
- Track multiple credit cards with balances and APRs
- Compare avalanche vs snowball payoff methods
- Calculate interest savings
- Compare debt payoff vs investment returns

## Example Output

### Portfolio Summary
```
Total Portfolio Value: $125,000
Options Value: $45,000
Total Debt: $17,500
Net Worth: $107,500
```

### Risk Analysis
```
Options Exposure: 36%
Crypto/Crypto-Adjacent Exposure: 68%
Top Concentration Risk: MSTR Stock (28%)
```

### Mining Metrics (12 months)
```
Total BTC Mined: 0.1250 BTC
Total Revenue: $12,500
Total Electricity: $3,200
Net Profit: $9,300
Profit Margin: 74.4%
Monthly Average Profit: $775
```

## Project Structure

```
portfolio-analyzer/
├── README.md
├── AUDIT_REPORT.md
├── CHANGES.md
├── package.json
├── .gitignore
├── .env.example
│
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── manifest.json
│
├── src/
│   ├── components/
│   │   ├── PortfolioAnalyzer.js    # Main portfolio analysis component
│   │   └── ErrorBoundary.js         # React error boundary
│   │
│   ├── utils/
│   │   └── logger.js                # Logging utility
│   │
│   ├── App.js                       # Root component
│   ├── App.css
│   ├── App.test.js                  # Component tests
│   ├── index.js                     # Entry point
│   └── index.css
│
└── build/                           # Production build (generated)
```

## Configuration

### Environment Variables

Create a `.env` file (see `.env.example` for template):

```bash
# Environment
REACT_APP_ENVIRONMENT=development

# Logging Level (debug, info, warn, error)
REACT_APP_LOG_LEVEL=info

# Optional: Feature Flags
REACT_APP_ENABLE_EXPORT=true
```

### Default Settings

The application comes with sensible defaults:
- **BTC Price**: $100,000
- **MSTR Price**: $400
- **NVDA Price**: $135
- **IBIT Price**: $48
- **Mining Network Hashrate**: 900 EH/s
- **Monthly Difficulty Growth**: 2.5%

All defaults can be customized in the UI.

## Technical Notes

### Mining Calculations

The mining profitability calculator uses the following model:

1. **Network Share Calculation**: `(provider_hashrate / network_hashrate) * uptime_percentage`
2. **BTC Per Day**: `network_share * blocks_per_day * block_reward`
3. **Difficulty Growth**: Models exponential growth: `network_hashrate * (1 + growth_rate)^month`
4. **Electricity Costs**: `power_kW * 24 * 30.42 * electricity_rate_per_kWh`
5. **Profit Margin**: `(revenue - electricity) / revenue * 100`

### Options Valuation

Options are valued using a simplified Black-Scholes approximation:

- **Intrinsic Value**: `max(0, current_price - strike)` for calls
- **Time Value**: `current_price * volatility * sqrt(time_to_expiry) * 0.2`
- **Total Value**: `max(intrinsic_value, intrinsic_value + time_value) * contracts * 100`

Note: This is a simplified model. For production use, consider integrating with a professional options pricing API.

### Portfolio Aggregation

Portfolio values are calculated in real-time:
- **Core Assets**: Direct multiplication (quantity × price)
- **Options**: Sum of all option positions by category and timeframe
- **Mining**: 2x multiple on annual profit (simplified valuation)
- **Total**: Sum of all asset categories

### Risk Metrics

- **Concentration Risk**: Assets >25% allocation flagged as "High", >15% as "Medium"
- **Options Exposure**: Percentage of portfolio in options positions
- **Crypto Exposure**: Percentage in BTC, miners, MSTR, and crypto-related options

### Withdrawal Strategy

The withdrawal optimizer prioritizes:
1. Short-term options near expiry (< 6 months)
2. Medium-term options (6-12 months)
3. Options with significant gains
4. MSTR stock (partial positions)
5. Growth stocks
6. Long-term options (if needed)
7. BTC/Miners (only if absolutely necessary)

Core assets (BTC cold storage and miners) are protected based on `minCoreRetention` setting.

## Development

### Running Tests

```bash
npm test
```

### Code Quality

The project uses:
- ESLint (via react-scripts)
- Prettier (recommended)
- JSDoc for documentation

### Logging

The application uses a custom logger (`src/utils/logger.js`) that:
- Suppresses debug logs in production
- Respects `REACT_APP_LOG_LEVEL` environment variable
- Provides structured logging with timestamps

### Error Handling

React Error Boundary catches component errors and displays user-friendly error messages. Errors are logged using the logger utility.

## Future Enhancements

Potential improvements:
- [ ] Backend API for data persistence
- [ ] Real-time price feeds integration
- [ ] More sophisticated options pricing (Greeks calculation)
- [ ] Historical performance tracking
- [ ] Tax optimization features
- [ ] Multi-user support
- [ ] Mobile app version
- [ ] Component refactoring (split monolithic component)

## License

MIT License - see LICENSE file for details

## Contributing

This is a portfolio project. For questions or suggestions, please open an issue on GitHub.

---

**Note**: This tool is for personal portfolio analysis and educational purposes. It is not financial advice. Always consult with a qualified financial advisor before making investment decisions.
