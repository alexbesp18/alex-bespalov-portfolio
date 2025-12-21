/**
 * Tests for validation utilities
 */

import {
  validateInteger,
  validateFloat,
  validateAges,
  validateFinancialInputs,
  clamp,
  safeParseInt,
  safeParseFloat,
} from '../validation';

describe('validateInteger', () => {
  it('should validate valid integers', () => {
    const result = validateInteger(25, 18, 100, 'Age');
    expect(result.isValid).toBe(true);
    expect(result.value).toBe(25);
    expect(result.error).toBeNull();
  });

  it('should reject non-numeric strings', () => {
    const result = validateInteger('abc', 0, 100, 'Value');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('valid number');
  });

  it('should reject values below minimum', () => {
    const result = validateInteger(10, 18, 100, 'Age');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('at least 18');
    expect(result.value).toBe(18);
  });

  it('should reject values above maximum', () => {
    const result = validateInteger(150, 18, 100, 'Age');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('at most 100');
    expect(result.value).toBe(100);
  });

  it('should handle string numbers', () => {
    const result = validateInteger('50', 0, 100, 'Value');
    expect(result.isValid).toBe(true);
    expect(result.value).toBe(50);
  });
});

describe('validateFloat', () => {
  it('should validate valid floats', () => {
    const result = validateFloat(2.7, 0, 20, 'Rate');
    expect(result.isValid).toBe(true);
    expect(result.value).toBe(2.7);
  });

  it('should reject NaN', () => {
    const result = validateFloat(NaN, 0, 100, 'Value');
    expect(result.isValid).toBe(false);
  });

  it('should handle string floats', () => {
    const result = validateFloat('9.6', 0, 100, 'Rate');
    expect(result.isValid).toBe(true);
    expect(result.value).toBeCloseTo(9.6);
  });
});

describe('validateAges', () => {
  it('should validate correct age progression', () => {
    const result = validateAges(30, 50, 90);
    expect(result.isValid).toBe(true);
    expect(Object.keys(result.errors)).toHaveLength(0);
  });

  it('should reject retirement age <= current age', () => {
    const result = validateAges(50, 45, 90);
    expect(result.isValid).toBe(false);
    expect(result.errors.retirementAge).toBeDefined();
  });

  it('should reject end age <= retirement age', () => {
    const result = validateAges(30, 60, 55);
    expect(result.isValid).toBe(false);
    expect(result.errors.endAge).toBeDefined();
  });

  it('should reject current age below minimum', () => {
    const result = validateAges(15, 50, 90);
    expect(result.isValid).toBe(false);
    expect(result.errors.currentAge).toBeDefined();
  });
});

describe('validateFinancialInputs', () => {
  it('should validate correct financial inputs', () => {
    const result = validateFinancialInputs(100000, 50000, 10000, 9.6);
    expect(result.isValid).toBe(true);
  });

  it('should reject negative desired income', () => {
    const result = validateFinancialInputs(-100000, 50000, 10000, 9.6);
    expect(result.isValid).toBe(false);
    expect(result.errors.desiredIncome).toBeDefined();
  });

  it('should reject negative expected return', () => {
    const result = validateFinancialInputs(100000, 50000, 10000, -5);
    expect(result.isValid).toBe(false);
    expect(result.errors.expectedReturn).toBeDefined();
  });

  it('should warn when both investment and contribution are zero', () => {
    const result = validateFinancialInputs(100000, 0, 0, 9.6);
    expect(result.isValid).toBe(false);
    expect(result.errors.investment).toBeDefined();
  });

  it('should accept zero contribution with positive investment', () => {
    const result = validateFinancialInputs(100000, 50000, 0, 9.6);
    expect(result.isValid).toBe(true);
  });
});

describe('clamp', () => {
  it('should return value within bounds unchanged', () => {
    expect(clamp(50, 0, 100)).toBe(50);
  });

  it('should clamp to minimum', () => {
    expect(clamp(-10, 0, 100)).toBe(0);
  });

  it('should clamp to maximum', () => {
    expect(clamp(150, 0, 100)).toBe(100);
  });
});

describe('safeParseInt', () => {
  it('should parse valid integers', () => {
    expect(safeParseInt('42')).toBe(42);
    expect(safeParseInt(42)).toBe(42);
  });

  it('should return fallback for invalid input', () => {
    expect(safeParseInt('abc', 0)).toBe(0);
    expect(safeParseInt('abc', 10)).toBe(10);
  });

  it('should truncate floats', () => {
    expect(safeParseInt('42.9')).toBe(42);
  });
});

describe('safeParseFloat', () => {
  it('should parse valid floats', () => {
    expect(safeParseFloat('9.6')).toBeCloseTo(9.6);
    expect(safeParseFloat(9.6)).toBeCloseTo(9.6);
  });

  it('should return fallback for invalid input', () => {
    expect(safeParseFloat('abc', 0)).toBe(0);
    expect(safeParseFloat('abc', 5.5)).toBe(5.5);
  });
});

