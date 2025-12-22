/**
 * Tax and Depreciation Constants
 * 
 * Constants related to tax calculations and depreciation schedules
 * for Bitcoin mining equipment.
 * 
 * @module constants/tax
 */

/**
 * MACRS 5-year depreciation schedule
 * Used for standard equipment depreciation without bonus depreciation
 * 
 * Year 1: 20%, Year 2: 32%, Year 3: 19.2%, Year 4: 11.52%, Year 5: 11.52%, Year 6: 5.76%
 * 
 * @constant {number[]}
 */
export const MACRS_RATES = [0.20, 0.32, 0.192, 0.1152, 0.1152, 0.0576];

/**
 * MACRS 7-year depreciation schedule (alternative)
 * @constant {number[]}
 */
export const MACRS_RATES_7_YEAR = [0.1429, 0.2449, 0.1749, 0.1249, 0.0893, 0.0892, 0.0893, 0.0446];

/**
 * Default federal tax rate for business income
 * @constant {number}
 */
export const DEFAULT_FEDERAL_TAX_RATE = 35;

/**
 * Default state tax rate (0 for states without income tax)
 * @constant {number}
 */
export const DEFAULT_STATE_TAX_RATE = 0;

/**
 * Common state tax rates by state
 * @constant {Object}
 */
export const STATE_TAX_RATES = {
  TX: 0,      // Texas - no income tax
  WY: 0,      // Wyoming - no income tax
  FL: 0,      // Florida - no income tax
  NV: 0,      // Nevada - no income tax
  WA: 0,      // Washington - no income tax (but B&O tax)
  CA: 13.3,   // California - highest
  NY: 10.9,   // New York
  NJ: 10.75,  // New Jersey
  PA: 3.07,   // Pennsylvania
  GA: 5.49,   // Georgia
  NC: 4.75,   // North Carolina
  KY: 4.0,    // Kentucky
  MT: 6.75,   // Montana
  ND: 2.9,    // North Dakota
};

/**
 * Bonus depreciation rates by year
 * Phase-out schedule per TCJA
 * @constant {Object}
 */
export const BONUS_DEPRECIATION_RATES = {
  2023: 0.80,  // 80%
  2024: 0.60,  // 60%
  2025: 0.40,  // 40%
  2026: 0.20,  // 20%
  2027: 0.00,  // 0% - fully phased out
};

/**
 * Get the bonus depreciation rate for a given year
 * 
 * @param {number} year - Tax year
 * @returns {number} Bonus depreciation rate (0-1)
 */
export const getBonusDepreciationRate = (year) => {
  if (year <= 2022) return 1.0; // 100% before phase-out
  return BONUS_DEPRECIATION_RATES[year] ?? 0;
};

/**
 * Calculate depreciation for a given year using MACRS
 * 
 * @param {number} assetCost - Original cost of asset
 * @param {number} year - Year of depreciation (1-indexed)
 * @param {boolean} useBonusDepreciation - Whether to use 100% bonus depreciation
 * @param {number[]} [schedule=MACRS_RATES] - Depreciation schedule to use
 * @returns {number} Depreciation amount for the year
 */
export const calculateDepreciation = (assetCost, year, useBonusDepreciation = true, schedule = MACRS_RATES) => {
  if (useBonusDepreciation && year === 1) {
    return assetCost; // 100% bonus depreciation in year 1
  }
  
  if (year < 1 || year > schedule.length) {
    return 0;
  }
  
  return assetCost * schedule[year - 1];
};

/**
 * Calculate total tax liability
 * 
 * @param {number} taxableIncome - Taxable income amount
 * @param {number} federalRate - Federal tax rate (percentage)
 * @param {number} stateRate - State tax rate (percentage)
 * @returns {Object} Tax breakdown
 */
export const calculateTaxLiability = (taxableIncome, federalRate, stateRate) => {
  const federalTax = Math.max(0, taxableIncome) * (federalRate / 100);
  const stateTax = Math.max(0, taxableIncome) * (stateRate / 100);
  
  return {
    federalTax,
    stateTax,
    totalTax: federalTax + stateTax,
    effectiveRate: taxableIncome > 0 ? ((federalTax + stateTax) / taxableIncome) * 100 : 0,
  };
};

