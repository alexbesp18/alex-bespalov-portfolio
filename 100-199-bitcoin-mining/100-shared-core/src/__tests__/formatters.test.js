/**
 * Formatter Tests
 * @jest-environment node
 */

import {
  formatCurrency,
  formatBTC,
  formatElectricityRate,
} from '../formatters/currency.js';

import {
  formatNumber,
  formatPercentage,
  formatHashrate,
  formatPower,
  formatEfficiency,
  formatCompact,
} from '../formatters/numbers.js';

describe('Currency Formatters', () => {
  describe('formatCurrency', () => {
    it('formats positive numbers correctly', () => {
      expect(formatCurrency(1234)).toBe('$1,234');
    });
    
    it('formats negative numbers correctly', () => {
      expect(formatCurrency(-1234)).toBe('-$1,234');
    });
    
    it('handles decimal places', () => {
      expect(formatCurrency(1234.56, { decimals: 2 })).toBe('$1,234.56');
    });
    
    it('handles null/undefined', () => {
      expect(formatCurrency(null)).toBe('$0');
      expect(formatCurrency(undefined)).toBe('$0');
    });
    
    it('handles compact notation', () => {
      expect(formatCurrency(1500000, { compact: true })).toBe('$1.50M');
      expect(formatCurrency(1500, { compact: true })).toBe('$1.5K');
    });
    
    it('handles sign option', () => {
      expect(formatCurrency(1234, { showSign: true })).toBe('+$1,234');
    });
  });
  
  describe('formatBTC', () => {
    it('formats BTC with symbol', () => {
      expect(formatBTC(0.12345678)).toBe('₿0.1235');
    });
    
    it('formats BTC without symbol', () => {
      expect(formatBTC(0.12345678, 4, false)).toBe('0.1235');
    });
    
    it('handles custom decimals', () => {
      expect(formatBTC(0.12345678, 8)).toBe('₿0.12345678');
    });
  });
  
  describe('formatElectricityRate', () => {
    it('formats electricity rate correctly', () => {
      expect(formatElectricityRate(0.065)).toBe('$0.065');
    });
    
    it('handles null values', () => {
      expect(formatElectricityRate(null)).toBe('$0.000');
    });
  });
});

describe('Number Formatters', () => {
  describe('formatNumber', () => {
    it('formats with thousands separators', () => {
      expect(formatNumber(1234567)).toBe('1,234,567');
    });
    
    it('handles decimal places', () => {
      expect(formatNumber(1234.567, 2)).toBe('1,234.57');
    });
  });
  
  describe('formatPercentage', () => {
    it('formats percentage correctly', () => {
      expect(formatPercentage(45.6)).toBe('45.6%');
    });
    
    it('handles sign option', () => {
      expect(formatPercentage(45.6, 1, true)).toBe('+45.6%');
      expect(formatPercentage(-10.5, 1, true)).toBe('-10.5%');
    });
  });
  
  describe('formatHashrate', () => {
    it('formats TH/s correctly', () => {
      expect(formatHashrate(500)).toBe('500 TH/s');
    });
    
    it('converts to PH/s for large values', () => {
      expect(formatHashrate(1500)).toBe('1.5 PH/s');
    });
    
    it('converts to EH/s for very large values', () => {
      expect(formatHashrate(1500000)).toBe('1.50 EH/s');
    });
  });
  
  describe('formatPower', () => {
    it('formats watts correctly', () => {
      expect(formatPower(500)).toBe('500 W');
    });
    
    it('converts to kW for large values', () => {
      expect(formatPower(3500)).toBe('3.5 kW');
    });
    
    it('converts to MW for very large values', () => {
      expect(formatPower(1500000)).toBe('1.50 MW');
    });
  });
  
  describe('formatEfficiency', () => {
    it('formats efficiency correctly', () => {
      expect(formatEfficiency(15.5)).toBe('15.5 J/TH');
    });
  });
  
  describe('formatCompact', () => {
    it('formats millions correctly', () => {
      expect(formatCompact(1500000)).toBe('1.5M');
    });
    
    it('formats thousands correctly', () => {
      expect(formatCompact(1500)).toBe('1.5K');
    });
    
    it('handles negative numbers', () => {
      expect(formatCompact(-1500000)).toBe('-1.5M');
    });
  });
});

