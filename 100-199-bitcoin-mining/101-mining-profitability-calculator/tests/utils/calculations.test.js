/**
 * Tests for calculation utilities
 */

import {
  getCalculatedEndValues,
  calculateYearlyProfit,
  calculateTwoYearProfit,
  getCellColor,
  getDisplayValue,
  calculateQuickInsights,
  calculateMonthlyGrowth,
  calculateAnnualIncreases
} from '../../src/utils/calculations';
import { DEFAULT_PARAMS, DEFAULT_PRESET_MINERS, ELECTRICITY_RATES } from '../../src/utils/constants';

describe('calculations', () => {
  describe('getCalculatedEndValues', () => {
    it('should return direct end values when useAnnualIncreases is false', () => {
      const params = { ...DEFAULT_PARAMS, useAnnualIncreases: false };
      const result = getCalculatedEndValues(params);
      
      expect(result.btcPriceEnd).toBe(params.btcPriceEnd);
      expect(result.networkHashrateEnd).toBe(params.networkHashrateEnd);
    });

    it('should calculate end values from annual increases when useAnnualIncreases is true', () => {
      const params = {
        ...DEFAULT_PARAMS,
        useAnnualIncreases: true,
        btcPriceStart: 100000,
        annualBtcPriceIncrease: 50,
        networkHashrateStart: 900,
        annualDifficultyIncrease: 20
      };
      const result = getCalculatedEndValues(params);
      
      expect(result.btcPriceEnd).toBe(150000); // 100000 * 1.5
      expect(result.networkHashrateEnd).toBe(1080); // 900 * 1.2
    });
  });

  describe('calculateYearlyProfit', () => {
    it('should calculate profit for a miner', () => {
      const miner = DEFAULT_PRESET_MINERS[0];
      const electricityRate = 0.06;
      const params = DEFAULT_PARAMS;
      const minerPrices = { [miner.id]: miner.defaultPrice };

      const result = calculateYearlyProfit(miner, electricityRate, params, minerPrices);

      expect(result).toHaveProperty('netProfit');
      expect(result).toHaveProperty('roi');
      expect(result).toHaveProperty('totalBtcMined');
      expect(result).toHaveProperty('afterTaxProfit');
      expect(result.minerPrice).toBe(miner.defaultPrice);
    });
  });

  describe('getCellColor', () => {
    it('should return appropriate color for ROI metric', () => {
      expect(getCellColor(60, 'roi')).toBe('bg-green-300');
      expect(getCellColor(30, 'roi')).toBe('bg-green-200');
      expect(getCellColor(15, 'roi')).toBe('bg-green-100');
      expect(getCellColor(5, 'roi')).toBe('bg-green-50');
      expect(getCellColor(-10, 'roi')).toBe('bg-red-50');
      expect(getCellColor(-30, 'roi')).toBe('bg-red-100');
    });

    it('should return appropriate color for profit metric', () => {
      expect(getCellColor(25000, 'netProfit')).toBe('bg-green-300');
      expect(getCellColor(15000, 'netProfit')).toBe('bg-green-200');
      expect(getCellColor(7500, 'netProfit')).toBe('bg-green-100');
      expect(getCellColor(1000, 'netProfit')).toBe('bg-green-50');
      expect(getCellColor(-2000, 'netProfit')).toBe('bg-red-50');
    });
  });

  describe('getDisplayValue', () => {
    it('should return correct value for different metrics', () => {
      const result = {
        netProfit: 10000,
        afterTaxProfit: 15000,
        operationalProfit: 20000,
        roi: 25,
        annualizedRoi: 12.5
      };

      expect(getDisplayValue(result, 'netProfit')).toBe(10000);
      expect(getDisplayValue(result, 'afterTaxProfit')).toBe(15000);
      expect(getDisplayValue(result, 'operationalProfit')).toBe(20000);
      expect(getDisplayValue(result, 'roi', false)).toBe(25);
      expect(getDisplayValue(result, 'roi', true)).toBe(12.5);
    });
  });

  describe('calculateMonthlyGrowth', () => {
    it('should calculate monthly growth percentage', () => {
      const start = 900;
      const end = 1080; // 20% increase
      const result = calculateMonthlyGrowth(start, end);
      
      expect(result).toBeCloseTo(1.67, 1); // 20% / 12 months
    });
  });

  describe('calculateAnnualIncreases', () => {
    it('should calculate annual increases from start/end values', () => {
      const params = {
        btcPriceStart: 100000,
        btcPriceEnd: 150000,
        networkHashrateStart: 900,
        networkHashrateEnd: 1080
      };
      
      const result = calculateAnnualIncreases(params);
      
      expect(result.annualBtcPriceIncrease).toBeCloseTo(50, 1);
      expect(result.annualDifficultyIncrease).toBeCloseTo(20, 1);
    });
  });
});
