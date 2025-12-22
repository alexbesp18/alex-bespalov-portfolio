/**
 * Options Valuation Calculations
 * 
 * Black-Scholes approximation and options valuation for portfolio analysis.
 * 
 * @module calculations/options
 */

import { validateNumber } from '../validation/numbers.js';

/**
 * Calculate intrinsic value of an option
 * 
 * @param {string} type - Option type ('call' or 'put')
 * @param {number} currentPrice - Current underlying price
 * @param {number} strikePrice - Strike price
 * @returns {number} Intrinsic value
 */
export const calculateIntrinsicValue = (type, currentPrice, strikePrice) => {
  if (type === 'call') {
    return Math.max(0, currentPrice - strikePrice);
  }
  return Math.max(0, strikePrice - currentPrice);
};

/**
 * Calculate time value using simplified Black-Scholes approximation
 * 
 * @param {number} currentPrice - Current underlying price
 * @param {number} monthsToExpiry - Months until expiration
 * @param {number} [volatility=0.8] - Implied volatility (decimal)
 * @returns {number} Time value component
 */
export const calculateTimeValue = (currentPrice, monthsToExpiry, volatility = 0.8) => {
  if (monthsToExpiry <= 0 || currentPrice <= 0) return 0;
  
  const annualizedTime = monthsToExpiry / 12;
  // Simplified time value approximation
  return currentPrice * volatility * Math.sqrt(annualizedTime) * 0.2;
};

/**
 * Calculate option value using Black-Scholes approximation
 * 
 * @param {Object} option - Option details
 * @param {string} option.type - 'call' or 'put'
 * @param {number} option.strike - Strike price
 * @param {number} option.contracts - Number of contracts
 * @param {number} option.costBasis - Cost basis per contract
 * @param {number} currentPrice - Current underlying price
 * @param {number} projectedPrice - Projected price at expiry
 * @param {number} monthsToExpiry - Months until expiration
 * @param {Object} [config={}] - Configuration options
 * @returns {Object} Option valuation
 */
export const calculateOptionValue = (option, currentPrice, projectedPrice, monthsToExpiry, config = {}) => {
  const { volatility = 0.8 } = config;
  const { strike, contracts = 1, type = 'call', costBasis = 0 } = option;
  
  // Validate inputs
  const validStrike = validateNumber(strike, 0);
  const validContracts = Math.max(1, parseInt(contracts) || 1);
  const validCurrentPrice = validateNumber(currentPrice, 0);
  const validProjectedPrice = validateNumber(projectedPrice, 0);
  const validMonthsToExpiry = validateNumber(monthsToExpiry, 0);
  
  // Calculate intrinsic value
  const intrinsicValue = calculateIntrinsicValue(type, validCurrentPrice, validStrike);
  
  // Calculate time value
  const timeValue = calculateTimeValue(validCurrentPrice, validMonthsToExpiry, volatility);
  
  // Current option price (at least intrinsic value)
  const optionPrice = Math.max(intrinsicValue, intrinsicValue + timeValue);
  const currentValue = optionPrice * validContracts * 100; // 100 shares per contract
  
  // Projected value at expiry (intrinsic only, no time value)
  const projectedIntrinsicValue = calculateIntrinsicValue(type, validProjectedPrice, validStrike);
  const projectedValue = projectedIntrinsicValue * validContracts * 100;
  
  // Cost and P/L
  const costBasisTotal = validateNumber(costBasis, 0) * validContracts * 100;
  const profitLoss = currentValue - costBasisTotal;
  const profitLossPercent = costBasisTotal > 0 ? (profitLoss / costBasisTotal) * 100 : 0;
  
  return {
    currentValue,
    projectedValue,
    intrinsicValue,
    timeValue,
    optionPrice,
    inTheMoney: intrinsicValue > 0,
    profitLoss,
    profitLossPercent,
    costBasisTotal,
    contracts: validContracts,
  };
};

/**
 * Calculate months until expiration
 * 
 * @param {string|Date} expiryDate - Expiration date
 * @returns {number} Months until expiry (0 if expired)
 */
export const getMonthsToExpiry = (expiryDate) => {
  try {
    const expiry = new Date(expiryDate);
    const now = new Date();
    
    if (isNaN(expiry.getTime())) return 0;
    
    const diffMs = expiry - now;
    const months = diffMs / (1000 * 60 * 60 * 24 * 30.42);
    
    return Math.max(0, months);
  } catch {
    return 0;
  }
};

/**
 * Categorize option by time to expiry
 * 
 * @param {number} monthsToExpiry - Months until expiry
 * @returns {string} Category ('short', 'medium', 'long')
 */
export const categorizeByExpiry = (monthsToExpiry) => {
  if (monthsToExpiry <= 6) return 'short';
  if (monthsToExpiry <= 12) return 'medium';
  return 'long';
};

/**
 * Calculate total value of options portfolio
 * 
 * @param {Object[]} options - Array of options
 * @param {Object} prices - Current prices by underlying
 * @returns {Object} Portfolio summary
 */
export const calculateOptionsPortfolioValue = (options, prices) => {
  let totalValue = 0;
  let totalCost = 0;
  
  const byCategory = {
    short: 0,
    medium: 0,
    long: 0,
  };
  
  const byUnderlying = {};
  
  options.forEach(option => {
    const underlying = option.underlying?.toLowerCase() || 'unknown';
    const currentPrice = prices[underlying] || 0;
    const monthsToExpiry = getMonthsToExpiry(option.expiry);
    
    const valuation = calculateOptionValue(option, currentPrice, currentPrice, monthsToExpiry);
    
    totalValue += valuation.currentValue;
    totalCost += valuation.costBasisTotal;
    
    // By category
    const category = categorizeByExpiry(monthsToExpiry);
    byCategory[category] += valuation.currentValue;
    
    // By underlying
    if (!byUnderlying[underlying]) {
      byUnderlying[underlying] = 0;
    }
    byUnderlying[underlying] += valuation.currentValue;
  });
  
  return {
    totalValue,
    totalCost,
    profitLoss: totalValue - totalCost,
    profitLossPercent: totalCost > 0 ? ((totalValue - totalCost) / totalCost) * 100 : 0,
    byCategory,
    byUnderlying,
    count: options.length,
  };
};

/**
 * Calculate option delta (simplified)
 * Measures sensitivity to underlying price change
 * 
 * @param {string} type - Option type
 * @param {number} currentPrice - Current underlying price
 * @param {number} strikePrice - Strike price
 * @param {number} monthsToExpiry - Months to expiry
 * @returns {number} Delta (-1 to 1)
 */
export const calculateDelta = (type, currentPrice, strikePrice, monthsToExpiry) => {
  const moneyness = currentPrice / strikePrice;
  const timeDecay = Math.min(1, monthsToExpiry / 12);
  
  // Simplified delta calculation
  if (type === 'call') {
    if (moneyness > 1.2) return 0.9 + (0.1 * timeDecay);
    if (moneyness > 1.0) return 0.5 + (0.4 * (moneyness - 1) * 5);
    if (moneyness > 0.8) return 0.1 + (0.4 * (moneyness - 0.8) * 5);
    return 0.1 * timeDecay;
  } else {
    if (moneyness < 0.8) return -0.9 - (0.1 * timeDecay);
    if (moneyness < 1.0) return -0.5 - (0.4 * (1 - moneyness) * 5);
    if (moneyness < 1.2) return -0.1 - (0.4 * (1.2 - moneyness) * 5);
    return -0.1 * timeDecay;
  }
};

