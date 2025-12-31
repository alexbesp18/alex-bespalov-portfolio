/**
 * Mining Calculations Tests
 * @jest-environment node
 */

import {
  calculateNetworkShare,
  calculateDailyBtcMined,
  calculateMonthlyBtcMined,
  calculateElectricityCost,
  calculateMonthlyElectricity,
  calculatePoolFee,
  calculateMonthlyProfit,
  getCalculatedEndValues,
  calculateMonthlyGrowth,
  calculateBreakevenElectricityRate,
  calculateBreakevenBtcPrice,
} from '../calculations/mining.js';

import { BLOCK_REWARD, BLOCKS_PER_DAY, DAYS_PER_MONTH } from '../constants/bitcoin.js';

describe('Mining Calculations', () => {
  describe('calculateNetworkShare', () => {
    it('calculates correct network share', () => {
      // 500 TH/s miner with 1000 EH/s network = 500 / 1,000,000,000 = 0.0000005
      const share = calculateNetworkShare(500, 1000);
      expect(share).toBeCloseTo(0.0000005, 10);
    });
    
    it('returns 0 for zero network hashrate', () => {
      expect(calculateNetworkShare(500, 0)).toBe(0);
    });
    
    it('returns 0 for negative network hashrate', () => {
      expect(calculateNetworkShare(500, -1000)).toBe(0);
    });
  });
  
  describe('calculateDailyBtcMined', () => {
    it('calculates daily BTC mined correctly', () => {
      const daily = calculateDailyBtcMined(500, 1000, BLOCK_REWARD, 100);
      const expectedShare = 500 / (1000 * 1000000);
      const expected = expectedShare * BLOCKS_PER_DAY * BLOCK_REWARD;
      expect(daily).toBeCloseTo(expected, 10);
    });
    
    it('accounts for uptime percentage', () => {
      const fullUptime = calculateDailyBtcMined(500, 1000, BLOCK_REWARD, 100);
      const halfUptime = calculateDailyBtcMined(500, 1000, BLOCK_REWARD, 50);
      expect(halfUptime).toBeCloseTo(fullUptime * 0.5, 10);
    });
  });
  
  describe('calculateMonthlyBtcMined', () => {
    it('calculates monthly BTC mined correctly', () => {
      const monthly = calculateMonthlyBtcMined(500, 1000, BLOCK_REWARD, 100);
      const daily = calculateDailyBtcMined(500, 1000, BLOCK_REWARD, 100);
      expect(monthly).toBeCloseTo(daily * DAYS_PER_MONTH, 10);
    });
  });
  
  describe('calculateElectricityCost', () => {
    it('calculates electricity cost correctly', () => {
      // 3000W * 24 hours * $0.10/kWh = 3kW * 24 * $0.10 = $7.20
      const cost = calculateElectricityCost(3000, 0.10, 24);
      expect(cost).toBeCloseTo(7.2, 2);
    });
  });
  
  describe('calculateMonthlyElectricity', () => {
    it('calculates monthly electricity cost correctly', () => {
      const monthly = calculateMonthlyElectricity(3000, 0.10);
      const expected = (3000 / 1000) * 24 * DAYS_PER_MONTH * 0.10;
      expect(monthly).toBeCloseTo(expected, 2);
    });
  });
  
  describe('calculatePoolFee', () => {
    it('calculates pool fee correctly', () => {
      const fee = calculatePoolFee(1000, 2);
      expect(fee).toBe(20);
    });
    
    it('clamps fee percentage to 0-100', () => {
      expect(calculatePoolFee(1000, -5)).toBe(0);
      expect(calculatePoolFee(1000, 150)).toBe(1000);
    });
  });
  
  describe('calculateMonthlyProfit', () => {
    const testMiner = { hashrate: 500, power: 5500 };
    const testParams = {
      btcPrice: 100000,
      networkHashrate: 900,
      electricityRate: 0.05,
      poolFee: 2,
      uptime: 100,
    };
    
    it('returns all expected fields', () => {
      const result = calculateMonthlyProfit(testMiner, testParams);
      
      expect(result).toHaveProperty('btcMined');
      expect(result).toHaveProperty('btcMinedNet');
      expect(result).toHaveProperty('grossRevenue');
      expect(result).toHaveProperty('poolFees');
      expect(result).toHaveProperty('netRevenue');
      expect(result).toHaveProperty('electricityCost');
      expect(result).toHaveProperty('operationalProfit');
    });
    
    it('calculates positive profit for efficient miner with low electricity', () => {
      const result = calculateMonthlyProfit(testMiner, testParams);
      expect(result.operationalProfit).toBeGreaterThan(0);
    });
    
    it('net BTC is less than gross due to pool fee', () => {
      const result = calculateMonthlyProfit(testMiner, testParams);
      expect(result.btcMinedNet).toBeLessThan(result.btcMined);
      expect(result.btcMinedNet).toBeCloseTo(result.btcMined * 0.98, 10);
    });
  });
  
  describe('getCalculatedEndValues', () => {
    it('returns direct values when not using annual increases', () => {
      const params = {
        btcPriceStart: 100000,
        btcPriceEnd: 150000,
        networkHashrateStart: 900,
        networkHashrateEnd: 1200,
        useAnnualIncreases: false,
      };
      
      const result = getCalculatedEndValues(params);
      expect(result.btcPriceEnd).toBe(150000);
      expect(result.networkHashrateEnd).toBe(1200);
    });
    
    it('calculates end values from annual increases', () => {
      const params = {
        btcPriceStart: 100000,
        networkHashrateStart: 900,
        annualBtcPriceIncrease: 50,
        annualDifficultyIncrease: 25,
        useAnnualIncreases: true,
      };
      
      const result = getCalculatedEndValues(params);
      expect(result.btcPriceEnd).toBe(150000);
      expect(result.networkHashrateEnd).toBe(1125);
    });
  });
  
  describe('calculateMonthlyGrowth', () => {
    it('calculates monthly growth rate correctly', () => {
      // 50% annual growth = ~4.17% monthly
      const monthlyGrowth = calculateMonthlyGrowth(100, 150, 12);
      expect(monthlyGrowth).toBeCloseTo(4.17, 1);
    });
    
    it('returns 0 for zero start value', () => {
      expect(calculateMonthlyGrowth(0, 100, 12)).toBe(0);
    });
  });
  
  describe('calculateBreakevenElectricityRate', () => {
    it('calculates breakeven electricity rate', () => {
      const miner = { hashrate: 500, power: 5500 };
      const rate = calculateBreakevenElectricityRate(miner, 100000, 900, 2);
      
      expect(rate).toBeGreaterThan(0);
      expect(rate).toBeLessThan(1); // Should be a reasonable rate
    });
  });
  
  describe('calculateBreakevenBtcPrice', () => {
    it('calculates breakeven BTC price', () => {
      const miner = { hashrate: 500, power: 5500 };
      const price = calculateBreakevenBtcPrice(miner, 900, 0.05, 2);
      
      expect(price).toBeGreaterThan(0);
      expect(price).toBeLessThan(1000000); // Should be reasonable
    });
  });
});

