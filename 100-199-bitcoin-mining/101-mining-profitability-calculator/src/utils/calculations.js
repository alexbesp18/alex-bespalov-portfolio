/**
 * Pure calculation functions for Bitcoin mining profitability
 * All functions are pure (no side effects, deterministic)
 */

import {
  BLOCK_REWARD,
  BLOCKS_PER_DAY,
  MACRS_RATES
} from './constants';

/**
 * Calculate end values based on annual increases or use direct values
 * @param {Object} params - Calculation parameters
 * @returns {Object} - { btcPriceEnd, networkHashrateEnd }
 */
export const getCalculatedEndValues = (params) => {
  if (params.useAnnualIncreases) {
    return {
      btcPriceEnd: params.btcPriceStart * (1 + params.annualBtcPriceIncrease / 100),
      networkHashrateEnd: params.networkHashrateStart * (1 + params.annualDifficultyIncrease / 100)
    };
  }
  return {
    btcPriceEnd: params.btcPriceEnd,
    networkHashrateEnd: params.networkHashrateEnd
  };
};

/**
 * Calculate monthly mining details for a given year
 * @param {Object} miner - Miner object with hashrate, power, etc.
 * @param {number} electricityRate - Electricity rate in $/kWh
 * @param {Object} params - Calculation parameters
 * @param {Object} minerPrices - Map of miner ID to price
 * @param {number} year - Year number (1 or 2)
 * @param {Object} previousYearEnd - End values from previous year (for year 2)
 * @returns {Object} - Monthly breakdown and totals
 */
export const calculateMonthlyDetails = (miner, electricityRate, params, minerPrices, year = 1, previousYearEnd = null) => {
  const { btcPriceEnd, networkHashrateEnd } = getCalculatedEndValues(params);
  const minerPrice = minerPrices[miner.id] || miner.defaultPrice;
  
  let btcPriceStart = params.btcPriceStart;
  let networkHashrateStart = params.networkHashrateStart;
  let currentBtcPriceEnd = btcPriceEnd;
  let currentNetworkHashrateEnd = networkHashrateEnd;
  
  // For year 2, start where year 1 ended
  if (year === 2 && previousYearEnd) {
    btcPriceStart = previousYearEnd.btcPriceEnd;
    networkHashrateStart = previousYearEnd.networkHashrateEnd;
    
    if (params.useAnnualIncreases) {
      currentBtcPriceEnd = btcPriceStart * (1 + params.annualBtcPriceIncrease / 100);
      currentNetworkHashrateEnd = networkHashrateStart * (1 + params.annualDifficultyIncrease / 100);
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
    const progress = month / 11;
    
    const btcPrice = btcPriceStart + (currentBtcPriceEnd - btcPriceStart) * progress;
    const networkHashrate = networkHashrateStart + (currentNetworkHashrateEnd - networkHashrateStart) * progress;
    
    const minerHashrateTH = miner.hashrate;
    const networkHashrateEH = networkHashrate;
    const shareOfNetwork = minerHashrateTH / (networkHashrateEH * 1000000);
    
    const btcPerDay = shareOfNetwork * BLOCKS_PER_DAY * BLOCK_REWARD;
    const btcPerMonth = btcPerDay * 30.42;
    
    const grossRevenue = btcPerMonth * btcPrice;
    const poolFees = grossRevenue * (params.poolFee / 100);
    const netRevenue = grossRevenue - poolFees;
    
    const powerKw = miner.power / 1000;
    const electricityCost = powerKw * 24 * 30.42 * electricityRate;
    
    const operationalProfit = netRevenue - electricityCost;
    
    monthlyData.push({
      month: month + 1,
      btcPrice,
      networkHashrate,
      btcMined: btcPerMonth,
      btcMinedNet: btcPerMonth * (1 - params.poolFee / 100),
      grossRevenue,
      poolFees,
      netRevenue,
      electricityCost,
      operationalProfit
    });
    
    totalBtcMined += btcPerMonth * (1 - params.poolFee / 100);
    totalRevenue += netRevenue;
    totalElectricity += electricityCost;
    totalPoolFees += poolFees;
  }
  
  const totalOperationalProfit = totalRevenue - totalElectricity;
  
  // Calculate depreciation based on year
  let depreciation = 0;
  if (params.useBonusDepreciation && year === 1) {
    depreciation = minerPrice;
  } else if (!params.useBonusDepreciation && year <= MACRS_RATES.length) {
    depreciation = minerPrice * MACRS_RATES[year - 1];
  }
  
  // Calculate taxes
  const taxableIncome = Math.max(0, totalOperationalProfit - depreciation);
  const federalTax = taxableIncome * (params.taxRate / 100);
  const stateTax = taxableIncome * (params.stateRate / 100);
  const totalTax = federalTax + stateTax;
  
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
      networkHashrateEnd: currentNetworkHashrateEnd
    }
  };
};

/**
 * Calculate yearly profit for a miner
 * @param {Object} miner - Miner object
 * @param {number} electricityRate - Electricity rate in $/kWh
 * @param {Object} params - Calculation parameters
 * @param {Object} minerPrices - Map of miner ID to price
 * @returns {Object} - Yearly profit details including ROI
 */
export const calculateYearlyProfit = (miner, electricityRate, params, minerPrices) => {
  const details = calculateMonthlyDetails(miner, electricityRate, params, minerPrices, 1);
  const netProfit = details.afterTaxProfit - details.minerPrice;
  const roi = details.minerPrice > 0 ? (netProfit / details.minerPrice) * 100 : 0;
  
  return {
    ...details,
    netProfit,
    roi,
    electricityOnlyBtcCost: details.totalBtcMined > 0 ? details.totalElectricity / details.totalBtcMined : 0
  };
};

/**
 * Calculate 2-year cumulative profit
 * @param {Object} miner - Miner object
 * @param {number} electricityRate - Electricity rate in $/kWh
 * @param {Object} params - Calculation parameters
 * @param {Object} minerPrices - Map of miner ID to price
 * @returns {Object} - 2-year profit details
 */
export const calculateTwoYearProfit = (miner, electricityRate, params, minerPrices) => {
  const year1Details = calculateMonthlyDetails(miner, electricityRate, params, minerPrices, 1);
  const year2Details = calculateMonthlyDetails(
    miner,
    electricityRate,
    params,
    minerPrices,
    2,
    { btcPriceEnd: year1Details.endValues.btcPriceEnd, networkHashrateEnd: year1Details.endValues.networkHashrateEnd }
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
    minerPrice: year1Details.minerPrice
  };
};

/**
 * Get cell color class based on value and metric type
 * @param {number} value - The value to color-code
 * @param {string} metric - The metric type ('roi' or other)
 * @returns {string} - Tailwind CSS class name
 */
export const getCellColor = (value, metric) => {
  if (metric === 'roi') {
    if (value > 50) return 'bg-green-300';
    if (value > 25) return 'bg-green-200';
    if (value > 10) return 'bg-green-100';
    if (value > 0) return 'bg-green-50';
    if (value > -25) return 'bg-red-50';
    if (value > -50) return 'bg-red-100';
    return 'bg-red-200';
  } else {
    if (value > 20000) return 'bg-green-300';
    if (value > 10000) return 'bg-green-200';
    if (value > 5000) return 'bg-green-100';
    if (value > 0) return 'bg-green-50';
    if (value > -5000) return 'bg-red-50';
    if (value > -10000) return 'bg-red-100';
    return 'bg-red-200';
  }
};

/**
 * Get display value based on metric type
 * @param {Object} result - Result object with various profit metrics
 * @param {string} metric - Metric to display ('netProfit', 'afterTaxProfit', 'operationalProfit', 'roi')
 * @param {boolean} isTwoYear - Whether this is a 2-year result
 * @returns {number} - The value to display
 */
export const getDisplayValue = (result, metric, isTwoYear = false) => {
  switch (metric) {
    case 'operationalProfit':
      return result.operationalProfit;
    case 'afterTaxProfit':
      return result.afterTaxProfit;
    case 'roi':
      return isTwoYear ? result.annualizedRoi : result.roi;
    default:
      return result.netProfit;
  }
};

/**
 * Calculate quick insights from profit matrix
 * @param {Array} profitMatrix - Array of miner profit results
 * @param {Array} miners - Array of miner objects
 * @returns {Object|null} - Insights object or null if no data
 */
export const calculateQuickInsights = (profitMatrix, miners) => {
  if (!profitMatrix || profitMatrix.length === 0) return null;
  
  // Find most profitable at $0.05/kWh
  const bestProfitMiner = profitMatrix.reduce((best, current) => {
    const currentBest = current.results.find(r => r.rate === 0.05);
    const prevBest = best.results.find(r => r.rate === 0.05);
    return currentBest.netProfit > prevBest.netProfit ? current : best;
  });
  
  // Find most efficient
  const mostEfficient = miners.reduce((best, current) => 
    current.efficiency < best.efficiency ? current : best
  );
  
  // Calculate average breakeven price
  const breakevenPrices = profitMatrix.map(row => {
    const profitable = row.results.filter(r => r.netProfit > 0);
    return profitable.length > 0 ? profitable[profitable.length - 1].rate : null;
  }).filter(price => price !== null);
  
  const avgBreakeven = breakevenPrices.length > 0 
    ? (breakevenPrices.reduce((sum, price) => sum + price, 0) / breakevenPrices.length)
    : 0;
  
  return {
    mostProfitable: bestProfitMiner.miner.name,
    mostProfitableROI: bestProfitMiner.results.find(r => r.rate === 0.05).roi,
    mostEfficient: mostEfficient.name,
    mostEfficientValue: mostEfficient.efficiency,
    avgBreakevenElectricity: avgBreakeven
  };
};

/**
 * Calculate monthly growth rate for network hashrate
 * @param {number} startHashrate - Starting network hashrate
 * @param {number} endHashrate - Ending network hashrate
 * @returns {number} - Monthly growth percentage
 */
export const calculateMonthlyGrowth = (startHashrate, endHashrate) => {
  return ((endHashrate - startHashrate) / startHashrate) * 100 / 12;
};

/**
 * Calculate annual increases from start/end values
 * @param {Object} params - Parameters with start/end values
 * @returns {Object} - { annualBtcPriceIncrease, annualDifficultyIncrease }
 */
export const calculateAnnualIncreases = (params) => {
  const btcIncrease = ((params.btcPriceEnd - params.btcPriceStart) / params.btcPriceStart) * 100;
  const difficultyIncrease = ((params.networkHashrateEnd - params.networkHashrateStart) / params.networkHashrateStart) * 100;
  
  return {
    annualBtcPriceIncrease: Math.round(btcIncrease * 10) / 10,
    annualDifficultyIncrease: Math.round(difficultyIncrease * 10) / 10
  };
};
