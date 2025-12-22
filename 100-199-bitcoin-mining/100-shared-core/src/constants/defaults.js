/**
 * Default Parameters and Configuration
 * 
 * Default values for calculation parameters used across all calculators.
 * 
 * @module constants/defaults
 */

/**
 * Default calculation parameters
 * @constant {Object}
 */
export const DEFAULT_PARAMS = {
  // Bitcoin price projections
  btcPriceStart: 110000,
  btcPriceEnd: 150000,
  
  // Network hashrate projections (EH/s)
  networkHashrateStart: 900,
  networkHashrateEnd: 1100,
  
  // Fees
  poolFee: 2,
  
  // Tax rates (%)
  taxRate: 35,
  stateRate: 0,
  federalTaxRate: 35,
  stateTaxRate: 0,
  
  // Depreciation
  useBonusDepreciation: true,
  
  // Annual growth rates (%)
  annualBtcPriceIncrease: 36.4,
  annualDifficultyIncrease: 22.2,
  useAnnualIncreases: false,
  
  // Projection settings
  projectionYears: 2,
};

/**
 * Default parameters for 3-year projections
 * @constant {Object}
 */
export const DEFAULT_PARAMS_3_YEAR = {
  ...DEFAULT_PARAMS,
  projectionYears: 3,
  // Extended projections
  year2BtcPriceMultiplier: 1.5,
  year3BtcPriceMultiplier: 2.0,
  year2DifficultyMultiplier: 1.3,
  year3DifficultyMultiplier: 1.6,
};

/**
 * Default mining parameters for portfolio analysis
 * @constant {Object}
 */
export const DEFAULT_MINING_PARAMS = {
  networkHashrate: 900,
  monthlyDifficultyGrowth: 2.5,
  blockReward: 3.125,
  blocksPerDay: 144,
};

/**
 * Default hosting company parameters
 * @constant {Object}
 */
export const DEFAULT_HOSTING_PARAMS = {
  electricityRate: 0.075,
  managementFee: 5,
  uptime: 98,
};

/**
 * Create custom parameters by merging with defaults
 * 
 * @param {Object} customParams - Custom parameter overrides
 * @param {Object} [baseParams=DEFAULT_PARAMS] - Base parameters to extend
 * @returns {Object} Merged parameters
 */
export const createParams = (customParams, baseParams = DEFAULT_PARAMS) => {
  return { ...baseParams, ...customParams };
};

/**
 * Validate and sanitize parameters
 * 
 * @param {Object} params - Parameters to validate
 * @returns {Object} Validated parameters with defaults for invalid values
 */
export const validateParams = (params) => {
  const validated = { ...DEFAULT_PARAMS };
  
  for (const [key, value] of Object.entries(params)) {
    if (key in DEFAULT_PARAMS) {
      const defaultValue = DEFAULT_PARAMS[key];
      
      if (typeof defaultValue === 'number') {
        const numValue = parseFloat(value);
        validated[key] = isNaN(numValue) ? defaultValue : numValue;
      } else if (typeof defaultValue === 'boolean') {
        validated[key] = Boolean(value);
      } else {
        validated[key] = value;
      }
    }
  }
  
  return validated;
};

/**
 * Storage keys for localStorage
 * @constant {Object}
 */
export const STORAGE_KEYS = {
  MINERS: 'minerProfitMatrix_miners',
  PRICES: 'minerProfitMatrix_prices',
  PARAMS: 'minerProfitMatrix_params',
  SCENARIOS: 'minerProfitMatrix_scenarios',
  HAS_VISITED: 'hasVisited',
  
  // Miner Acquisition Calculator
  ACQUISITION_MINERS: 'minerAcquisitionCalc_miners',
  ACQUISITION_PARAMS: 'minerAcquisitionCalc_params',
  ACQUISITION_SCENARIOS: 'minerAcquisitionCalc_scenarios',
  
  // Hosted Mining Portfolio
  PORTFOLIO_COMPANIES: 'miningPortfolio_companies',
  PORTFOLIO_MINERS: 'miningPortfolio_miners',
  PORTFOLIO_PARAMS: 'miningPortfolio_params',
  
  // Miner Price Tracker
  TRACKER_MINERS: 'minerPriceTracker_miners',
  TRACKER_HISTORY: 'minerPriceTracker_history',
  TRACKER_SPECS: 'minerPriceTracker_specs',
};

