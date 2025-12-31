/**
 * Currency Formatting Utilities
 * 
 * Functions for formatting currency values, BTC amounts, and electricity rates.
 * 
 * @module formatters/currency
 */

/**
 * Format a number as USD currency
 * 
 * @param {number} value - Value to format
 * @param {Object} [options={}] - Formatting options
 * @param {number} [options.decimals=0] - Number of decimal places
 * @param {boolean} [options.showSign=false] - Show +/- sign
 * @param {boolean} [options.compact=false] - Use compact notation (K, M, B)
 * @returns {string} Formatted currency string
 * @example
 * formatCurrency(1234.56) // "$1,235"
 * formatCurrency(1234.56, { decimals: 2 }) // "$1,234.56"
 * formatCurrency(1234567, { compact: true }) // "$1.23M"
 */
export const formatCurrency = (value, options = {}) => {
  const { decimals = 0, showSign = false, compact = false } = options;
  
  if (value === null || value === undefined || isNaN(value)) {
    return '$0';
  }
  
  const absValue = Math.abs(value);
  let formatted;
  
  if (compact) {
    if (absValue >= 1e9) {
      formatted = `$${(absValue / 1e9).toFixed(2)}B`;
    } else if (absValue >= 1e6) {
      formatted = `$${(absValue / 1e6).toFixed(2)}M`;
    } else if (absValue >= 1e3) {
      formatted = `$${(absValue / 1e3).toFixed(1)}K`;
    } else {
      formatted = `$${absValue.toFixed(decimals)}`;
    }
  } else {
    formatted = `$${absValue.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })}`;
  }
  
  if (value < 0) {
    return `-${formatted}`;
  }
  
  if (showSign && value > 0) {
    return `+${formatted}`;
  }
  
  return formatted;
};

/**
 * Format a number as BTC
 * 
 * @param {number} value - BTC value to format
 * @param {number} [decimals=4] - Number of decimal places
 * @param {boolean} [showSymbol=true] - Whether to show ₿ symbol
 * @returns {string} Formatted BTC string
 * @example
 * formatBTC(0.12345678) // "₿0.1235"
 * formatBTC(1.5, 2, false) // "1.50"
 */
export const formatBTC = (value, decimals = 4, showSymbol = true) => {
  if (value === null || value === undefined || isNaN(value)) {
    return showSymbol ? '₿0' : '0';
  }
  
  const formatted = value.toFixed(decimals);
  return showSymbol ? `₿${formatted}` : formatted;
};

/**
 * Format electricity rate
 * 
 * @param {number} rate - Rate in $/kWh
 * @param {number} [decimals=3] - Number of decimal places
 * @returns {string} Formatted rate string
 * @example
 * formatElectricityRate(0.065) // "$0.065"
 */
export const formatElectricityRate = (rate) => {
  if (rate === null || rate === undefined || isNaN(rate)) {
    return '$0.000';
  }
  return `$${rate.toFixed(3)}`;
};

/**
 * Format electricity rate with unit
 * 
 * @param {number} rate - Rate in $/kWh
 * @returns {string} Formatted rate with unit
 * @example
 * formatElectricityRateWithUnit(0.065) // "$0.065/kWh"
 */
export const formatElectricityRateWithUnit = (rate) => {
  return `${formatElectricityRate(rate)}/kWh`;
};

/**
 * Format a value as a price (positive only, with $ prefix)
 * 
 * @param {number} value - Price value
 * @param {number} [decimals=0] - Decimal places
 * @returns {string} Formatted price
 */
export const formatPrice = (value, decimals = 0) => {
  if (value === null || value === undefined || isNaN(value) || value < 0) {
    return '$0';
  }
  return formatCurrency(value, { decimals });
};

/**
 * Format a value as cost per unit
 * 
 * @param {number} value - Cost value
 * @param {string} unit - Unit string (e.g., "BTC", "TH", "kWh")
 * @param {number} [decimals=2] - Decimal places
 * @returns {string} Formatted cost per unit
 * @example
 * formatCostPerUnit(45000, "BTC") // "$45,000/BTC"
 */
export const formatCostPerUnit = (value, unit, decimals = 2) => {
  return `${formatCurrency(value, { decimals })}/${unit}`;
};

