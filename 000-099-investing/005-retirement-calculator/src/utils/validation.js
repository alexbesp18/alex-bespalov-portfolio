/**
 * Input validation utilities for retirement calculator
 * 
 * Provides validation functions and sanitization for user inputs
 * to ensure calculations remain stable and meaningful.
 */

import { INPUT_CONSTRAINTS } from '../config/constants';

/**
 * Validation result object
 * @typedef {Object} ValidationResult
 * @property {boolean} isValid - Whether the input is valid
 * @property {string|null} error - Error message if invalid
 * @property {number} value - Sanitized value (clamped to bounds)
 */

/**
 * Validate and sanitize an integer input
 * 
 * @param {string|number} input - Raw input value
 * @param {number} min - Minimum allowed value
 * @param {number} max - Maximum allowed value
 * @param {string} fieldName - Name of the field for error messages
 * @returns {ValidationResult} Validation result with sanitized value
 */
export const validateInteger = (input, min, max, fieldName) => {
  const parsed = parseInt(input, 10);
  
  if (isNaN(parsed)) {
    return {
      isValid: false,
      error: `${fieldName} must be a valid number`,
      value: min,
    };
  }
  
  if (parsed < min) {
    return {
      isValid: false,
      error: `${fieldName} must be at least ${min}`,
      value: min,
    };
  }
  
  if (parsed > max) {
    return {
      isValid: false,
      error: `${fieldName} must be at most ${max}`,
      value: max,
    };
  }
  
  return {
    isValid: true,
    error: null,
    value: parsed,
  };
};

/**
 * Validate and sanitize a float input
 * 
 * @param {string|number} input - Raw input value
 * @param {number} min - Minimum allowed value
 * @param {number} max - Maximum allowed value
 * @param {string} fieldName - Name of the field for error messages
 * @returns {ValidationResult} Validation result with sanitized value
 */
export const validateFloat = (input, min, max, fieldName) => {
  const parsed = parseFloat(input);
  
  if (isNaN(parsed)) {
    return {
      isValid: false,
      error: `${fieldName} must be a valid number`,
      value: min,
    };
  }
  
  if (parsed < min) {
    return {
      isValid: false,
      error: `${fieldName} must be at least ${min}`,
      value: min,
    };
  }
  
  if (parsed > max) {
    return {
      isValid: false,
      error: `${fieldName} must be at most ${max}`,
      value: max,
    };
  }
  
  return {
    isValid: true,
    error: null,
    value: parsed,
  };
};

/**
 * Validate age inputs for logical consistency
 * 
 * @param {number} currentAge - Current age
 * @param {number} retirementAge - Retirement age
 * @param {number} endAge - Life expectancy age
 * @returns {Object} Validation results for all age fields
 */
export const validateAges = (currentAge, retirementAge, endAge) => {
  const errors = {};
  
  if (currentAge >= retirementAge) {
    errors.retirementAge = 'Retirement age must be greater than current age';
  }
  
  if (retirementAge >= endAge) {
    errors.endAge = 'Life expectancy must be greater than retirement age';
  }
  
  if (currentAge < INPUT_CONSTRAINTS.minAge) {
    errors.currentAge = `Current age must be at least ${INPUT_CONSTRAINTS.minAge}`;
  }
  
  if (endAge > INPUT_CONSTRAINTS.maxLifeExpectancy) {
    errors.endAge = `Life expectancy cannot exceed ${INPUT_CONSTRAINTS.maxLifeExpectancy}`;
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
};

/**
 * Validate financial inputs
 * 
 * @param {number} desiredIncome - Desired annual income
 * @param {number} initialInvestment - Initial investment amount
 * @param {number} annualContribution - Annual contribution
 * @param {number} expectedReturn - Expected return rate
 * @returns {Object} Validation results
 */
export const validateFinancialInputs = (
  desiredIncome,
  initialInvestment,
  annualContribution,
  expectedReturn
) => {
  const errors = {};
  
  if (desiredIncome < 0) {
    errors.desiredIncome = 'Desired income cannot be negative';
  }
  
  if (initialInvestment < 0) {
    errors.initialInvestment = 'Initial investment cannot be negative';
  }
  
  if (annualContribution < 0) {
    errors.annualContribution = 'Annual contribution cannot be negative';
  }
  
  if (expectedReturn < 0) {
    errors.expectedReturn = 'Expected return cannot be negative';
  }
  
  if (expectedReturn > INPUT_CONSTRAINTS.maxReturn) {
    errors.expectedReturn = `Expected return cannot exceed ${INPUT_CONSTRAINTS.maxReturn}%`;
  }
  
  // Warn if no investment at all
  if (initialInvestment === 0 && annualContribution === 0) {
    errors.investment = 'Either initial investment or annual contribution should be greater than 0';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
};

/**
 * Clamp a value between min and max bounds
 * 
 * @param {number} value - Value to clamp
 * @param {number} min - Minimum bound
 * @param {number} max - Maximum bound
 * @returns {number} Clamped value
 */
export const clamp = (value, min, max) => {
  return Math.min(Math.max(value, min), max);
};

/**
 * Safely parse an integer with fallback
 * 
 * @param {string|number} value - Value to parse
 * @param {number} fallback - Fallback value if parsing fails
 * @returns {number} Parsed integer or fallback
 */
export const safeParseInt = (value, fallback = 0) => {
  const parsed = parseInt(value, 10);
  return isNaN(parsed) ? fallback : parsed;
};

/**
 * Safely parse a float with fallback
 * 
 * @param {string|number} value - Value to parse
 * @param {number} fallback - Fallback value if parsing fails
 * @returns {number} Parsed float or fallback
 */
export const safeParseFloat = (value, fallback = 0) => {
  const parsed = parseFloat(value);
  return isNaN(parsed) ? fallback : parsed;
};

