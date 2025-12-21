/**
 * Tests for formatting utilities
 */

import {
  formatCurrency,
  formatPercent,
  formatCompactCurrency,
  formatNumber,
} from '../formatters';

describe('formatCurrency', () => {
  it('should format positive numbers as USD currency', () => {
    expect(formatCurrency(1000)).toBe('$1,000');
    expect(formatCurrency(1000000)).toBe('$1,000,000');
  });

  it('should format zero as $0', () => {
    expect(formatCurrency(0)).toBe('$0');
  });

  it('should format negative numbers correctly', () => {
    expect(formatCurrency(-1000)).toBe('-$1,000');
  });

  it('should round decimal values to whole numbers', () => {
    expect(formatCurrency(1234.56)).toBe('$1,235');
    expect(formatCurrency(1234.49)).toBe('$1,234');
  });

  it('should handle large numbers', () => {
    expect(formatCurrency(123456789)).toBe('$123,456,789');
  });
});

describe('formatPercent', () => {
  it('should format numbers as percentages with 2 decimal places', () => {
    expect(formatPercent(9.6)).toBe('9.60%');
    expect(formatPercent(10)).toBe('10.00%');
  });

  it('should handle zero', () => {
    expect(formatPercent(0)).toBe('0.00%');
  });

  it('should round to 2 decimal places', () => {
    expect(formatPercent(9.567)).toBe('9.57%');
    expect(formatPercent(9.564)).toBe('9.56%');
  });

  it('should handle negative percentages', () => {
    expect(formatPercent(-5.5)).toBe('-5.50%');
  });
});

describe('formatCompactCurrency', () => {
  it('should format billions with B suffix', () => {
    expect(formatCompactCurrency(1500000000)).toBe('$1.5B');
    expect(formatCompactCurrency(2000000000)).toBe('$2.0B');
  });

  it('should format millions with M suffix', () => {
    expect(formatCompactCurrency(1500000)).toBe('$1.5M');
    expect(formatCompactCurrency(2000000)).toBe('$2.0M');
  });

  it('should format thousands with K suffix', () => {
    expect(formatCompactCurrency(1500)).toBe('$2K');
    expect(formatCompactCurrency(50000)).toBe('$50K');
  });

  it('should format small numbers as regular currency', () => {
    expect(formatCompactCurrency(500)).toBe('$500');
    expect(formatCompactCurrency(999)).toBe('$999');
  });

  it('should handle negative values', () => {
    expect(formatCompactCurrency(-1500000)).toBe('-$1.5M');
  });
});

describe('formatNumber', () => {
  it('should format numbers with thousand separators', () => {
    expect(formatNumber(1000)).toBe('1,000');
    expect(formatNumber(1000000)).toBe('1,000,000');
  });

  it('should handle zero', () => {
    expect(formatNumber(0)).toBe('0');
  });

  it('should handle negative numbers', () => {
    expect(formatNumber(-1000)).toBe('-1,000');
  });

  it('should preserve decimal places', () => {
    expect(formatNumber(1234.56)).toBe('1,234.56');
  });
});

