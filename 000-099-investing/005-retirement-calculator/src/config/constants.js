/**
 * Application configuration constants
 * Centralized configuration for the retirement calculator
 */

/**
 * Inflation rate scenarios (annual percentage)
 */
export const INFLATION_RATES = {
  best: 1.8,   // Historical low inflation periods
  base: 2.7,  // 20-year average inflation
  worst: 4.5, // High inflation periods
};

/**
 * Default input values for the calculator
 */
export const DEFAULT_VALUES = {
  currentAge: 29,
  retirementAge: 50,
  endAge: 90,
  desiredIncome: 100000,
  initialInvestment: 50000,
  annualContribution: 0,
  expectedReturn: 9.6, // S&P 500 historical average
  customInflation: 2.7,
  inflationScenario: 'base',
};

/**
 * Input validation constraints
 */
export const INPUT_CONSTRAINTS = {
  minAge: 18,
  maxAge: 100,
  maxLifeExpectancy: 120,
  minInflation: 0,
  maxInflation: 20,
  minReturn: 0,
  maxReturn: 50,
  contributionStep: 1000,
  investmentStep: 5000,
};

/**
 * Newton's method configuration for required return calculation
 */
export const NEWTON_METHOD_CONFIG = {
  initialGuess: 0.1,    // 10% initial rate guess
  tolerance: 0.0001,    // Convergence tolerance
  maxIterations: 100,   // Maximum iterations before giving up
};

/**
 * Display configuration
 */
export const DISPLAY_CONFIG = {
  currency: 'USD',
  locale: 'en-US',
  percentDecimals: 2,
  projectedOutcomesAmounts: [25000, 50000, 75000, 100000, 150000],
  requiredReturnsAmounts: [10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000],
  maxProjectedOutcomes: 6,
};

/**
 * Return rate thresholds for UI highlighting
 */
export const RETURN_THRESHOLDS = {
  unrealistic: 20,      // Returns above this are highlighted as unrealistic
  veryUnrealistic: 25,  // Returns above this are extremely unrealistic
};

