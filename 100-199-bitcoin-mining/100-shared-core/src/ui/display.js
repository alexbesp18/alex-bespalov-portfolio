/**
 * Display Utilities for Mining Calculators
 *
 * UI-specific helper functions for displaying mining calculation results.
 * These functions contain presentation logic (CSS classes, formatting for display)
 * and should not be used in business logic calculations.
 *
 * @module ui/display
 */

/**
 * Get cell color class based on value and metric
 *
 * @param {number} value - The value to color-code
 * @param {string} metric - The metric type ('roi', 'profit', etc.)
 * @returns {string} Tailwind CSS class name
 */
export const getCellColor = (value, metric) => {
  if (metric === 'roi') {
    if (value > 50) return 'bg-green-300';
    if (value > 25) return 'bg-green-200';
    if (value > 10) return 'bg-green-100';
    if (value > 0) return 'bg-green-50';
    if (value > -25) return 'bg-red-50';
    if (value > -50) return 'bg-red-100';
    return 'bg-red-200';
  } else {
    if (value > 20000) return 'bg-green-300';
    if (value > 10000) return 'bg-green-200';
    if (value > 5000) return 'bg-green-100';
    if (value > 0) return 'bg-green-50';
    if (value > -5000) return 'bg-red-50';
    if (value > -10000) return 'bg-red-100';
    return 'bg-red-200';
  }
};

/**
 * Get display value based on metric type
 *
 * @param {Object} result - Result object with various profit metrics
 * @param {string} metric - Metric to display
 * @param {boolean} [isTwoYear=false] - Whether this is a 2-year result
 * @returns {number} The value to display
 */
export const getDisplayValue = (result, metric, isTwoYear = false) => {
  switch (metric) {
    case 'operationalProfit':
      return result.operationalProfit || 0;
    case 'afterTaxProfit':
      return result.afterTaxProfit || 0;
    case 'roi':
      return isTwoYear ? (result.annualizedRoi || 0) : (result.roi || 0);
    case 'netProfit':
    default:
      return result.netProfit || 0;
  }
};

/**
 * Get risk level color class
 *
 * @param {string} riskLevel - Risk level ('Low', 'Medium', 'High')
 * @returns {string} Tailwind CSS class for risk level
 */
export const getRiskLevelColor = (riskLevel) => {
  switch (riskLevel) {
    case 'High':
      return 'text-red-600 bg-red-50';
    case 'Medium':
      return 'text-yellow-600 bg-yellow-50';
    case 'Low':
      return 'text-green-600 bg-green-50';
    default:
      return 'text-gray-600 bg-gray-50';
  }
};

/**
 * Get profit status indicator
 *
 * @param {number} profit - Profit value
 * @returns {Object} Object with status, color class, and icon suggestion
 */
export const getProfitStatus = (profit) => {
  if (profit > 0) {
    return {
      status: 'profitable',
      colorClass: 'text-green-600',
      bgClass: 'bg-green-50',
      icon: 'trending-up'
    };
  } else if (profit < 0) {
    return {
      status: 'loss',
      colorClass: 'text-red-600',
      bgClass: 'bg-red-50',
      icon: 'trending-down'
    };
  }
  return {
    status: 'breakeven',
    colorClass: 'text-gray-600',
    bgClass: 'bg-gray-50',
    icon: 'minus'
  };
};
