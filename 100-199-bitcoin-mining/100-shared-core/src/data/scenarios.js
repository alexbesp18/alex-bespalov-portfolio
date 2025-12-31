/**
 * Market Scenarios and Presets
 * 
 * Predefined market scenarios for quick parameter loading.
 * 
 * @module data/scenarios
 */

/**
 * Preset market scenarios
 * @constant {Object}
 */
export const PRESET_SCENARIOS = {
  current: {
    name: 'Current Market',
    description: 'Based on current market conditions',
    params: {
      btcPriceStart: 100000,
      btcPriceEnd: 150000,
      networkHashrateStart: 900,
      networkHashrateEnd: 1100,
      poolFee: 2,
      taxRate: 35,
      stateRate: 0,
      useBonusDepreciation: true,
    },
  },
  
  conservative: {
    name: 'Conservative',
    description: 'Lower price growth, higher difficulty growth',
    params: {
      btcPriceStart: 100000,
      btcPriceEnd: 120000,
      networkHashrateStart: 900,
      networkHashrateEnd: 1200,
      poolFee: 2,
      taxRate: 35,
      stateRate: 5,
      useBonusDepreciation: true,
    },
  },
  
  bullish: {
    name: 'Bullish 2025',
    description: 'Optimistic price projection',
    params: {
      btcPriceStart: 100000,
      btcPriceEnd: 200000,
      networkHashrateStart: 900,
      networkHashrateEnd: 1300,
      poolFee: 2,
      taxRate: 35,
      stateRate: 0,
      useBonusDepreciation: true,
    },
  },
  
  superBullish: {
    name: 'Super Bull',
    description: 'Very optimistic - 3x BTC price',
    params: {
      btcPriceStart: 100000,
      btcPriceEnd: 300000,
      networkHashrateStart: 900,
      networkHashrateEnd: 1500,
      poolFee: 2,
      taxRate: 35,
      stateRate: 0,
      useBonusDepreciation: true,
    },
  },
  
  bearish: {
    name: 'Bearish',
    description: 'Price decline scenario',
    params: {
      btcPriceStart: 100000,
      btcPriceEnd: 70000,
      networkHashrateStart: 900,
      networkHashrateEnd: 800,
      poolFee: 2,
      taxRate: 35,
      stateRate: 0,
      useBonusDepreciation: true,
    },
  },
  
  sideways: {
    name: 'Sideways',
    description: 'Flat price, moderate difficulty growth',
    params: {
      btcPriceStart: 100000,
      btcPriceEnd: 105000,
      networkHashrateStart: 900,
      networkHashrateEnd: 1050,
      poolFee: 2,
      taxRate: 35,
      stateRate: 0,
      useBonusDepreciation: true,
    },
  },
  
  halvingYear: {
    name: '2028 Halving Year',
    description: 'Accounts for block reward reduction',
    params: {
      btcPriceStart: 150000,
      btcPriceEnd: 250000,
      networkHashrateStart: 1500,
      networkHashrateEnd: 1800,
      poolFee: 2,
      taxRate: 35,
      stateRate: 0,
      useBonusDepreciation: false, // Bonus depreciation phased out
    },
  },
  
  texasMiner: {
    name: 'Texas Miner',
    description: 'Texas-based operation, no state tax',
    params: {
      btcPriceStart: 100000,
      btcPriceEnd: 150000,
      networkHashrateStart: 900,
      networkHashrateEnd: 1100,
      poolFee: 2,
      taxRate: 35,
      stateRate: 0,
      useBonusDepreciation: true,
    },
  },
  
  californiaMiner: {
    name: 'California Miner',
    description: 'California-based, high state tax',
    params: {
      btcPriceStart: 100000,
      btcPriceEnd: 150000,
      networkHashrateStart: 900,
      networkHashrateEnd: 1100,
      poolFee: 2,
      taxRate: 35,
      stateRate: 13.3,
      useBonusDepreciation: true,
    },
  },
};

/**
 * Get a scenario by key
 * 
 * @param {string} key - Scenario key
 * @returns {Object|undefined} Scenario object or undefined
 */
export const getScenario = (key) => {
  return PRESET_SCENARIOS[key];
};

/**
 * Get all scenario keys
 * 
 * @returns {string[]} Array of scenario keys
 */
export const getScenarioKeys = () => {
  return Object.keys(PRESET_SCENARIOS);
};

/**
 * Get scenarios grouped by category
 * 
 * @returns {Object} Scenarios grouped by category
 */
export const getScenariosByCategory = () => {
  return {
    market: ['current', 'conservative', 'bullish', 'superBullish', 'bearish', 'sideways'],
    special: ['halvingYear'],
    location: ['texasMiner', 'californiaMiner'],
  };
};

/**
 * Create a custom scenario
 * 
 * @param {string} name - Scenario name
 * @param {string} description - Scenario description
 * @param {Object} params - Scenario parameters
 * @returns {Object} New scenario object
 */
export const createScenario = (name, description, params) => {
  return {
    name,
    description,
    params: { ...PRESET_SCENARIOS.current.params, ...params },
    isCustom: true,
    createdAt: new Date().toISOString(),
  };
};

/**
 * Calculate annual growth rates from start/end values
 * 
 * @param {Object} params - Parameters with start/end values
 * @returns {Object} Annual growth rates
 */
export const calculateGrowthRates = (params) => {
  const btcGrowth = ((params.btcPriceEnd - params.btcPriceStart) / params.btcPriceStart) * 100;
  const difficultyGrowth = ((params.networkHashrateEnd - params.networkHashrateStart) / params.networkHashrateStart) * 100;
  
  return {
    annualBtcPriceIncrease: Math.round(btcGrowth * 10) / 10,
    annualDifficultyIncrease: Math.round(difficultyGrowth * 10) / 10,
  };
};

/**
 * Calculate end values from annual growth rates
 * 
 * @param {Object} params - Parameters with start values and growth rates
 * @returns {Object} End values
 */
export const calculateEndValues = (params) => {
  return {
    btcPriceEnd: params.btcPriceStart * (1 + params.annualBtcPriceIncrease / 100),
    networkHashrateEnd: params.networkHashrateStart * (1 + params.annualDifficultyIncrease / 100),
  };
};

/**
 * Validate scenario parameters
 * 
 * @param {Object} params - Parameters to validate
 * @returns {Object} Validation result with isValid and errors
 */
export const validateScenarioParams = (params) => {
  const errors = [];
  
  if (!params.btcPriceStart || params.btcPriceStart <= 0) {
    errors.push('BTC start price must be positive');
  }
  
  if (!params.networkHashrateStart || params.networkHashrateStart <= 0) {
    errors.push('Network hashrate must be positive');
  }
  
  if (params.poolFee < 0 || params.poolFee > 100) {
    errors.push('Pool fee must be between 0-100%');
  }
  
  if (params.taxRate < 0 || params.taxRate > 100) {
    errors.push('Tax rate must be between 0-100%');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

