/**
 * Financial calculation utilities for retirement planning
 * 
 * This module contains pure functions for calculating future values,
 * required returns, and retirement funding needs.
 */

import { NEWTON_METHOD_CONFIG } from '../config/constants';

/**
 * Calculate future value based on present value and inflation rate
 * 
 * @param {number} presentValue - The current value in today's dollars
 * @param {number} years - Number of years into the future
 * @param {number} inflationRate - Annual inflation rate as a percentage (e.g., 2.7 for 2.7%)
 * @returns {number} The future value adjusted for inflation
 * 
 * @example
 * calculateFutureValue(100000, 20, 2.7) // Returns ~170,243
 */
export const calculateFutureValue = (presentValue, years, inflationRate) => {
  return presentValue * Math.pow(1 + inflationRate / 100, years);
};

/**
 * Calculate required annual return rate for a lump sum investment
 * 
 * @param {number} presentValue - Initial investment amount
 * @param {number} futureValue - Target future value
 * @param {number} years - Number of years to reach target
 * @returns {number} Required annual return as a percentage
 * 
 * @example
 * calculateRequiredReturn(50000, 1000000, 20) // Returns ~16.16%
 */
export const calculateRequiredReturn = (presentValue, futureValue, years) => {
  if (presentValue <= 0 || years <= 0) {
    return Infinity;
  }
  return (Math.pow(futureValue / presentValue, 1 / years) - 1) * 100;
};

/**
 * Calculate required annual return with regular contributions using Newton's method
 * 
 * For investments with annual contributions, there's no closed-form solution.
 * We use the Newton-Raphson method to iteratively find the required rate.
 * 
 * The future value formula being solved:
 * FV = P(1+r)^n + C[(1+r)^n - 1]/r
 * 
 * Where:
 * - P = initial investment
 * - C = annual contribution
 * - r = annual return rate
 * - n = number of years
 * 
 * @param {number} initialInvestment - Lump sum investment at start
 * @param {number} annualContribution - Amount added each year
 * @param {number} targetValue - Desired future value
 * @param {number} years - Number of years
 * @returns {number} Required annual return as a percentage
 */
export const calculateRequiredReturnWithContributions = (
  initialInvestment,
  annualContribution,
  targetValue,
  years
) => {
  // If no contributions, use simple formula
  if (annualContribution === 0) {
    return calculateRequiredReturn(initialInvestment, targetValue, years);
  }

  // If total contributions already exceed target, no return needed
  const totalContributions = initialInvestment + (annualContribution * years);
  if (totalContributions >= targetValue) {
    return 0;
  }

  const { initialGuess, tolerance, maxIterations } = NEWTON_METHOD_CONFIG;
  let rate = initialGuess;

  for (let i = 0; i < maxIterations; i++) {
    const r = rate;

    // Calculate future value with current rate guess
    // FV = P(1+r)^n + C[(1+r)^n - 1]/r
    const compoundFactor = Math.pow(1 + r, years);
    const fv = initialInvestment * compoundFactor +
               annualContribution * ((compoundFactor - 1) / r);

    // Calculate derivative for Newton's method
    // d(FV)/dr = P*n*(1+r)^(n-1) + C*[n*(1+r)^(n-1)*r - ((1+r)^n - 1)] / r^2
    const dfv = initialInvestment * years * Math.pow(1 + r, years - 1) +
                annualContribution * (
                  (years * Math.pow(1 + r, years - 1) * r - (compoundFactor - 1)) / (r * r)
                );

    // Newton's method update: r_new = r - f(r)/f'(r)
    const newRate = r - (fv - targetValue) / dfv;

    // Check for convergence
    if (Math.abs(newRate - rate) < tolerance) {
      return newRate * 100;
    }

    rate = newRate;
  }

  // Return best guess if max iterations reached
  return rate * 100;
};

/**
 * Calculate future value of investments with expected return rate
 * 
 * Computes the future value of an initial investment plus regular contributions
 * growing at a specified annual return rate.
 * 
 * @param {number} initialInvestment - Starting investment amount
 * @param {number} annualContribution - Amount added each year
 * @param {number} returnRate - Expected annual return as percentage
 * @param {number} years - Number of years to grow
 * @returns {number} Projected future value
 * 
 * @example
 * calculateFutureValueWithReturn(50000, 10000, 9.6, 20) // Returns ~876,432
 */
export const calculateFutureValueWithReturn = (
  initialInvestment,
  annualContribution,
  returnRate,
  years
) => {
  // Handle edge cases
  if (years <= 0) {
    return initialInvestment;
  }
  
  const r = returnRate / 100;

  // Handle zero return rate
  if (r === 0) {
    return initialInvestment + (annualContribution * years);
  }

  if (annualContribution === 0) {
    return initialInvestment * Math.pow(1 + r, years);
  }

  const compoundFactor = Math.pow(1 + r, years);
  const futureValueInitial = initialInvestment * compoundFactor;
  const futureValueContributions = annualContribution * ((compoundFactor - 1) / r);

  return futureValueInitial + futureValueContributions;
};

/**
 * Calculate additional annual contribution needed to reach a target
 * 
 * Given current investment, contribution, and expected return, calculates
 * how much additional annual saving is needed to close the gap to a target.
 * 
 * @param {number} initialInvestment - Starting investment amount
 * @param {number} currentContribution - Current annual contribution
 * @param {number} targetValue - Desired future value
 * @param {number} returnRate - Expected annual return as percentage
 * @param {number} years - Number of years
 * @returns {number} Additional annual contribution needed (0 if already on track)
 */
export const calculateAdditionalContributionNeeded = (
  initialInvestment,
  currentContribution,
  targetValue,
  returnRate,
  years
) => {
  // Handle edge cases
  if (years <= 0) {
    return Math.max(0, targetValue - initialInvestment);
  }
  
  const r = returnRate / 100;
  
  // Handle zero return rate
  if (r === 0) {
    const gap = targetValue - initialInvestment - (currentContribution * years);
    return gap <= 0 ? 0 : gap / years;
  }
  
  const compoundFactor = Math.pow(1 + r, years);
  
  const futureValueInitial = initialInvestment * compoundFactor;
  const futureValueCurrentContrib = currentContribution * ((compoundFactor - 1) / r);

  const gap = targetValue - futureValueInitial - futureValueCurrentContrib;

  if (gap <= 0) {
    return 0;
  }

  // Calculate additional annual contribution needed to close gap
  const additionalNeeded = gap / ((compoundFactor - 1) / r);

  return Math.max(0, additionalNeeded);
};

/**
 * Calculate total retirement funding needed over retirement years
 * 
 * Sums up the inflation-adjusted income needed for each year of retirement,
 * from retirement age through end of life expectancy.
 * 
 * @param {number} desiredIncome - Annual income needed in today's dollars
 * @param {number} currentAge - Current age
 * @param {number} retirementAge - Age at retirement
 * @param {number} endAge - Life expectancy age
 * @param {number} inflationRate - Annual inflation rate as percentage
 * @returns {number} Total funding needed in future dollars
 */
export const calculateTotalFunding = (
  desiredIncome,
  currentAge,
  retirementAge,
  endAge,
  inflationRate
) => {
  let total = 0;
  const yearsInRetirement = endAge - retirementAge;

  for (let year = 0; year < yearsInRetirement; year++) {
    const yearsFromNow = retirementAge - currentAge + year;
    const futureValue = calculateFutureValue(desiredIncome, yearsFromNow, inflationRate);
    total += futureValue;
  }

  return total;
};

/**
 * Calculate future income requirements at various ages
 * 
 * @param {number} currentAge - Current age
 * @param {number} retirementAge - Age at retirement
 * @param {number} endAge - Life expectancy age
 * @param {number} desiredIncome - Annual income in today's dollars
 * @param {Object} inflationRates - Object with best, base, worst, custom rates
 * @returns {Array<Object>} Array of future value calculations by age
 */
export const calculateFutureValuesByAge = (
  currentAge,
  retirementAge,
  endAge,
  desiredIncome,
  inflationRates
) => {
  const ages = [retirementAge, 60, 70, 80, endAge]
    .filter(age => age >= retirementAge && age <= endAge)
    .filter((age, index, self) => self.indexOf(age) === index); // Remove duplicates

  return ages.map(age => {
    const years = age - currentAge;
    return {
      age,
      years,
      best: calculateFutureValue(desiredIncome, years, inflationRates.best),
      base: calculateFutureValue(desiredIncome, years, inflationRates.base),
      worst: calculateFutureValue(desiredIncome, years, inflationRates.worst),
      custom: calculateFutureValue(desiredIncome, years, inflationRates.custom),
    };
  });
};

/**
 * Calculate required returns for various investment amounts
 * 
 * @param {Array<number>} investmentAmounts - Array of investment amounts to analyze
 * @param {number} annualContribution - Annual contribution amount
 * @param {Object} fundingTargets - Object with base, worst, custom funding targets
 * @param {number} yearsToRetirement - Years until retirement
 * @returns {Array<Object>} Array of required return calculations
 */
export const calculateRequiredReturnsTable = (
  investmentAmounts,
  annualContribution,
  fundingTargets,
  yearsToRetirement
) => {
  return investmentAmounts.map(amount => ({
    investment: amount,
    baseReturn: calculateRequiredReturn(amount, fundingTargets.base, yearsToRetirement),
    baseReturnWithContrib: calculateRequiredReturnWithContributions(
      amount, annualContribution, fundingTargets.base, yearsToRetirement
    ),
    worstReturn: calculateRequiredReturn(amount, fundingTargets.worst, yearsToRetirement),
    worstReturnWithContrib: calculateRequiredReturnWithContributions(
      amount, annualContribution, fundingTargets.worst, yearsToRetirement
    ),
    customReturn: calculateRequiredReturn(amount, fundingTargets.custom, yearsToRetirement),
    customReturnWithContrib: calculateRequiredReturnWithContributions(
      amount, annualContribution, fundingTargets.custom, yearsToRetirement
    ),
  }));
};

/**
 * Calculate projected outcomes for various investment scenarios
 * 
 * @param {Array<number>} investmentAmounts - Array of investment amounts to analyze
 * @param {number} annualContribution - Annual contribution amount
 * @param {number} expectedReturn - Expected annual return rate
 * @param {number} yearsToRetirement - Years until retirement
 * @param {Object} fundingTargets - Object with base, worst, custom funding targets
 * @returns {Array<Object>} Array of projected outcome calculations
 */
export const calculateProjectedOutcomes = (
  investmentAmounts,
  annualContribution,
  expectedReturn,
  yearsToRetirement,
  fundingTargets
) => {
  return investmentAmounts.map(amount => {
    const projectedValue = calculateFutureValueWithReturn(
      amount, annualContribution, expectedReturn, yearsToRetirement
    );

    return {
      investment: amount,
      projectedValue,
      baseCaseTarget: fundingTargets.base,
      baseCaseGap: fundingTargets.base - projectedValue,
      baseCaseMet: projectedValue >= fundingTargets.base,
      additionalForBase: calculateAdditionalContributionNeeded(
        amount, annualContribution, fundingTargets.base, expectedReturn, yearsToRetirement
      ),
      worstCaseTarget: fundingTargets.worst,
      worstCaseGap: fundingTargets.worst - projectedValue,
      worstCaseMet: projectedValue >= fundingTargets.worst,
      additionalForWorst: calculateAdditionalContributionNeeded(
        amount, annualContribution, fundingTargets.worst, expectedReturn, yearsToRetirement
      ),
      customTarget: fundingTargets.custom,
      customGap: fundingTargets.custom - projectedValue,
      customMet: projectedValue >= fundingTargets.custom,
      additionalForCustom: calculateAdditionalContributionNeeded(
        amount, annualContribution, fundingTargets.custom, expectedReturn, yearsToRetirement
      ),
    };
  });
};

