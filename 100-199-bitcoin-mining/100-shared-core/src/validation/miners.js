/**
 * Miner Validation Utilities
 * 
 * Functions for validating miner data structures.
 * 
 * @module validation/miners
 */

import { validateNumber, validatePositive, isPositiveNumber } from './numbers.js';

/**
 * @typedef {Object} MinerValidationResult
 * @property {boolean} isValid - Whether the miner data is valid
 * @property {string[]} errors - List of validation errors
 * @property {Object} sanitized - Sanitized miner data
 */

/**
 * Required fields for a valid miner
 */
const REQUIRED_FIELDS = ['hashrate', 'power'];

/**
 * Optional fields with defaults
 */
const OPTIONAL_FIELDS = {
  name: 'Custom Miner',
  fullName: 'Custom Miner',
  efficiency: null, // Calculated from power/hashrate
  defaultPrice: 0,
  manufacturer: 'Unknown',
  coolingType: 'Air',
  releaseYear: new Date().getFullYear(),
  series: 'Custom',
};

/**
 * Validate a miner object
 * 
 * @param {Object} miner - Miner object to validate
 * @param {Object} [options={}] - Validation options
 * @param {boolean} [options.requirePrice=false] - Whether price is required
 * @param {boolean} [options.sanitize=true] - Whether to return sanitized data
 * @returns {MinerValidationResult} Validation result
 */
export const validateMiner = (miner, options = {}) => {
  const { requirePrice = false, sanitize = true } = options;
  const errors = [];
  
  if (!miner || typeof miner !== 'object') {
    return {
      isValid: false,
      errors: ['Miner must be an object'],
      sanitized: null,
    };
  }
  
  // Check required fields
  if (!isPositiveNumber(miner.hashrate)) {
    errors.push('Hashrate must be a positive number');
  }
  
  if (!isPositiveNumber(miner.power)) {
    errors.push('Power must be a positive number');
  }
  
  if (requirePrice && !isPositiveNumber(miner.defaultPrice) && !isPositiveNumber(miner.price)) {
    errors.push('Price must be a positive number');
  }
  
  // Validate optional fields if present
  if (miner.efficiency !== undefined && miner.efficiency !== null) {
    if (!isPositiveNumber(miner.efficiency)) {
      errors.push('Efficiency must be a positive number if provided');
    }
  }
  
  if (miner.releaseYear !== undefined) {
    const year = parseInt(miner.releaseYear, 10);
    if (isNaN(year) || year < 2010 || year > 2030) {
      errors.push('Release year must be between 2010 and 2030');
    }
  }
  
  // Create sanitized version
  let sanitized = null;
  
  if (sanitize && errors.length === 0) {
    sanitized = sanitizeMiner(miner);
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    sanitized,
  };
};

/**
 * Sanitize miner data by ensuring all fields have valid values
 * 
 * @param {Object} miner - Miner data to sanitize
 * @returns {Object} Sanitized miner object
 */
export const sanitizeMiner = (miner) => {
  const hashrate = validatePositive(miner.hashrate, 100);
  const power = validatePositive(miner.power, 1500);
  
  const sanitized = {
    id: miner.id || generateMinerId(miner),
    name: String(miner.name || OPTIONAL_FIELDS.name).trim(),
    fullName: String(miner.fullName || miner.name || OPTIONAL_FIELDS.fullName).trim(),
    hashrate,
    power,
    efficiency: miner.efficiency !== undefined 
      ? validatePositive(miner.efficiency, power / hashrate)
      : Math.round((power / hashrate) * 10) / 10,
    defaultPrice: validatePositive(miner.defaultPrice || miner.price, OPTIONAL_FIELDS.defaultPrice),
    manufacturer: String(miner.manufacturer || OPTIONAL_FIELDS.manufacturer).trim(),
    coolingType: validateCoolingType(miner.coolingType),
    releaseYear: validateNumber(miner.releaseYear, 2010, 2030) || OPTIONAL_FIELDS.releaseYear,
    series: String(miner.series || OPTIONAL_FIELDS.series).trim(),
  };
  
  // Preserve any additional fields
  for (const [key, value] of Object.entries(miner)) {
    if (!(key in sanitized)) {
      sanitized[key] = value;
    }
  }
  
  return sanitized;
};

/**
 * Generate a unique miner ID from its properties
 * 
 * @param {Object} miner - Miner object
 * @returns {string} Generated ID
 */
export const generateMinerId = (miner) => {
  const name = miner.name || miner.fullName || 'CUSTOM';
  const baseId = name
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '');
  
  // Add a random suffix for uniqueness
  const suffix = Math.random().toString(36).substring(2, 6).toUpperCase();
  
  return `${baseId}_${suffix}`;
};

/**
 * Validate cooling type
 * 
 * @param {string} type - Cooling type to validate
 * @returns {string} Valid cooling type
 */
const VALID_COOLING_TYPES = ['Air', 'Hydro', 'Immersion', 'Unknown'];

export const validateCoolingType = (type) => {
  if (!type) return 'Air';
  
  const normalized = String(type).toLowerCase();
  
  if (normalized.includes('hydro')) return 'Hydro';
  if (normalized.includes('immersion')) return 'Immersion';
  if (normalized.includes('air')) return 'Air';
  
  // Check for exact match (case insensitive)
  const match = VALID_COOLING_TYPES.find(
    t => t.toLowerCase() === normalized
  );
  
  return match || 'Air';
};

/**
 * Validate an array of miners
 * 
 * @param {Array} miners - Array of miner objects
 * @param {Object} [options={}] - Validation options
 * @returns {Object} Validation result with valid miners and errors
 */
export const validateMiners = (miners, options = {}) => {
  if (!Array.isArray(miners)) {
    return {
      isValid: false,
      valid: [],
      invalid: [],
      errors: ['Input must be an array of miners'],
    };
  }
  
  const valid = [];
  const invalid = [];
  const errors = [];
  
  miners.forEach((miner, index) => {
    const result = validateMiner(miner, options);
    
    if (result.isValid) {
      valid.push(result.sanitized || miner);
    } else {
      invalid.push({ index, miner, errors: result.errors });
      errors.push(`Miner at index ${index}: ${result.errors.join(', ')}`);
    }
  });
  
  return {
    isValid: invalid.length === 0,
    valid,
    invalid,
    errors,
  };
};

/**
 * Check if two miners are the same (based on key properties)
 * 
 * @param {Object} miner1 - First miner
 * @param {Object} miner2 - Second miner
 * @returns {boolean} Whether miners are the same
 */
export const isSameMiner = (miner1, miner2) => {
  if (miner1.id && miner2.id && miner1.id === miner2.id) {
    return true;
  }
  
  return (
    miner1.name === miner2.name &&
    miner1.hashrate === miner2.hashrate &&
    miner1.power === miner2.power
  );
};

/**
 * Merge miner data with updates
 * 
 * @param {Object} existing - Existing miner data
 * @param {Object} updates - Updates to apply
 * @returns {Object} Merged miner
 */
export const mergeMinerData = (existing, updates) => {
  const merged = { ...existing };
  
  for (const [key, value] of Object.entries(updates)) {
    if (value !== undefined && value !== null) {
      merged[key] = value;
    }
  }
  
  // Recalculate efficiency if power or hashrate changed
  if (updates.power !== undefined || updates.hashrate !== undefined) {
    const hashrate = merged.hashrate || 1;
    const power = merged.power || 0;
    merged.efficiency = Math.round((power / hashrate) * 10) / 10;
  }
  
  return merged;
};

