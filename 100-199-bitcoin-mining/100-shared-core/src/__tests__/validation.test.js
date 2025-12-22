/**
 * Validation Tests
 * @jest-environment node
 */

import {
  validateNumber,
  validatePositive,
  validatePercentage,
  validateInteger,
  isValidNumber,
  isPositiveNumber,
  roundTo,
  clamp,
  percentChange,
  safeDivide,
  parseNumeric,
} from '../validation/numbers.js';

import {
  validateMiner,
  sanitizeMiner,
  validateMiners,
  isSameMiner,
} from '../validation/miners.js';

describe('Number Validation', () => {
  describe('validateNumber', () => {
    it('clamps to min', () => {
      expect(validateNumber(-10, 0, 100)).toBe(0);
    });
    
    it('clamps to max', () => {
      expect(validateNumber(150, 0, 100)).toBe(100);
    });
    
    it('parses string numbers', () => {
      expect(validateNumber('50', 0, 100)).toBe(50);
    });
    
    it('returns min for NaN', () => {
      expect(validateNumber('abc', 0, 100)).toBe(0);
    });
  });
  
  describe('validatePositive', () => {
    it('returns default for negative', () => {
      expect(validatePositive(-10, 0)).toBe(0);
    });
    
    it('returns value for positive', () => {
      expect(validatePositive(50, 0)).toBe(50);
    });
  });
  
  describe('validatePercentage', () => {
    it('clamps to 0-100', () => {
      expect(validatePercentage(150)).toBe(100);
      expect(validatePercentage(-10)).toBe(0);
    });
  });
  
  describe('validateInteger', () => {
    it('rounds to integer', () => {
      expect(validateInteger(5.7)).toBe(5);
    });
    
    it('clamps to range', () => {
      expect(validateInteger(150, 0, 100)).toBe(100);
    });
  });
  
  describe('isValidNumber', () => {
    it('returns true for valid numbers', () => {
      expect(isValidNumber(42)).toBe(true);
      expect(isValidNumber('42')).toBe(true);
      expect(isValidNumber(0)).toBe(true);
    });
    
    it('returns false for invalid values', () => {
      expect(isValidNumber(null)).toBe(false);
      expect(isValidNumber(undefined)).toBe(false);
      expect(isValidNumber('')).toBe(false);
      expect(isValidNumber('abc')).toBe(false);
      expect(isValidNumber(NaN)).toBe(false);
    });
  });
  
  describe('isPositiveNumber', () => {
    it('returns true for positive numbers', () => {
      expect(isPositiveNumber(42)).toBe(true);
      expect(isPositiveNumber(0.5)).toBe(true);
    });
    
    it('returns false for zero and negative', () => {
      expect(isPositiveNumber(0)).toBe(false);
      expect(isPositiveNumber(-5)).toBe(false);
    });
  });
  
  describe('roundTo', () => {
    it('rounds to specified decimals', () => {
      expect(roundTo(1.23456, 2)).toBe(1.23);
      expect(roundTo(1.23456, 3)).toBe(1.235);
    });
  });
  
  describe('clamp', () => {
    it('clamps value to range', () => {
      expect(clamp(5, 0, 10)).toBe(5);
      expect(clamp(-5, 0, 10)).toBe(0);
      expect(clamp(15, 0, 10)).toBe(10);
    });
  });
  
  describe('percentChange', () => {
    it('calculates percent change correctly', () => {
      expect(percentChange(100, 150)).toBe(50);
      expect(percentChange(100, 50)).toBe(-50);
    });
    
    it('returns 0 for zero old value', () => {
      expect(percentChange(0, 100)).toBe(0);
    });
  });
  
  describe('safeDivide', () => {
    it('divides normally for non-zero denominator', () => {
      expect(safeDivide(10, 2)).toBe(5);
    });
    
    it('returns fallback for zero denominator', () => {
      expect(safeDivide(10, 0)).toBe(0);
      expect(safeDivide(10, 0, -1)).toBe(-1);
    });
  });
  
  describe('parseNumeric', () => {
    it('parses regular numbers', () => {
      expect(parseNumeric(42)).toBe(42);
      expect(parseNumeric('42')).toBe(42);
    });
    
    it('parses currency strings', () => {
      expect(parseNumeric('$1,234.56')).toBe(1234.56);
    });
    
    it('parses compact notation', () => {
      expect(parseNumeric('1.5K')).toBe(1500);
      expect(parseNumeric('2M')).toBe(2000000);
    });
  });
});

describe('Miner Validation', () => {
  describe('validateMiner', () => {
    it('validates a valid miner', () => {
      const miner = {
        name: 'S21 XP',
        hashrate: 270,
        power: 3645,
      };
      
      const result = validateMiner(miner);
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
    
    it('rejects miner without hashrate', () => {
      const miner = {
        name: 'S21 XP',
        power: 3645,
      };
      
      const result = validateMiner(miner);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Hashrate must be a positive number');
    });
    
    it('rejects miner without power', () => {
      const miner = {
        name: 'S21 XP',
        hashrate: 270,
      };
      
      const result = validateMiner(miner);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Power must be a positive number');
    });
  });
  
  describe('sanitizeMiner', () => {
    it('adds default values for missing fields', () => {
      const miner = {
        hashrate: 270,
        power: 3645,
      };
      
      const sanitized = sanitizeMiner(miner);
      expect(sanitized.name).toBe('Custom Miner');
      expect(sanitized.manufacturer).toBe('Unknown');
      expect(sanitized.coolingType).toBe('Air');
    });
    
    it('calculates efficiency if not provided', () => {
      const miner = {
        hashrate: 270,
        power: 3645,
      };
      
      const sanitized = sanitizeMiner(miner);
      expect(sanitized.efficiency).toBeCloseTo(13.5, 1);
    });
    
    it('generates ID if not provided', () => {
      const miner = {
        name: 'Test Miner',
        hashrate: 270,
        power: 3645,
      };
      
      const sanitized = sanitizeMiner(miner);
      expect(sanitized.id).toBeDefined();
      expect(sanitized.id).toContain('TEST_MINER');
    });
  });
  
  describe('validateMiners', () => {
    it('validates array of miners', () => {
      const miners = [
        { name: 'Miner 1', hashrate: 270, power: 3645 },
        { name: 'Miner 2', hashrate: 500, power: 5500 },
      ];
      
      const result = validateMiners(miners);
      expect(result.isValid).toBe(true);
      expect(result.valid).toHaveLength(2);
      expect(result.invalid).toHaveLength(0);
    });
    
    it('separates valid and invalid miners', () => {
      const miners = [
        { name: 'Valid', hashrate: 270, power: 3645 },
        { name: 'Invalid', hashrate: -100, power: 3645 },
      ];
      
      const result = validateMiners(miners);
      expect(result.isValid).toBe(false);
      expect(result.valid).toHaveLength(1);
      expect(result.invalid).toHaveLength(1);
    });
  });
  
  describe('isSameMiner', () => {
    it('matches by ID', () => {
      const miner1 = { id: 'S21_XP', name: 'S21 XP', hashrate: 270, power: 3645 };
      const miner2 = { id: 'S21_XP', name: 'Different Name', hashrate: 300, power: 4000 };
      
      expect(isSameMiner(miner1, miner2)).toBe(true);
    });
    
    it('matches by name and specs when no ID', () => {
      const miner1 = { name: 'S21 XP', hashrate: 270, power: 3645 };
      const miner2 = { name: 'S21 XP', hashrate: 270, power: 3645 };
      
      expect(isSameMiner(miner1, miner2)).toBe(true);
    });
    
    it('does not match different miners', () => {
      const miner1 = { name: 'S21 XP', hashrate: 270, power: 3645 };
      const miner2 = { name: 'S21 Pro', hashrate: 234, power: 3510 };
      
      expect(isSameMiner(miner1, miner2)).toBe(false);
    });
  });
});

