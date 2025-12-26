/**
 * Tests for calculation utility functions
 * These functions are extracted from PortfolioAnalyzer for testing
 */

/**
 * Validates and clamps a number value within specified bounds
 * @param {string|number} value - The value to validate
 * @param {number} [min=0] - Minimum allowed value
 * @param {number} [max=Infinity] - Maximum allowed value
 * @returns {number} Validated number clamped between min and max
 */
const validateNumber = (value, min = 0, max = Infinity) => {
  const num = parseFloat(value);
  if (isNaN(num)) return min;
  return Math.max(min, Math.min(max, num));
};

/**
 * Calculates the number of months until an option expiry date
 * @param {string} expiryDate - ISO date string (YYYY-MM-DD)
 * @returns {number} Number of months until expiry (0 if expired or invalid)
 */
const getMonthsToExpiry = (expiryDate) => {
  try {
    const expiry = new Date(expiryDate);
    const now = new Date();
    if (isNaN(expiry.getTime())) return 0;
    return Math.max(0, (expiry - now) / (1000 * 60 * 60 * 24 * 30.42));
  } catch (error) {
    return 0;
  }
};

describe('validateNumber', () => {
  test('validates valid numbers', () => {
    expect(validateNumber('123')).toBe(123);
    expect(validateNumber(456)).toBe(456);
    expect(validateNumber('12.34')).toBe(12.34);
  });

  test('clamps values to minimum', () => {
    expect(validateNumber('-10', 0)).toBe(0);
    expect(validateNumber('abc', 5)).toBe(5);
    expect(validateNumber(NaN, 10)).toBe(10);
  });

  test('clamps values to maximum', () => {
    expect(validateNumber('200', 0, 100)).toBe(100);
    expect(validateNumber(150, 0, 100)).toBe(100);
  });

  test('handles edge cases', () => {
    expect(validateNumber('0', 0, 100)).toBe(0);
    expect(validateNumber('100', 0, 100)).toBe(100);
    expect(validateNumber('', 0, 100)).toBe(0);
  });
});

describe('getMonthsToExpiry', () => {
  test('calculates months correctly for future dates', () => {
    const futureDate = new Date();
    futureDate.setMonth(futureDate.getMonth() + 6);
    const expiryStr = futureDate.toISOString().split('T')[0];
    
    const months = getMonthsToExpiry(expiryStr);
    expect(months).toBeGreaterThan(5);
    expect(months).toBeLessThan(7);
  });

  test('returns 0 for past dates', () => {
    const pastDate = '2020-01-01';
    expect(getMonthsToExpiry(pastDate)).toBe(0);
  });

  test('handles invalid date strings', () => {
    expect(getMonthsToExpiry('invalid-date')).toBe(0);
    expect(getMonthsToExpiry('')).toBe(0);
    expect(getMonthsToExpiry('2023-13-45')).toBe(0);
  });

  test('handles valid ISO date format', () => {
    const date = '2025-12-31';
    const months = getMonthsToExpiry(date);
    expect(months).toBeGreaterThanOrEqual(0);
  });
});

