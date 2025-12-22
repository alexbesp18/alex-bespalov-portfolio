/**
 * Tax and Depreciation Calculations
 * 
 * Functions for calculating taxes and depreciation for mining operations.
 * 
 * @module calculations/taxes
 */

import { MACRS_RATES, calculateDepreciation as baseCalculateDepreciation } from '../constants/tax.js';

// Re-export from constants for convenience
export { MACRS_RATES, calculateDepreciation as calculateYearlyDepreciation } from '../constants/tax.js';

/**
 * Calculate complete depreciation schedule
 * 
 * @param {number} assetCost - Cost of the asset
 * @param {boolean} [useBonusDepreciation=true] - Use 100% bonus depreciation
 * @returns {Object[]} Depreciation schedule by year
 */
export const calculateDepreciationSchedule = (assetCost, useBonusDepreciation = true) => {
  const schedule = [];
  let remainingBasis = assetCost;
  
  if (useBonusDepreciation) {
    schedule.push({
      year: 1,
      depreciation: assetCost,
      remainingBasis: 0,
      rate: 1.0,
    });
    return schedule;
  }
  
  for (let i = 0; i < MACRS_RATES.length; i++) {
    const depreciation = assetCost * MACRS_RATES[i];
    remainingBasis -= depreciation;
    
    schedule.push({
      year: i + 1,
      depreciation,
      remainingBasis: Math.max(0, remainingBasis),
      rate: MACRS_RATES[i],
    });
  }
  
  return schedule;
};

/**
 * Calculate taxable mining income
 * 
 * @param {number} operationalProfit - Pre-tax operational profit
 * @param {number} depreciation - Depreciation amount
 * @param {number} [otherDeductions=0] - Other business deductions
 * @returns {number} Taxable income (minimum 0)
 */
export const calculateTaxableIncome = (operationalProfit, depreciation, otherDeductions = 0) => {
  return Math.max(0, operationalProfit - depreciation - otherDeductions);
};

/**
 * Calculate mining tax liability with full breakdown
 * 
 * @param {Object} income - Income breakdown
 * @param {number} income.operationalProfit - Pre-tax operational profit
 * @param {number} income.depreciation - Depreciation amount
 * @param {Object} rates - Tax rates
 * @param {number} rates.federal - Federal tax rate (%)
 * @param {number} rates.state - State tax rate (%)
 * @returns {Object} Complete tax breakdown
 */
export const calculateMiningTax = (income, rates) => {
  const { operationalProfit, depreciation } = income;
  const { federal = 35, state = 0 } = rates;
  
  const taxableIncome = calculateTaxableIncome(operationalProfit, depreciation);
  
  const federalTax = taxableIncome * (federal / 100);
  const stateTax = taxableIncome * (state / 100);
  const totalTax = federalTax + stateTax;
  
  const afterTaxProfit = operationalProfit - totalTax;
  const effectiveRate = operationalProfit > 0 ? (totalTax / operationalProfit) * 100 : 0;
  
  // Tax savings from depreciation
  const taxSavings = depreciation * ((federal + state) / 100);
  
  return {
    operationalProfit,
    depreciation,
    taxableIncome,
    federalTax,
    stateTax,
    totalTax,
    afterTaxProfit,
    effectiveRate,
    taxSavings,
  };
};

/**
 * Calculate after-tax profit with equipment purchase
 * 
 * @param {number} operationalProfit - Operational profit
 * @param {number} equipmentCost - Cost of equipment
 * @param {number} year - Year number (affects depreciation)
 * @param {Object} rates - Tax rates { federal, state }
 * @param {boolean} [useBonusDepreciation=true] - Use bonus depreciation
 * @returns {Object} After-tax calculation
 */
export const calculateAfterTaxWithEquipment = (
  operationalProfit, 
  equipmentCost, 
  year, 
  rates,
  useBonusDepreciation = true
) => {
  const depreciation = baseCalculateDepreciation(equipmentCost, year, useBonusDepreciation);
  
  const taxResult = calculateMiningTax(
    { operationalProfit, depreciation },
    rates
  );
  
  // Net profit accounts for equipment cost in year 1
  const netProfit = year === 1 
    ? taxResult.afterTaxProfit - equipmentCost 
    : taxResult.afterTaxProfit;
  
  return {
    ...taxResult,
    equipmentCost: year === 1 ? equipmentCost : 0,
    netProfit,
    roi: equipmentCost > 0 ? (netProfit / equipmentCost) * 100 : 0,
  };
};

/**
 * Calculate maximum equipment price for target profit
 * Used in acquisition price calculator
 * 
 * @param {number} operationalProfit - Expected operational profit
 * @param {number} targetProfit - Target after-tax profit
 * @param {Object} rates - Tax rates { federal, state }
 * @returns {number} Maximum acquisition price
 */
export const calculateMaxAcquisitionPrice = (operationalProfit, targetProfit, rates) => {
  const { federal = 35, state = 0 } = rates;
  const totalTaxRate = (federal + state) / 100;
  
  if (totalTaxRate === 0) {
    // No taxes, equipment price = operational profit - target profit
    return Math.max(0, operationalProfit - targetProfit);
  }
  
  // With 100% bonus depreciation:
  // Target = OpProfit - max(0, (OpProfit - EquipPrice) * TaxRate)
  // If OpProfit > EquipPrice (normal case):
  // Target = OpProfit - (OpProfit - EquipPrice) * TaxRate
  // Target = OpProfit * (1 - TaxRate) + EquipPrice * TaxRate
  // EquipPrice = (Target - OpProfit * (1 - TaxRate)) / TaxRate
  
  const acquisitionPrice = (targetProfit - operationalProfit * (1 - totalTaxRate)) / totalTaxRate;
  
  // Clamp to valid range
  if (acquisitionPrice < 0) {
    // Operational profit too low for target profit with taxes
    return Math.max(0, operationalProfit - targetProfit);
  }
  
  if (acquisitionPrice > operationalProfit) {
    // Equipment cost exceeds operational profit (no taxes owed)
    return Math.max(0, operationalProfit - targetProfit);
  }
  
  return Math.max(0, acquisitionPrice);
};

/**
 * Estimate quarterly tax payments
 * 
 * @param {number} annualTax - Estimated annual tax
 * @returns {Object} Quarterly payment schedule
 */
export const calculateQuarterlyPayments = (annualTax) => {
  const quarterlyAmount = annualTax / 4;
  
  return {
    q1: { dueDate: 'April 15', amount: quarterlyAmount },
    q2: { dueDate: 'June 15', amount: quarterlyAmount },
    q3: { dueDate: 'September 15', amount: quarterlyAmount },
    q4: { dueDate: 'January 15', amount: quarterlyAmount },
    total: annualTax,
  };
};

