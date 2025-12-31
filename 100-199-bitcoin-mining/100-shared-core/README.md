# @btc-mining/shared-core

Shared utilities for Bitcoin mining calculators. This package provides a single source of truth for:

- **Constants**: Bitcoin network parameters, tax rates, electricity presets
- **Calculations**: Mining profitability, multi-year projections, tax analysis
- **Data**: Miner database, market scenarios, power consumption reference
- **Formatters**: Currency, numbers, percentages, dates
- **Storage**: LocalStorage utilities with compression and migration
- **Export**: JSON, CSV, and Excel utilities
- **Validation**: Number validation, miner schema validation
- **React Hooks**: useLocalStorage, useMiningCalculations, useScenarios

## Installation

Add to your project's `package.json`:

```json
{
  "dependencies": {
    "@btc-mining/shared-core": "file:../100-shared-core"
  }
}
```

Then run `npm install`.

## Quick Start

```javascript
// Import specific modules
import {
  BLOCK_REWARD,
  ELECTRICITY_RATES,
  calculateMonthlyProfit,
  formatCurrency,
  useMiningCalculations,
} from '@btc-mining/shared-core';

// Or import from specific paths for tree-shaking
import { BLOCK_REWARD } from '@btc-mining/shared-core/constants';
import { calculateMonthlyProfit } from '@btc-mining/shared-core/calculations';
import { formatCurrency } from '@btc-mining/shared-core/formatters';
```

## Module Reference

### Constants

#### `constants/bitcoin.js`
```javascript
import { 
  BLOCK_REWARD,          // Current block reward (3.125 BTC)
  BLOCKS_PER_DAY,        // 144 blocks
  DAYS_PER_YEAR,         // 365 days
  HALVING_DATES,         // Historical and projected halving dates
  getEffectiveBlockReward,  // Get block reward for a date
  getHalvingInRange,     // Check if halving occurs in date range
} from '@btc-mining/shared-core';
```

#### `constants/tax.js`
```javascript
import {
  MACRS_RATES,           // 5-year depreciation schedule
  STATE_TAX_RATES,       // Common state tax rates by state
  calculateDepreciation, // Calculate depreciation by year
  calculateTaxLiability, // Calculate total tax
} from '@btc-mining/shared-core';
```

#### `constants/electricity.js`
```javascript
import {
  ELECTRICITY_RATES,     // Standard rates for matrix [0.047 - 0.10]
  ELECTRICITY_PRESETS,   // Named presets (cheap, industrial, hosting, etc.)
  REGIONAL_ELECTRICITY_RATES, // Rates by region
} from '@btc-mining/shared-core';
```

#### `constants/defaults.js`
```javascript
import {
  DEFAULT_PARAMS,        // Default calculation parameters
  STORAGE_KEYS,          // LocalStorage key constants
  createParams,          // Merge custom params with defaults
  validateParams,        // Validate and sanitize params
} from '@btc-mining/shared-core';
```

### Calculations

#### Core Mining (`calculations/mining.js`)
```javascript
import {
  calculateNetworkShare,    // Miner's share of network hashrate
  calculateDailyBtcMined,   // Daily BTC production
  calculateMonthlyBtcMined, // Monthly BTC production
  calculateMonthlyProfit,   // Complete monthly profit breakdown
  calculateBreakevenElectricityRate, // Max electricity rate for profit
  calculateBreakevenBtcPrice,        // Min BTC price for profit
} from '@btc-mining/shared-core';

// Example
const profit = calculateMonthlyProfit(
  { hashrate: 500, power: 5500 },  // Miner
  {
    btcPrice: 100000,
    networkHashrate: 900,
    electricityRate: 0.05,
    poolFee: 2,
  }
);
// Returns: { btcMined, grossRevenue, electricityCost, operationalProfit, ... }
```

#### Projections (`calculations/projections.js`)
```javascript
import {
  calculateMonthlyDetails,    // Detailed monthly breakdown
  calculateYearlyProfit,      // 1-year profit with ROI
  calculateTwoYearProfit,     // 2-year cumulative analysis
  calculateThreeYearProfit,   // 3-year cumulative analysis
  calculateMultiYearProjection, // N-year projection
  calculatePaybackPeriod,     // Months until breakeven
} from '@btc-mining/shared-core';
```

#### Tax Analysis (`calculations/taxes.js`)
```javascript
import {
  calculateMiningTax,         // Full tax breakdown
  calculateDepreciationSchedule, // MACRS schedule
  calculateMaxAcquisitionPrice,  // Max price for target profit
} from '@btc-mining/shared-core';
```

#### Risk Metrics (`calculations/risk.js`)
```javascript
import {
  calculateIRR,             // Internal Rate of Return
  calculateNPV,             // Net Present Value
  calculateRiskMetrics,     // Risk score and metrics
  calculateQuickInsights,   // Summary insights from profit matrix
  getCellColor,             // Color coding for profit values
} from '@btc-mining/shared-core';
```

### Data

#### Miner Database (`data/miners.js`)
```javascript
import {
  MINER_DATABASE,      // Complete miner database
  getAllMiners,        // Get all miners
  getMinerById,        // Find by ID
  getMinerByName,      // Find by name (partial match)
  getMinersBy,         // Filter by criteria
  sortMiners,          // Sort miners by field
} from '@btc-mining/shared-core';

// Example
const efficientMiners = getMinersBy({ maxEfficiency: 15 });
const bitmainHydro = getMinersBy({ manufacturer: 'Bitmain', coolingType: 'Hydro' });
```

#### Scenarios (`data/scenarios.js`)
```javascript
import {
  PRESET_SCENARIOS,    // Built-in market scenarios
  getScenario,         // Get scenario by key
  createScenario,      // Create custom scenario
  calculateGrowthRates, // Calculate rates from start/end
} from '@btc-mining/shared-core';
```

### Formatters

```javascript
import {
  // Currency
  formatCurrency,      // $1,234 or $1.23M
  formatBTC,           // ₿0.1234
  formatElectricityRate, // $0.065
  
  // Numbers
  formatNumber,        // 1,234,567
  formatPercentage,    // 45.6%
  formatHashrate,      // 500 TH/s or 1.5 EH/s
  formatPower,         // 3.5 kW
  formatEfficiency,    // 15.5 J/TH
  formatCompact,       // 1.5M
  
  // Dates
  formatDate,          // 2025-01-15
  formatDateHuman,     // January 15, 2025
  formatRelativeTime,  // 2 days ago
  formatDuration,      // 1 year, 6 months
} from '@btc-mining/shared-core';
```

### Storage

```javascript
import {
  createStorageManager,  // Namespaced localStorage wrapper
  isLocalStorageAvailable,
  
  // Compression
  compressData,         // LZ compress for large datasets
  decompressData,
  smartCompress,        // Only compress if beneficial
  
  // Migration
  createMigrationManager, // Version-based data migrations
  migrateWithDefaults,  // Merge with default values
} from '@btc-mining/shared-core';

// Example
const storage = createStorageManager('myApp');
storage.set('miners', minerData);
const miners = storage.get('miners', []);
```

### Validation

```javascript
import {
  // Numbers
  validateNumber,      // Clamp to min/max
  validatePositive,    // Ensure positive
  validatePercentage,  // Clamp to 0-100
  isValidNumber,       // Check if valid number
  roundTo,             // Round to decimals
  clamp,               // Clamp value
  safeDivide,          // Divide with zero fallback
  
  // Miners
  validateMiner,       // Validate miner object
  sanitizeMiner,       // Sanitize with defaults
  validateMiners,      // Validate array of miners
} from '@btc-mining/shared-core';
```

### Export

```javascript
import {
  // JSON
  exportToJSON,        // Download as JSON file
  importFromJSON,      // Parse JSON file
  createJSONImportHandler, // File input handler
  
  // CSV
  exportToCSV,         // Download as CSV
  importFromCSV,       // Parse CSV file
  arrayToCSV,          // Convert to CSV string
  parseCSV,            // Parse CSV string
} from '@btc-mining/shared-core';
```

### React Hooks

```javascript
import {
  useLocalStorage,        // Persistent state
  useMiningCalculations,  // Mining calculation hook
  useScenarios,           // Scenario management hook
} from '@btc-mining/shared-core';

// useLocalStorage
const [miners, setMiners] = useLocalStorage('miners', []);

// useMiningCalculations
const {
  profitMatrix,
  quickInsights,
  calculateYearly,
  findBestMiner,
} = useMiningCalculations(miners, minerPrices, params);

// useScenarios
const {
  params,
  loadScenario,
  saveScenario,
  customScenarios,
} = useScenarios();
```

## Migration Guide

### From Inline Constants

Before:
```javascript
const BLOCK_REWARD = 3.125;
const BLOCKS_PER_DAY = 144;
const MACRS_RATES = [0.20, 0.32, ...];
```

After:
```javascript
import { BLOCK_REWARD, BLOCKS_PER_DAY, MACRS_RATES } from '@btc-mining/shared-core';
```

### From Inline Calculations

Before:
```javascript
const calculateMonthlyProfit = (miner, params) => {
  const share = miner.hashrate / (params.networkHashrate * 1000000);
  // ... 50 lines of calculation logic
};
```

After:
```javascript
import { calculateMonthlyProfit } from '@btc-mining/shared-core';
```

### From Inline Formatters

Before:
```javascript
const formatCurrency = (value) => `$${value.toLocaleString()}`;
const formatPercentage = (value) => `${value.toFixed(1)}%`;
```

After:
```javascript
import { formatCurrency, formatPercentage } from '@btc-mining/shared-core';
```

## Testing

```bash
npm test           # Run tests
npm run test:watch # Watch mode
npm run test:coverage # Coverage report
```

## Architecture

```
100-shared-core/
├── src/
│   ├── index.js           # Main barrel export
│   ├── constants/
│   │   ├── bitcoin.js     # Network constants
│   │   ├── tax.js         # Tax/depreciation
│   │   ├── electricity.js # Electricity rates
│   │   └── defaults.js    # Default parameters
│   ├── calculations/
│   │   ├── mining.js      # Core mining math
│   │   ├── projections.js # Multi-year projections
│   │   ├── taxes.js       # Tax calculations
│   │   ├── options.js     # Options valuation
│   │   └── risk.js        # Risk metrics
│   ├── data/
│   │   ├── miners.js      # Miner database
│   │   ├── powerDatabase.js # Power reference
│   │   └── scenarios.js   # Market scenarios
│   ├── formatters/
│   │   ├── currency.js    # Currency formatting
│   │   ├── numbers.js     # Number formatting
│   │   └── dates.js       # Date formatting
│   ├── storage/
│   │   ├── localStorage.js # Storage wrapper
│   │   ├── compression.js # LZ compression
│   │   └── migration.js   # Data migrations
│   ├── export/
│   │   ├── json.js        # JSON export/import
│   │   ├── csv.js         # CSV export/import
│   │   └── excel.js       # Excel utilities
│   ├── validation/
│   │   ├── numbers.js     # Number validation
│   │   └── miners.js      # Miner validation
│   ├── hooks/
│   │   ├── useLocalStorage.js
│   │   ├── useMiningCalculations.js
│   │   └── useScenarios.js
│   └── __tests__/
│       ├── mining.test.js
│       ├── formatters.test.js
│       └── validation.test.js
```

## License

MIT

