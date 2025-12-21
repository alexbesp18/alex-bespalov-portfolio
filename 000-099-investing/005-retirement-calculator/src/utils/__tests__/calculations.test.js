/**
 * Tests for financial calculation utilities
 */

import {
  calculateFutureValue,
  calculateRequiredReturn,
  calculateRequiredReturnWithContributions,
  calculateFutureValueWithReturn,
  calculateAdditionalContributionNeeded,
  calculateTotalFunding,
  calculateFutureValuesByAge,
  calculateRequiredReturnsTable,
  calculateProjectedOutcomes,
} from '../calculations';

describe('calculateFutureValue', () => {
  it('should calculate future value with inflation correctly', () => {
    // $100,000 at 2.7% inflation for 20 years
    const result = calculateFutureValue(100000, 20, 2.7);
    expect(result).toBeCloseTo(170376.18, 0);
  });

  it('should return present value when years is 0', () => {
    const result = calculateFutureValue(100000, 0, 2.7);
    expect(result).toBe(100000);
  });

  it('should return present value when inflation is 0', () => {
    const result = calculateFutureValue(100000, 20, 0);
    expect(result).toBe(100000);
  });

  it('should handle high inflation rates', () => {
    const result = calculateFutureValue(100000, 10, 10);
    expect(result).toBeCloseTo(259374.25, 0);
  });
});

describe('calculateRequiredReturn', () => {
  it('should calculate required return for lump sum investment', () => {
    // Need $1M from $50K in 20 years
    const result = calculateRequiredReturn(50000, 1000000, 20);
    expect(result).toBeCloseTo(16.16, 1);
  });

  it('should return 0 when present value equals future value', () => {
    const result = calculateRequiredReturn(100000, 100000, 20);
    expect(result).toBeCloseTo(0, 5);
  });

  it('should handle very short time periods', () => {
    const result = calculateRequiredReturn(100000, 110000, 1);
    expect(result).toBeCloseTo(10, 1);
  });

  it('should return Infinity for zero initial investment', () => {
    const result = calculateRequiredReturn(0, 1000000, 20);
    expect(result).toBe(Infinity);
  });
});

describe('calculateRequiredReturnWithContributions', () => {
  it('should use simple formula when no contributions', () => {
    const result = calculateRequiredReturnWithContributions(50000, 0, 1000000, 20);
    expect(result).toBeCloseTo(16.16, 1);
  });

  it('should reduce required return when adding contributions', () => {
    const withoutContrib = calculateRequiredReturnWithContributions(50000, 0, 1000000, 20);
    const withContrib = calculateRequiredReturnWithContributions(50000, 10000, 1000000, 20);
    expect(withContrib).toBeLessThan(withoutContrib);
  });

  it('should return 0 when total contributions exceed target', () => {
    // $50K initial + $100K/yr * 20 years = $2.05M > $1M target
    const result = calculateRequiredReturnWithContributions(50000, 100000, 1000000, 20);
    expect(result).toBe(0);
  });

  it('should converge to reasonable return with moderate contributions', () => {
    const result = calculateRequiredReturnWithContributions(50000, 5000, 500000, 20);
    expect(result).toBeGreaterThan(0);
    expect(result).toBeLessThan(20);
  });
});

describe('calculateFutureValueWithReturn', () => {
  it('should calculate future value with returns for lump sum', () => {
    // $50K at 9.6% for 20 years
    const result = calculateFutureValueWithReturn(50000, 0, 9.6, 20);
    expect(result).toBeCloseTo(312738.31, 0);
  });

  it('should include contributions in future value', () => {
    const lumpSumOnly = calculateFutureValueWithReturn(50000, 0, 9.6, 20);
    const withContrib = calculateFutureValueWithReturn(50000, 10000, 9.6, 20);
    expect(withContrib).toBeGreaterThan(lumpSumOnly);
  });

  it('should return initial investment when return rate is 0', () => {
    const result = calculateFutureValueWithReturn(50000, 0, 0, 20);
    expect(result).toBe(50000);
  });

  it('should handle zero return rate with contributions', () => {
    // $50K + $10K/yr for 20 years at 0% = $50K + $200K = $250K
    const result = calculateFutureValueWithReturn(50000, 10000, 0, 20);
    expect(result).toBe(250000);
  });

  it('should return initial investment when years is 0', () => {
    const result = calculateFutureValueWithReturn(50000, 10000, 9.6, 0);
    expect(result).toBe(50000);
  });

  it('should handle negative years gracefully', () => {
    const result = calculateFutureValueWithReturn(50000, 10000, 9.6, -5);
    expect(result).toBe(50000);
  });
});

describe('calculateAdditionalContributionNeeded', () => {
  it('should return 0 when already on track', () => {
    // Large initial investment that will exceed target
    const result = calculateAdditionalContributionNeeded(500000, 10000, 100000, 9.6, 20);
    expect(result).toBe(0);
  });

  it('should calculate positive additional contribution when short', () => {
    const result = calculateAdditionalContributionNeeded(10000, 0, 1000000, 9.6, 20);
    expect(result).toBeGreaterThan(0);
  });

  it('should reduce additional needed when current contribution increases', () => {
    const noContrib = calculateAdditionalContributionNeeded(10000, 0, 1000000, 9.6, 20);
    const withContrib = calculateAdditionalContributionNeeded(10000, 5000, 1000000, 9.6, 20);
    expect(withContrib).toBeLessThan(noContrib);
  });

  it('should handle zero return rate', () => {
    // Need $100K, have $50K initial, 0 contribution, 20 years, 0% return
    // Gap = $100K - $50K = $50K, need $50K / 20 = $2.5K/yr
    const result = calculateAdditionalContributionNeeded(50000, 0, 100000, 0, 20);
    expect(result).toBe(2500);
  });

  it('should handle zero years', () => {
    // With 0 years, just need the gap immediately
    const result = calculateAdditionalContributionNeeded(50000, 0, 100000, 9.6, 0);
    expect(result).toBe(50000);
  });
});

describe('calculateTotalFunding', () => {
  it('should calculate total funding for retirement period', () => {
    const result = calculateTotalFunding(100000, 30, 50, 70, 2.7);
    // 20 years in retirement, each year inflated
    expect(result).toBeGreaterThan(100000 * 20);
  });

  it('should increase with higher inflation', () => {
    const lowInflation = calculateTotalFunding(100000, 30, 50, 70, 1.8);
    const highInflation = calculateTotalFunding(100000, 30, 50, 70, 4.5);
    expect(highInflation).toBeGreaterThan(lowInflation);
  });

  it('should increase with longer retirement period', () => {
    const shortRetirement = calculateTotalFunding(100000, 30, 50, 70, 2.7);
    const longRetirement = calculateTotalFunding(100000, 30, 50, 90, 2.7);
    expect(longRetirement).toBeGreaterThan(shortRetirement);
  });
});

describe('calculateFutureValuesByAge', () => {
  it('should return array of future values at different ages', () => {
    const inflationRates = { best: 1.8, base: 2.7, worst: 4.5, custom: 3.0 };
    const result = calculateFutureValuesByAge(30, 50, 80, 100000, inflationRates);
    
    expect(Array.isArray(result)).toBe(true);
    expect(result.length).toBeGreaterThan(0);
    expect(result[0]).toHaveProperty('age');
    expect(result[0]).toHaveProperty('years');
    expect(result[0]).toHaveProperty('best');
    expect(result[0]).toHaveProperty('base');
    expect(result[0]).toHaveProperty('worst');
  });

  it('should filter ages within retirement range', () => {
    const inflationRates = { best: 1.8, base: 2.7, worst: 4.5, custom: 3.0 };
    const result = calculateFutureValuesByAge(45, 55, 75, 100000, inflationRates);
    
    result.forEach(item => {
      expect(item.age).toBeGreaterThanOrEqual(55);
      expect(item.age).toBeLessThanOrEqual(75);
    });
  });
});

describe('calculateRequiredReturnsTable', () => {
  it('should calculate returns for multiple investment amounts', () => {
    const amounts = [10000, 50000, 100000];
    const fundingTargets = { base: 1000000, worst: 1500000, custom: 1200000 };
    const result = calculateRequiredReturnsTable(amounts, 5000, fundingTargets, 20, 3.0);
    
    expect(result.length).toBe(3);
    expect(result[0]).toHaveProperty('investment', 10000);
    expect(result[0]).toHaveProperty('baseReturn');
    expect(result[0]).toHaveProperty('baseReturnWithContrib');
    expect(result[0]).toHaveProperty('worstReturn');
  });

  it('should have lower returns for higher initial investments', () => {
    const amounts = [10000, 100000];
    const fundingTargets = { base: 1000000, worst: 1500000, custom: 1200000 };
    const result = calculateRequiredReturnsTable(amounts, 0, fundingTargets, 20, 3.0);
    
    expect(result[0].baseReturn).toBeGreaterThan(result[1].baseReturn);
  });
});

describe('calculateProjectedOutcomes', () => {
  it('should calculate projected outcomes for investment amounts', () => {
    const amounts = [25000, 50000, 100000];
    const fundingTargets = { base: 500000, worst: 750000, custom: 600000 };
    const result = calculateProjectedOutcomes(amounts, 5000, 9.6, 20, fundingTargets);
    
    expect(result.length).toBe(3);
    expect(result[0]).toHaveProperty('projectedValue');
    expect(result[0]).toHaveProperty('baseCaseMet');
    expect(result[0]).toHaveProperty('baseCaseGap');
    expect(result[0]).toHaveProperty('additionalForBase');
  });

  it('should mark goals as met when projected value exceeds target', () => {
    const amounts = [500000]; // Large enough to meet targets
    const fundingTargets = { base: 100000, worst: 150000, custom: 120000 };
    const result = calculateProjectedOutcomes(amounts, 0, 9.6, 20, fundingTargets);
    
    expect(result[0].baseCaseMet).toBe(true);
    expect(result[0].worstCaseMet).toBe(true);
  });
});

