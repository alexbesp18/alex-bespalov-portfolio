/**
 * Formatting utilities for currency and percentage display
 */

import { DISPLAY_CONFIG } from '../config/constants';

/**
 * Format a number as US currency
 * 
 * @param {number} value - The number to format
 * @returns {string} Formatted currency string (e.g., "$100,000")
 * 
 * @example
 * formatCurrency(1234567.89) // Returns "$1,234,568"
 */
export const formatCurrency = (value) => {
  return new Intl.NumberFormat(DISPLAY_CONFIG.locale, {
    style: 'currency',
    currency: DISPLAY_CONFIG.currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

/**
 * Format a number as a percentage
 * 
 * @param {number} value - The percentage value (e.g., 9.6 for 9.6%)
 * @returns {string} Formatted percentage string (e.g., "9.60%")
 * 
 * @example
 * formatPercent(9.567) // Returns "9.57%"
 */
export const formatPercent = (value) => {
  return `${value.toFixed(DISPLAY_CONFIG.percentDecimals)}%`;
};

/**
 * Format a large number with abbreviated suffix
 * 
 * @param {number} value - The number to format
 * @returns {string} Abbreviated number (e.g., "$1.5M")
 * 
 * @example
 * formatCompactCurrency(1500000) // Returns "$1.5M"
 */
export const formatCompactCurrency = (value) => {
  const absValue = Math.abs(value);
  const sign = value < 0 ? '-' : '';

  if (absValue >= 1000000000) {
    return `${sign}$${(absValue / 1000000000).toFixed(1)}B`;
  }
  if (absValue >= 1000000) {
    return `${sign}$${(absValue / 1000000).toFixed(1)}M`;
  }
  if (absValue >= 1000) {
    return `${sign}$${(absValue / 1000).toFixed(0)}K`;
  }
  return formatCurrency(value);
};

/**
 * Format a number with thousand separators
 * 
 * @param {number} value - The number to format
 * @returns {string} Formatted number (e.g., "1,234,567")
 * 
 * @example
 * formatNumber(1234567) // Returns "1,234,567"
 */
export const formatNumber = (value) => {
  return new Intl.NumberFormat(DISPLAY_CONFIG.locale).format(value);
};

