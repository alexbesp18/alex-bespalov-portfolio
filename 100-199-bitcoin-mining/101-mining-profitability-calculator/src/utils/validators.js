/**
 * Input validation utility functions
 */

/**
 * Validate miner object
 * @param {Object} miner - Miner object to validate
 * @returns {Object} - { isValid: boolean, errors: Array<string> }
 */
export const validateMiner = (miner) => {
  const errors = [];
  
  if (!miner.name || miner.name.trim() === '') {
    errors.push('Miner name is required');
  }
  
  if (!miner.hashrate || miner.hashrate <= 0) {
    errors.push('Hashrate must be greater than 0');
  }
  
  if (!miner.power || miner.power <= 0) {
    errors.push('Power consumption must be greater than 0');
  }
  
  if (!miner.defaultPrice || miner.defaultPrice < 0) {
    errors.push('Price must be non-negative');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

/**
 * Validate calculation parameters
 * @param {Object} params - Parameters to validate
 * @returns {Object} - { isValid: boolean, errors: Array<string> }
 */
export const validateParams = (params) => {
  const errors = [];
  
  if (params.btcPriceStart <= 0) {
    errors.push('BTC start price must be greater than 0');
  }
  
  if (params.btcPriceEnd <= 0) {
    errors.push('BTC end price must be greater than 0');
  }
  
  if (params.networkHashrateStart <= 0) {
    errors.push('Network hashrate start must be greater than 0');
  }
  
  if (params.networkHashrateEnd <= 0) {
    errors.push('Network hashrate end must be greater than 0');
  }
  
  if (params.poolFee < 0 || params.poolFee > 100) {
    errors.push('Pool fee must be between 0 and 100');
  }
  
  if (params.taxRate < 0 || params.taxRate > 100) {
    errors.push('Tax rate must be between 0 and 100');
  }
  
  if (params.stateRate < 0 || params.stateRate > 100) {
    errors.push('State tax rate must be between 0 and 100');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

/**
 * Validate electricity rate
 * @param {number} rate - Electricity rate
 * @returns {boolean} - Whether rate is valid
 */
export const validateElectricityRate = (rate) => {
  return rate > 0 && rate < 1; // Reasonable range: $0.01 to $0.99/kWh
};
