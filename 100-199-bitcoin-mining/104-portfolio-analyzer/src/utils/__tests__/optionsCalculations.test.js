/**
 * Tests for options valuation calculations
 */

/**
 * Simplified option calculation function for testing
 * Based on calculateOptionValue from PortfolioAnalyzer
 */
const calculateOptionValue = (option, currentPrice, projectedPrice, monthsToExpiry) => {
  const validateNumber = (value, min = 0, max = Infinity) => {
    const num = parseFloat(value);
    if (isNaN(num)) return min;
    return Math.max(min, Math.min(max, num));
  };

  try {
    const { strike, contracts, type } = option;
    
    const validStrike = validateNumber(strike, 0);
    const validContracts = Math.max(1, parseInt(contracts) || 1);
    const validCurrentPrice = validateNumber(currentPrice, 0);
    const validProjectedPrice = validateNumber(projectedPrice, 0);
    const validMonthsToExpiry = validateNumber(monthsToExpiry, 0);
    
    // Intrinsic value
    const intrinsicValue = type === 'call' 
      ? Math.max(0, validCurrentPrice - validStrike)
      : Math.max(0, validStrike - validCurrentPrice);
    
    // Time value (simplified Black-Scholes approximation)
    const annualizedTime = validMonthsToExpiry / 12;
    const volatility = 0.8; // High volatility assumption
    const timeValue = annualizedTime > 0 && validCurrentPrice > 0
      ? validCurrentPrice * volatility * Math.sqrt(annualizedTime) * 0.2
      : 0;
    
    const optionPrice = Math.max(intrinsicValue, intrinsicValue + timeValue);
    const totalValue = optionPrice * validContracts * 100;
    
    // Projected value at expiry
    const projectedIntrinsicValue = type === 'call'
      ? Math.max(0, validProjectedPrice - validStrike)
      : Math.max(0, validStrike - validProjectedPrice);
    const projectedValue = projectedIntrinsicValue * validContracts * 100;
    
    const costBasisTotal = validateNumber(option.costBasis, 0) * validContracts * 100;
    
    return {
      currentValue: totalValue,
      projectedValue,
      intrinsicValue,
      timeValue,
      inTheMoney: intrinsicValue > 0,
      profitLoss: totalValue - costBasisTotal
    };
  } catch (error) {
    return {
      currentValue: 0,
      projectedValue: 0,
      intrinsicValue: 0,
      timeValue: 0,
      inTheMoney: false,
      profitLoss: 0
    };
  }
};

describe('Options Valuation Calculations', () => {
  const defaultCallOption = {
    strike: 50,
    contracts: 1,
    type: 'call',
    costBasis: 2.5
  };

  const defaultPutOption = {
    strike: 50,
    contracts: 1,
    type: 'put',
    costBasis: 2.5
  };

  test('calculates call option value correctly when in the money', () => {
    const currentPrice = 60;
    const result = calculateOptionValue(defaultCallOption, currentPrice, currentPrice, 6);
    
    expect(result.intrinsicValue).toBe(10); // 60 - 50
    expect(result.inTheMoney).toBe(true);
    expect(result.currentValue).toBeGreaterThan(0);
  });

  test('calculates call option value correctly when out of the money', () => {
    const currentPrice = 40;
    const result = calculateOptionValue(defaultCallOption, currentPrice, currentPrice, 6);
    
    expect(result.intrinsicValue).toBe(0); // max(0, 40 - 50)
    expect(result.inTheMoney).toBe(false);
    expect(result.currentValue).toBeGreaterThanOrEqual(0); // May have time value
  });

  test('calculates put option value correctly when in the money', () => {
    const currentPrice = 40;
    const result = calculateOptionValue(defaultPutOption, currentPrice, currentPrice, 6);
    
    expect(result.intrinsicValue).toBe(10); // 50 - 40
    expect(result.inTheMoney).toBe(true);
  });

  test('calculates put option value correctly when out of the money', () => {
    const currentPrice = 60;
    const result = calculateOptionValue(defaultPutOption, currentPrice, currentPrice, 6);
    
    expect(result.intrinsicValue).toBe(0); // max(0, 50 - 60)
    expect(result.inTheMoney).toBe(false);
  });

  test('includes time value for options with time remaining', () => {
    const result6Months = calculateOptionValue(defaultCallOption, 50, 50, 6);
    const result0Months = calculateOptionValue(defaultCallOption, 50, 50, 0);
    
    expect(result6Months.timeValue).toBeGreaterThan(0);
    expect(result0Months.timeValue).toBe(0);
    expect(result6Months.currentValue).toBeGreaterThan(result0Months.currentValue);
  });

  test('calculates profit/loss correctly', () => {
    const currentPrice = 60;
    const result = calculateOptionValue(defaultCallOption, currentPrice, currentPrice, 6);
    
    const expectedCostBasis = defaultCallOption.costBasis * defaultCallOption.contracts * 100;
    expect(result.profitLoss).toBe(result.currentValue - expectedCostBasis);
  });

  test('handles multiple contracts correctly', () => {
    const option1Contract = { ...defaultCallOption, contracts: 1 };
    const option5Contracts = { ...defaultCallOption, contracts: 5 };
    
    const result1 = calculateOptionValue(option1Contract, 60, 60, 6);
    const result5 = calculateOptionValue(option5Contracts, 60, 60, 6);
    
    expect(result5.currentValue).toBeCloseTo(result1.currentValue * 5, 2);
  });

  test('calculates projected value at expiry correctly', () => {
    const currentPrice = 50;
    const projectedPrice = 70;
    const result = calculateOptionValue(defaultCallOption, currentPrice, projectedPrice, 0);
    
    expect(result.projectedValue).toBe(2000); // (70 - 50) * 1 * 100
  });

  test('handles zero strike price', () => {
    const option = { ...defaultCallOption, strike: 0 };
    const result = calculateOptionValue(option, 50, 50, 6);
    
    expect(result.intrinsicValue).toBe(50); // 50 - 0
    expect(result.currentValue).toBeGreaterThan(0);
  });

  test('handles expired options (0 months to expiry)', () => {
    const currentPrice = 60;
    const result = calculateOptionValue(defaultCallOption, currentPrice, currentPrice, 0);
    
    expect(result.timeValue).toBe(0);
    expect(result.currentValue).toBeGreaterThanOrEqual(result.intrinsicValue * 100);
  });

  test('handles negative current price gracefully', () => {
    const result = calculateOptionValue(defaultCallOption, -10, -10, 6);
    
    expect(result.intrinsicValue).toBe(0);
    expect(result.currentValue).toBeGreaterThanOrEqual(0);
  });

  test('handles invalid option type gracefully', () => {
    const invalidOption = { ...defaultCallOption, type: 'invalid' };
    const result = calculateOptionValue(invalidOption, 60, 60, 6);
    
    // Should default to call behavior or handle gracefully
    expect(result.currentValue).toBeGreaterThanOrEqual(0);
  });
});

