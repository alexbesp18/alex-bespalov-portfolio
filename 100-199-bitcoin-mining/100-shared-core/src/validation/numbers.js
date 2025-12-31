/**
 * Number Validation Utilities
 * 
 * Functions for validating and clamping numeric values.
 * 
 * @module validation/numbers
 */

/**
 * Validate and clamp a number within specified bounds
 * 
 * @param {*} value - Value to validate
 * @param {number} [min=0] - Minimum allowed value
 * @param {number} [max=Infinity] - Maximum allowed value
 * @returns {number} Validated number clamped between min and max
 * @example
 * validateNumber('123', 0, 100) // Returns 100
 * validateNumber('abc', 0, 100) // Returns 0 (min)
 * validateNumber(-5, 0, 100) // Returns 0 (clamped to min)
 */
export const validateNumber = (value, min = 0, max = Infinity) => {
  const num = parseFloat(value);
  
  if (isNaN(num)) {
    return min;
  }
  
  return Math.max(min, Math.min(max, num));
};

/**
 * Validate a positive number
 * 
 * @param {*} value - Value to validate
 * @param {number} [defaultValue=0] - Default if invalid
 * @returns {number} Positive number or default
 */
export const validatePositive = (value, defaultValue = 0) => {
  const num = parseFloat(value);
  
  if (isNaN(num) || num < 0) {
    return defaultValue;
  }
  
  return num;
};

/**
 * Validate a percentage (0-100)
 * 
 * @param {*} value - Value to validate
 * @param {number} [defaultValue=0] - Default if invalid
 * @returns {number} Percentage between 0-100
 */
export const validatePercentage = (value, defaultValue = 0) => {
  return validateNumber(value, 0, 100) || defaultValue;
};

/**
 * Validate an integer
 * 
 * @param {*} value - Value to validate
 * @param {number} [min=-Infinity] - Minimum value
 * @param {number} [max=Infinity] - Maximum value
 * @returns {number} Validated integer
 */
export const validateInteger = (value, min = -Infinity, max = Infinity) => {
  const num = parseInt(value, 10);
  
  if (isNaN(num)) {
    return Math.max(min, 0);
  }
  
  return Math.max(min, Math.min(max, num));
};

/**
 * Check if a value is a valid number
 * 
 * @param {*} value - Value to check
 * @returns {boolean} Whether value is a valid number
 */
export const isValidNumber = (value) => {
  if (value === null || value === undefined || value === '') {
    return false;
  }
  
  const num = Number(value);
  return !isNaN(num) && isFinite(num);
};

/**
 * Check if a value is a positive number
 * 
 * @param {*} value - Value to check
 * @returns {boolean} Whether value is a positive number
 */
export const isPositiveNumber = (value) => {
  return isValidNumber(value) && Number(value) > 0;
};

/**
 * Round to specified decimal places
 * 
 * @param {number} value - Value to round
 * @param {number} [decimals=2] - Number of decimal places
 * @returns {number} Rounded value
 */
export const roundTo = (value, decimals = 2) => {
  if (!isValidNumber(value)) return 0;
  
  const multiplier = Math.pow(10, decimals);
  return Math.round(value * multiplier) / multiplier;
};

/**
 * Clamp a value between min and max
 * 
 * @param {number} value - Value to clamp
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {number} Clamped value
 */
export const clamp = (value, min, max) => {
  return Math.max(min, Math.min(max, value));
};

/**
 * Linear interpolation between two values
 * 
 * @param {number} start - Start value
 * @param {number} end - End value
 * @param {number} t - Interpolation factor (0-1)
 * @returns {number} Interpolated value
 */
export const lerp = (start, end, t) => {
  return start + (end - start) * clamp(t, 0, 1);
};

/**
 * Calculate percentage change between two values
 * 
 * @param {number} oldValue - Original value
 * @param {number} newValue - New value
 * @returns {number} Percentage change
 */
export const percentChange = (oldValue, newValue) => {
  if (!oldValue || oldValue === 0) return 0;
  return ((newValue - oldValue) / oldValue) * 100;
};

/**
 * Safe division that returns 0 for divide-by-zero
 * 
 * @param {number} numerator - Numerator
 * @param {number} denominator - Denominator
 * @param {number} [fallback=0] - Fallback value for divide by zero
 * @returns {number} Division result or fallback
 */
export const safeDivide = (numerator, denominator, fallback = 0) => {
  if (!denominator || denominator === 0) return fallback;
  return numerator / denominator;
};

/**
 * Parse a number from various formats
 * Handles strings with commas, currency symbols, etc.
 * 
 * @param {string|number} value - Value to parse
 * @param {number} [fallback=0] - Fallback for unparseable values
 * @returns {number} Parsed number
 * @example
 * parseNumeric('$1,234.56') // 1234.56
 * parseNumeric('1.5K') // 1500
 */
export const parseNumeric = (value, fallback = 0) => {
  if (typeof value === 'number') return value;
  if (!value || typeof value !== 'string') return fallback;
  
  // Remove currency symbols and commas
  let cleaned = value.replace(/[$,€£¥]/g, '').trim();
  
  // Handle K, M, B suffixes
  const multipliers = { K: 1e3, M: 1e6, B: 1e9, T: 1e12 };
  const lastChar = cleaned.slice(-1).toUpperCase();
  
  if (multipliers[lastChar]) {
    cleaned = cleaned.slice(0, -1);
    const num = parseFloat(cleaned);
    return isNaN(num) ? fallback : num * multipliers[lastChar];
  }
  
  const num = parseFloat(cleaned);
  return isNaN(num) ? fallback : num;
};

