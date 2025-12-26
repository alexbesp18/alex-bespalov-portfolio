/**
 * Formatting utility functions
 */

/**
 * Format number as currency
 * @param {number} value - Value to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} - Formatted currency string
 */
export const formatCurrency = (value, decimals = 0) => {
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
};

/**
 * Format number with commas
 * @param {number} value - Value to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} - Formatted number string
 */
export const formatNumber = (value, decimals = 0) => {
  return value.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
};

/**
 * Format percentage
 * @param {number} value - Value to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} - Formatted percentage string
 */
export const formatPercentage = (value, decimals = 1) => {
  return `${value.toFixed(decimals)}%`;
};

/**
 * Format electricity rate
 * @param {number} rate - Rate in $/kWh
 * @returns {string} - Formatted rate string
 */
export const formatElectricityRate = (rate) => {
  return `$${rate.toFixed(3)}`;
};
