/**
 * Multi-Year Projection Calculations
 * 
 * Functions for calculating multi-year mining projections.
 * 
 * @module calculations/projections
 */

import { BLOCK_REWARD, DAYS_PER_MONTH, getEffectiveBlockReward, getHalvingInRange } from '../constants/bitcoin.js';
import { MACRS_RATES, calculateDepreciation, calculateTaxLiability } from '../constants/tax.js';
import { 
  calculateMonthlyBtcMined, 
  calculateMonthlyElectricity, 
  calculatePoolFee,
  getCalculatedEndValues,
  interpolateValue 
} from './mining.js';

/**
 * Calculate detailed monthly breakdown for a year
 * 
 * @param {Object} miner - Miner object with hashrate, power
 * @param {number} electricityRate - Electricity rate in $/kWh
 * @param {Object} params - Calculation parameters
 * @param {Object} minerPrices - Map of miner ID to price
 * @param {number} [year=1] - Year number (1, 2, or 3)
 * @param {Object} [previousYearEnd] - End values from previous year
 * @returns {Object} Monthly breakdown and year totals
 */
export const calculateMonthlyDetails = (miner, electricityRate, params, minerPrices, year = 1, previousYearEnd = null) => {
  const { btcPriceEnd, networkHashrateEnd } = getCalculatedEndValues(params);
  const minerPrice = minerPrices?.[miner.id] || miner.defaultPrice || miner.price || 0;
  
  let btcPriceStart = params.btcPriceStart;
  let networkHashrateStart = params.networkHashrateStart;
  let currentBtcPriceEnd = btcPriceEnd;
  let currentNetworkHashrateEnd = networkHashrateEnd;
  
  // For subsequent years, start where previous year ended
  if (year > 1 && previousYearEnd) {
    btcPriceStart = previousYearEnd.btcPriceEnd;
    networkHashrateStart = previousYearEnd.networkHashrateEnd;
    
    if (params.useAnnualIncreases) {
      currentBtcPriceEnd = btcPriceStart * (1 + (params.annualBtcPriceIncrease || 0) / 100);
      currentNetworkHashrateEnd = networkHashrateStart * (1 + (params.annualDifficultyIncrease || 0) / 100);
    } else {
      // Continue the same growth rate
      const btcGrowthRate = btcPriceEnd / params.btcPriceStart;
      const hashrateGrowthRate = networkHashrateEnd / params.networkHashrateStart;
      currentBtcPriceEnd = btcPriceStart * btcGrowthRate;
      currentNetworkHashrateEnd = networkHashrateStart * hashrateGrowthRate;
    }
  }
  
  const monthlyData = [];
  let totalBtcMined = 0;
  let totalRevenue = 0;
  let totalElectricity = 0;
  let totalPoolFees = 0;
  
  for (let month = 0; month < 12; month++) {
    const progress = month / 11; // 0 to 1 over 12 months
    
    const btcPrice = interpolateValue(btcPriceStart, currentBtcPriceEnd, progress);
    const networkHashrate = interpolateValue(networkHashrateStart, currentNetworkHashrateEnd, progress);
    
    const btcPerMonth = calculateMonthlyBtcMined(miner.hashrate, networkHashrate, BLOCK_REWARD, params.uptime || 100);
    const btcMinedNet = btcPerMonth * (1 - (params.poolFee || 2) / 100);
    
    const grossRevenue = btcPerMonth * btcPrice;
    const poolFees = calculatePoolFee(grossRevenue, params.poolFee || 2);
    const netRevenue = grossRevenue - poolFees;
    
    const electricityCost = calculateMonthlyElectricity(miner.power, electricityRate);
    const operationalProfit = netRevenue - electricityCost;
    
    monthlyData.push({
      month: month + 1,
      btcPrice,
      networkHashrate,
      btcMined: btcPerMonth,
      btcMinedNet,
      grossRevenue,
      poolFees,
      netRevenue,
      electricityCost,
      operationalProfit,
    });
    
    totalBtcMined += btcMinedNet;
    totalRevenue += netRevenue;
    totalElectricity += electricityCost;
    totalPoolFees += poolFees;
  }
  
  const totalOperationalProfit = totalRevenue - totalElectricity;
  
  // Calculate depreciation based on year
  const depreciation = calculateDepreciation(minerPrice, year, params.useBonusDepreciation);
  
  // Calculate taxes
  const taxableIncome = Math.max(0, totalOperationalProfit - depreciation);
  const { federalTax, stateTax, totalTax } = calculateTaxLiability(
    taxableIncome, 
    params.taxRate || params.federalTaxRate || 35, 
    params.stateRate || params.stateTaxRate || 0
  );
  
  const afterTaxProfit = totalOperationalProfit - totalTax;
  
  return {
    monthlyData,
    totalBtcMined,
    totalRevenue,
    totalElectricity,
    totalPoolFees,
    totalOperationalProfit,
    depreciation,
    taxableIncome,
    federalTax,
    stateTax,
    totalTax,
    afterTaxProfit,
    minerPrice,
    year,
    endValues: {
      btcPriceEnd: currentBtcPriceEnd,
      networkHashrateEnd: currentNetworkHashrateEnd,
    },
  };
};

/**
 * Calculate yearly profit for a miner (1 year)
 * 
 * @param {Object} miner - Miner object
 * @param {number} electricityRate - Electricity rate in $/kWh
 * @param {Object} params - Calculation parameters
 * @param {Object} minerPrices - Map of miner ID to price
 * @returns {Object} Yearly profit details including ROI
 */
export const calculateYearlyProfit = (miner, electricityRate, params, minerPrices) => {
  const details = calculateMonthlyDetails(miner, electricityRate, params, minerPrices, 1);
  const netProfit = details.afterTaxProfit - details.minerPrice;
  const roi = details.minerPrice > 0 ? (netProfit / details.minerPrice) * 100 : 0;
  
  return {
    ...details,
    netProfit,
    roi,
    electricityOnlyBtcCost: details.totalBtcMined > 0 ? details.totalElectricity / details.totalBtcMined : 0,
  };
};

/**
 * Calculate 2-year cumulative profit
 * 
 * @param {Object} miner - Miner object
 * @param {number} electricityRate - Electricity rate in $/kWh
 * @param {Object} params - Calculation parameters
 * @param {Object} minerPrices - Map of miner ID to price
 * @returns {Object} 2-year profit details
 */
export const calculateTwoYearProfit = (miner, electricityRate, params, minerPrices) => {
  const year1Details = calculateMonthlyDetails(miner, electricityRate, params, minerPrices, 1);
  const year2Details = calculateMonthlyDetails(
    miner,
    electricityRate,
    params,
    minerPrices,
    2,
    year1Details.endValues
  );
  
  const totalBtcMined = year1Details.totalBtcMined + year2Details.totalBtcMined;
  const totalOperationalProfit = year1Details.totalOperationalProfit + year2Details.totalOperationalProfit;
  const totalAfterTaxProfit = year1Details.afterTaxProfit + year2Details.afterTaxProfit;
  const totalNetProfit = totalAfterTaxProfit - year1Details.minerPrice;
  const twoYearRoi = year1Details.minerPrice > 0 ? (totalNetProfit / year1Details.minerPrice) * 100 : 0;
  const annualizedRoi = twoYearRoi / 2;
  
  return {
    year1Details,
    year2Details,
    totalBtcMined,
    operationalProfit: totalOperationalProfit,
    afterTaxProfit: totalAfterTaxProfit,
    netProfit: totalNetProfit,
    roi: twoYearRoi,
    annualizedRoi,
    electricityOnlyBtcCost: totalBtcMined > 0 
      ? (year1Details.totalElectricity + year2Details.totalElectricity) / totalBtcMined 
      : 0,
    minerPrice: year1Details.minerPrice,
  };
};

/**
 * Calculate 3-year cumulative profit
 * 
 * @param {Object} miner - Miner object
 * @param {number} electricityRate - Electricity rate in $/kWh
 * @param {Object} params - Calculation parameters
 * @param {Object} minerPrices - Map of miner ID to price
 * @returns {Object} 3-year profit details
 */
export const calculateThreeYearProfit = (miner, electricityRate, params, minerPrices) => {
  const year1Details = calculateMonthlyDetails(miner, electricityRate, params, minerPrices, 1);
  const year2Details = calculateMonthlyDetails(miner, electricityRate, params, minerPrices, 2, year1Details.endValues);
  const year3Details = calculateMonthlyDetails(miner, electricityRate, params, minerPrices, 3, year2Details.endValues);
  
  const totalBtcMined = year1Details.totalBtcMined + year2Details.totalBtcMined + year3Details.totalBtcMined;
  const totalOperationalProfit = year1Details.totalOperationalProfit + year2Details.totalOperationalProfit + year3Details.totalOperationalProfit;
  const totalAfterTaxProfit = year1Details.afterTaxProfit + year2Details.afterTaxProfit + year3Details.afterTaxProfit;
  const totalNetProfit = totalAfterTaxProfit - year1Details.minerPrice;
  const threeYearRoi = year1Details.minerPrice > 0 ? (totalNetProfit / year1Details.minerPrice) * 100 : 0;
  const annualizedRoi = threeYearRoi / 3;
  
  return {
    year1Details,
    year2Details,
    year3Details,
    totalBtcMined,
    operationalProfit: totalOperationalProfit,
    afterTaxProfit: totalAfterTaxProfit,
    netProfit: totalNetProfit,
    roi: threeYearRoi,
    annualizedRoi,
    minerPrice: year1Details.minerPrice,
  };
};

/**
 * Calculate multi-year projection with flexible year count
 * 
 * @param {Object} miner - Miner object
 * @param {number} electricityRate - Electricity rate in $/kWh
 * @param {Object} params - Calculation parameters
 * @param {Object} minerPrices - Map of miner ID to price
 * @param {number} [years=3] - Number of years to project
 * @returns {Object} Multi-year projection details
 */
export const calculateMultiYearProjection = (miner, electricityRate, params, minerPrices, years = 3) => {
  const yearlyDetails = [];
  let previousEndValues = null;
  
  for (let year = 1; year <= years; year++) {
    const details = calculateMonthlyDetails(
      miner, 
      electricityRate, 
      params, 
      minerPrices, 
      year, 
      previousEndValues
    );
    yearlyDetails.push(details);
    previousEndValues = details.endValues;
  }
  
  const minerPrice = yearlyDetails[0]?.minerPrice || 0;
  const totalBtcMined = yearlyDetails.reduce((sum, y) => sum + y.totalBtcMined, 0);
  const totalOperationalProfit = yearlyDetails.reduce((sum, y) => sum + y.totalOperationalProfit, 0);
  const totalAfterTaxProfit = yearlyDetails.reduce((sum, y) => sum + y.afterTaxProfit, 0);
  const totalNetProfit = totalAfterTaxProfit - minerPrice;
  const totalRoi = minerPrice > 0 ? (totalNetProfit / minerPrice) * 100 : 0;
  
  return {
    yearlyDetails,
    totalBtcMined,
    operationalProfit: totalOperationalProfit,
    afterTaxProfit: totalAfterTaxProfit,
    netProfit: totalNetProfit,
    roi: totalRoi,
    annualizedRoi: totalRoi / years,
    minerPrice,
    years,
  };
};

/**
 * Calculate payback period in months
 * 
 * @param {Object} miner - Miner object
 * @param {number} electricityRate - Electricity rate
 * @param {Object} params - Calculation parameters
 * @param {Object} minerPrices - Miner prices map
 * @returns {number} Payback period in months (Infinity if never pays back)
 */
export const calculatePaybackPeriod = (miner, electricityRate, params, minerPrices) => {
  const projection = calculateMultiYearProjection(miner, electricityRate, params, minerPrices, 5);
  
  let cumulativeProfit = -projection.minerPrice;
  let month = 0;
  
  for (const year of projection.yearlyDetails) {
    for (const monthData of year.monthlyData) {
      cumulativeProfit += monthData.operationalProfit;
      month++;
      
      if (cumulativeProfit >= 0) {
        return month;
      }
    }
  }
  
  return Infinity;
};

