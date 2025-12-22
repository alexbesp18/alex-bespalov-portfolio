/**
 * Number Formatting Utilities
 * 
 * Functions for formatting numbers, percentages, and hashrates.
 * 
 * @module formatters/numbers
 */

/**
 * Format a number with thousands separators
 * 
 * @param {number} value - Value to format
 * @param {number} [decimals=0] - Number of decimal places
 * @returns {string} Formatted number string
 * @example
 * formatNumber(1234567) // "1,234,567"
 * formatNumber(1234.567, 2) // "1,234.57"
 */
export const formatNumber = (value, decimals = 0) => {
  if (value === null || value === undefined || isNaN(value)) {
    return '0';
  }
  
  return value.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

/**
 * Format a number as percentage
 * 
 * @param {number} value - Value to format (as percentage, not decimal)
 * @param {number} [decimals=1] - Number of decimal places
 * @param {boolean} [showSign=false] - Show +/- sign for positive/negative
 * @returns {string} Formatted percentage string
 * @example
 * formatPercentage(45.6) // "45.6%"
 * formatPercentage(-10.5, 1, true) // "-10.5%"
 */
export const formatPercentage = (value, decimals = 1, showSign = false) => {
  if (value === null || value === undefined || isNaN(value)) {
    return '0%';
  }
  
  const formatted = `${value.toFixed(decimals)}%`;
  
  if (showSign && value > 0) {
    return `+${formatted}`;
  }
  
  return formatted;
};

/**
 * Format a decimal as percentage (multiply by 100 first)
 * 
 * @param {number} decimal - Decimal value (0.456 = 45.6%)
 * @param {number} [decimals=1] - Number of decimal places
 * @returns {string} Formatted percentage string
 * @example
 * formatDecimalAsPercentage(0.456) // "45.6%"
 */
export const formatDecimalAsPercentage = (decimal, decimals = 1) => {
  return formatPercentage(decimal * 100, decimals);
};

/**
 * Format hashrate with appropriate unit
 * 
 * @param {number} hashrateTH - Hashrate in TH/s
 * @param {number} [decimals=0] - Decimal places
 * @returns {string} Formatted hashrate with unit
 * @example
 * formatHashrate(500) // "500 TH/s"
 * formatHashrate(1500) // "1.5 PH/s"
 * formatHashrate(1500000) // "1.5 EH/s"
 */
export const formatHashrate = (hashrateTH, decimals = 0) => {
  if (hashrateTH === null || hashrateTH === undefined || isNaN(hashrateTH)) {
    return '0 TH/s';
  }
  
  if (hashrateTH >= 1000000) {
    return `${(hashrateTH / 1000000).toFixed(decimals || 2)} EH/s`;
  }
  
  if (hashrateTH >= 1000) {
    return `${(hashrateTH / 1000).toFixed(decimals || 1)} PH/s`;
  }
  
  return `${hashrateTH.toFixed(decimals)} TH/s`;
};

/**
 * Format power consumption
 * 
 * @param {number} watts - Power in watts
 * @param {number} [decimals=0] - Decimal places
 * @returns {string} Formatted power with unit
 * @example
 * formatPower(3500) // "3.5 kW"
 * formatPower(500) // "500 W"
 */
export const formatPower = (watts, decimals = 0) => {
  if (watts === null || watts === undefined || isNaN(watts)) {
    return '0 W';
  }
  
  if (watts >= 1000000) {
    return `${(watts / 1000000).toFixed(decimals || 2)} MW`;
  }
  
  if (watts >= 1000) {
    return `${(watts / 1000).toFixed(decimals || 1)} kW`;
  }
  
  return `${watts.toFixed(decimals)} W`;
};

/**
 * Format efficiency (J/TH)
 * 
 * @param {number} efficiency - Efficiency in J/TH (W/TH)
 * @param {number} [decimals=1] - Decimal places
 * @returns {string} Formatted efficiency
 * @example
 * formatEfficiency(15.5) // "15.5 J/TH"
 */
export const formatEfficiency = (efficiency, decimals = 1) => {
  if (efficiency === null || efficiency === undefined || isNaN(efficiency)) {
    return '0 J/TH';
  }
  
  return `${efficiency.toFixed(decimals)} J/TH`;
};

/**
 * Format a large number in compact form
 * 
 * @param {number} value - Number to format
 * @param {number} [decimals=1] - Decimal places
 * @returns {string} Compact formatted number
 * @example
 * formatCompact(1234567) // "1.2M"
 * formatCompact(1234) // "1.2K"
 */
export const formatCompact = (value, decimals = 1) => {
  if (value === null || value === undefined || isNaN(value)) {
    return '0';
  }
  
  const absValue = Math.abs(value);
  const sign = value < 0 ? '-' : '';
  
  if (absValue >= 1e12) {
    return `${sign}${(absValue / 1e12).toFixed(decimals)}T`;
  }
  if (absValue >= 1e9) {
    return `${sign}${(absValue / 1e9).toFixed(decimals)}B`;
  }
  if (absValue >= 1e6) {
    return `${sign}${(absValue / 1e6).toFixed(decimals)}M`;
  }
  if (absValue >= 1e3) {
    return `${sign}${(absValue / 1e3).toFixed(decimals)}K`;
  }
  
  return `${sign}${absValue.toFixed(decimals)}`;
};

/**
 * Format a ratio
 * 
 * @param {number} numerator - Top value
 * @param {number} denominator - Bottom value
 * @param {number} [decimals=2] - Decimal places
 * @returns {string} Formatted ratio
 * @example
 * formatRatio(3, 4) // "0.75"
 */
export const formatRatio = (numerator, denominator, decimals = 2) => {
  if (!denominator || denominator === 0) {
    return '0';
  }
  return (numerator / denominator).toFixed(decimals);
};

