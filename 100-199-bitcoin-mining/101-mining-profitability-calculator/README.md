# Bitcoin Mining Calculator

> **Note**: This is a quick matrix comparison tool. For detailed electricity/hosting analysis, see [102-bitcoin-mining-electricity-calculator](../102-bitcoin-mining-electricity-calculator).

Matrix comparison tool for quick Bitcoin mining profit analysis with tax-optimized calculations and 2-year projections.

## Features

- **Matrix Comparison**: Compare multiple miners across different electricity rates ($0.047-$0.10/kWh)
- **2-Year Projections**: See cumulative profitability over 2 years with annualized ROI
- **Tax Optimization**: Includes bonus depreciation (100% Year 1) and MACRS 5-year depreciation options
- **20+ Preset Miners**: Pre-loaded with popular Bitmain Antminer models (S21, S19 series)
- **Custom Miners**: Add and edit your own miner specifications
- **Scenario Management**: Save and load different market scenarios
- **Data Import/Export**: Export your configuration to JSON for backup/sharing
- **Monthly Breakdowns**: Click any cell to see detailed month-by-month calculations
- **Quick Insights**: Automatically identifies most profitable miner and efficiency metrics
- **LocalStorage Persistence**: All changes automatically saved to your browser

## Live Demo

https://bitcoin-mining-calculator.vercel.app

## Use Case

"Which miner should I buy if my electricity is $0.06/kWh?"

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MiningCalculator                          │
│                  (Main Container)                           │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Hooks      │    │  Components  │    │    Utils     │
│              │    │              │    │              │
│ useMinerData │    │ HashrateWidget│   │ calculations │
│ useScenarios │    │ WelcomeModal  │   │ formatters   │
│ useMiningCalc│    │ ErrorBoundary │   │ validators   │
│ useLocalStorage│  │ ProfitMatrix  │   │ constants    │
└──────────────┘    └──────────────┘    └──────────────┘
```

### Component Hierarchy

```
MiningCalculator (Main)
├── ErrorBoundary
├── WelcomeModal
├── HashrateWidget
├── ParametersPanel
├── ScenarioManager
├── DataManagement
├── ProfitMatrixTable
│   └── MinerRow (memoized)
└── DetailModal
```

## Tech Stack

- **React 19.1.0** - UI framework
- **Tailwind CSS 3.4** - Styling (via npm, not CDN)
- **Lucide React** - Icons
- **PropTypes** - Type checking
- **LocalStorage API** - Data persistence

## Project Structure

```
101-bitcoin-mining-calculator/
├── src/
│   ├── components/
│   │   ├── MiningCalculator.js      # Main container
│   │   ├── ErrorBoundary.js         # Error handling
│   │   ├── WelcomeModal.js          # First-time welcome
│   │   ├── HashrateWidget.js        # Network difficulty widget
│   │   └── ...                      # Other components
│   ├── hooks/
│   │   ├── useMinerData.js          # Miner CRUD operations
│   │   ├── useScenarios.js         # Scenario management
│   │   ├── useMiningCalculations.js # Calculation logic
│   │   ├── useLocalStorage.js      # LocalStorage persistence
│   │   └── useProfitMatrix.js      # Matrix calculations
│   ├── utils/
│   │   ├── calculations.js          # Pure calculation functions
│   │   ├── constants.js             # All constants
│   │   ├── formatters.js           # Number/currency formatting
│   │   └── validators.js           # Input validation
│   ├── types/
│   │   └── index.js                # PropTypes definitions
│   ├── App.js
│   └── index.js
├── tests/                          # Test suite (to be added)
├── public/
├── package.json
├── tailwind.config.js
├── postcss.config.js
├── README.md
├── AUDIT_REPORT.md
└── CHANGES.md
```

## Setup

### Prerequisites

- Node.js 16+ and npm

### Installation

```bash
npm install
```

### Development

```bash
npm start
```

Opens http://localhost:3000

### Build

```bash
npm run build
```

Creates optimized production build in `build/` directory.

### Test

```bash
npm test
```

## Usage Examples

### Comparing Miners

1. Open the calculator
2. View the matrix showing all miners across electricity rates
3. Click any cell to see detailed monthly breakdown
4. Adjust miner prices by editing the price field in the left column
5. Edit miner specs (hashrate, power) - efficiency auto-calculates

### Saving Scenarios

1. Adjust parameters (BTC price, network hashrate, tax rates)
2. Click "Save" button in Data Management section
3. Enter scenario name (e.g., "Bull Run 2025")
4. Load scenarios from the dropdown

### Exporting Data

1. Click "Export" in Data Management section
2. JSON file downloads with all miners, prices, and parameters
3. Share with others or use as backup

### Using Preset Scenarios

Click preset buttons:
- **Current Market**: $100k-$150k BTC, moderate difficulty growth
- **Conservative**: Lower BTC price growth, higher difficulty
- **Bullish 2025**: $100k-$200k BTC, aggressive growth

## Configuration Parameters

### Bitcoin Network
- **BTC Price Start/End**: Starting and ending BTC price for calculations
- **Network Hashrate Start/End**: Network difficulty in EH/s
- **Annual Increase Mode**: Use percentage increases instead of end values

### Mining Parameters
- **Pool Fee**: Mining pool fee percentage (typically 1-2%)
- **Electricity Rates**: Matrix columns ($0.047 to $0.10/kWh)

### Tax Settings
- **Federal Tax Rate**: Your federal income tax rate
- **State Tax Rate**: Your state income tax rate
- **Depreciation Method**:
  - **Bonus Depreciation**: 100% in Year 1 (recommended for tax optimization)
  - **MACRS 5-Year**: Spread over 6 years (20%, 32%, 19.2%, 11.52%, 11.52%, 5.76%)

## Calculation Details

### Monthly Calculations
- BTC mined per month based on miner hashrate vs network hashrate
- Revenue = BTC mined × BTC price
- Pool fees deducted from revenue
- Electricity costs = Power (kW) × 24 hours × 30.42 days × rate
- Operational profit = Revenue - Pool fees - Electricity

### Tax Calculations
- Depreciation reduces taxable income
- Taxable income = Operational profit - Depreciation
- Total tax = (Taxable income × Federal rate) + (Taxable income × State rate)
- After-tax profit = Operational profit - Total tax
- Net profit = After-tax profit - Miner purchase price

### 2-Year Analysis
- Year 2 continues growth trends from Year 1
- Depreciation: 100% in Year 1 (bonus) or 20% Year 1, 32% Year 2 (MACRS)
- ROI is annualized (total 2-year ROI ÷ 2)

## Technical Notes

### Performance Optimizations
- `React.memo` used for MinerRow component
- `useMemo` for expensive calculations (profit matrix)
- `useCallback` for event handlers
- LocalStorage updates are debounced via useEffect

### Data Persistence
- All data stored in browser LocalStorage
- Keys: `minerProfitMatrix_miners`, `minerProfitMatrix_prices`, `minerProfitMatrix_params`, `minerProfitMatrix_scenarios`
- Data persists across browser sessions
- Export/Import for backup and sharing

### Calculation Accuracy
- Uses actual Bitcoin network constants (3.125 BTC block reward, 144 blocks/day)
- Accounts for pool fees and electricity costs
- Includes federal and state tax calculations
- Supports both bonus depreciation and MACRS schedules

## Development

### Code Quality Standards
- PropTypes on all components
- Pure functions for calculations (no side effects)
- Custom hooks for business logic
- Modular component structure
- Comprehensive error handling

### Adding a New Miner
Edit `src/utils/constants.js` and add to `DEFAULT_PRESET_MINERS`:

```javascript
{
  id: 21,
  name: "S22 Pro",
  fullName: "Bitmain Antminer S22 Pro",
  hashrate: 250,
  power: 3600,
  efficiency: 14.4,
  defaultPrice: 5000,
  manufacturer: "Bitmain",
  coolingType: "Air",
  releaseYear: 2025,
  series: "S22"
}
```

### Running Tests
```bash
npm test
```

Tests are located in `tests/` directory (to be implemented).

## License

Private/Internal Use

## Related Projects

- [102-bitcoin-mining-electricity-calculator](../102-bitcoin-mining-electricity-calculator) - Detailed 3-year projections
- [105-miner-acquisition-calculator](../105-miner-acquisition-calculator) - Calculate max acquisition price
- [106-hosted-mining-portfolio](../106-hosted-mining-portfolio) - Multi-company portfolio tracking
