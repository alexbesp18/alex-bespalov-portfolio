/**
 * Risk Metrics and Analysis Calculations
 * 
 * Functions for calculating risk metrics, IRR, breakeven analysis.
 * 
 * @module calculations/risk
 */

import { validateNumber, safeDivide } from '../validation/numbers.js';

/**
 * Calculate Internal Rate of Return (IRR)
 * Uses Newton-Raphson method for approximation
 * 
 * @param {number[]} cashFlows - Array of cash flows (index 0 is initial investment, negative)
 * @param {number} [tolerance=0.0001] - Convergence tolerance
 * @param {number} [maxIterations=100] - Maximum iterations
 * @returns {number} IRR as percentage (e.g., 25 for 25%)
 */
export const calculateIRR = (cashFlows, tolerance = 0.0001, maxIterations = 100) => {
  if (!cashFlows || cashFlows.length < 2) return 0;
  
  // Initial guess
  let rate = 0.1;
  
  for (let i = 0; i < maxIterations; i++) {
    let npv = 0;
    let derivative = 0;
    
    for (let t = 0; t < cashFlows.length; t++) {
      const denominator = Math.pow(1 + rate, t);
      npv += cashFlows[t] / denominator;
      derivative -= (t * cashFlows[t]) / Math.pow(1 + rate, t + 1);
    }
    
    if (Math.abs(npv) < tolerance) {
      return rate * 100; // Convert to percentage
    }
    
    if (Math.abs(derivative) < tolerance) {
      break; // Avoid division by zero
    }
    
    rate = rate - npv / derivative;
    
    // Keep rate in reasonable bounds
    if (rate < -0.99) rate = -0.99;
    if (rate > 10) rate = 10;
  }
  
  return rate * 100;
};

/**
 * Calculate Net Present Value (NPV)
 * 
 * @param {number[]} cashFlows - Array of cash flows
 * @param {number} discountRate - Discount rate as percentage
 * @returns {number} NPV
 */
export const calculateNPV = (cashFlows, discountRate) => {
  if (!cashFlows || cashFlows.length === 0) return 0;
  
  const rate = discountRate / 100;
  
  return cashFlows.reduce((npv, cf, t) => {
    return npv + cf / Math.pow(1 + rate, t);
  }, 0);
};

/**
 * Calculate Sharpe Ratio (simplified for mining context)
 * 
 * @param {number} expectedReturn - Expected return percentage
 * @param {number} riskFreeRate - Risk-free rate percentage
 * @param {number} volatility - Standard deviation of returns percentage
 * @returns {number} Sharpe Ratio
 */
export const calculateSharpeRatio = (expectedReturn, riskFreeRate, volatility) => {
  if (!volatility || volatility === 0) return 0;
  return (expectedReturn - riskFreeRate) / volatility;
};

/**
 * Calculate mining operation risk metrics
 * 
 * @param {Object} params - Mining parameters
 * @param {Object} results - Calculation results
 * @returns {Object} Risk metrics
 */
export const calculateRiskMetrics = (params, results) => {
  const {
    btcPriceStart,
    btcPriceEnd,
    networkHashrateStart,
    networkHashrateEnd,
    electricityRate,
  } = params;
  
  const {
    minerPrice,
    operationalProfit,
    totalBtcMined,
    totalElectricity,
  } = results;
  
  // Price volatility assumption (BTC is highly volatile)
  const priceChange = safeDivide(btcPriceEnd - btcPriceStart, btcPriceStart, 0);
  const priceVolatility = Math.abs(priceChange) * 100;
  
  // Difficulty growth
  const difficultyGrowth = safeDivide(networkHashrateEnd - networkHashrateStart, networkHashrateStart, 0) * 100;
  
  // Breakeven BTC price
  const breakevenBtcPrice = totalBtcMined > 0 
    ? totalElectricity / totalBtcMined 
    : Infinity;
  
  // Margin of safety
  const currentBtcPrice = (btcPriceStart + btcPriceEnd) / 2;
  const marginOfSafety = currentBtcPrice > 0 
    ? ((currentBtcPrice - breakevenBtcPrice) / currentBtcPrice) * 100 
    : 0;
  
  // Risk score (0-100, higher = more risky)
  let riskScore = 0;
  
  // High volatility increases risk
  if (priceVolatility > 50) riskScore += 20;
  else if (priceVolatility > 30) riskScore += 10;
  
  // High difficulty growth increases risk
  if (difficultyGrowth > 30) riskScore += 20;
  else if (difficultyGrowth > 20) riskScore += 10;
  
  // Low margin of safety increases risk
  if (marginOfSafety < 20) riskScore += 30;
  else if (marginOfSafety < 40) riskScore += 15;
  
  // High electricity dependency
  const electricityToRevenue = operationalProfit > 0 
    ? (totalElectricity / (operationalProfit + totalElectricity)) * 100 
    : 100;
  
  if (electricityToRevenue > 70) riskScore += 30;
  else if (electricityToRevenue > 50) riskScore += 15;
  
  return {
    priceVolatility,
    difficultyGrowth,
    breakevenBtcPrice,
    marginOfSafety,
    electricityToRevenue,
    riskScore: Math.min(100, riskScore),
    riskLevel: riskScore > 60 ? 'High' : riskScore > 30 ? 'Medium' : 'Low',
  };
};

/**
 * Calculate sensitivity analysis
 * How profits change with price/difficulty changes
 * 
 * @param {number} baseProfit - Base case profit
 * @param {number} priceChangePercent - Price change percentage
 * @param {number} difficultyChangePercent - Difficulty change percentage
 * @param {number} btcMined - Base BTC mined
 * @param {number} baseBtcPrice - Base BTC price
 * @returns {number} Adjusted profit estimate
 */
export const calculateSensitivity = (
  baseProfit,
  priceChangePercent,
  difficultyChangePercent,
  btcMined,
  baseBtcPrice
) => {
  // Simplified sensitivity calculation
  const priceMultiplier = 1 + (priceChangePercent / 100);
  const difficultyMultiplier = 1 + (difficultyChangePercent / 100);
  
  // Revenue changes with price
  const revenueAdjustment = btcMined * baseBtcPrice * (priceMultiplier - 1);
  
  // BTC mined decreases with difficulty (inverse relationship)
  const btcMinedAdjustment = btcMined * baseBtcPrice * (1 - 1/difficultyMultiplier);
  
  return baseProfit + revenueAdjustment - btcMinedAdjustment;
};

/**
 * Calculate portfolio concentration risk
 * 
 * @param {Object} allocation - Asset allocation percentages
 * @returns {Object} Concentration risk metrics
 */
export const calculateConcentrationRisk = (allocation) => {
  const values = Object.values(allocation).filter(v => v > 0);
  
  if (values.length === 0) {
    return { herfindahl: 0, maxConcentration: 0, diversification: 'N/A' };
  }
  
  // Herfindahl-Hirschman Index (sum of squared market shares)
  const herfindahl = values.reduce((sum, pct) => sum + Math.pow(pct / 100, 2), 0);
  
  // Maximum concentration
  const maxConcentration = Math.max(...values);
  
  // Diversification rating
  let diversification;
  if (herfindahl > 0.5) diversification = 'Poor';
  else if (herfindahl > 0.25) diversification = 'Moderate';
  else if (herfindahl > 0.1) diversification = 'Good';
  else diversification = 'Excellent';
  
  // High concentration assets
  const highConcentration = Object.entries(allocation)
    .filter(([_, pct]) => pct > 25)
    .map(([asset, pct]) => ({ asset, percentage: pct }));
  
  return {
    herfindahl,
    maxConcentration,
    diversification,
    highConcentration,
    assetCount: values.length,
  };
};

/**
 * Calculate quick insights from profit matrix
 * 
 * @param {Array} profitMatrix - Array of miner profit results
 * @param {Array} miners - Array of miner objects
 * @param {number} [referenceRate=0.05] - Reference electricity rate
 * @returns {Object|null} Insights object or null if no data
 */
export const calculateQuickInsights = (profitMatrix, miners, referenceRate = 0.05) => {
  if (!profitMatrix || profitMatrix.length === 0 || !miners || miners.length === 0) {
    return null;
  }
  
  // Find most profitable at reference rate
  const bestProfitMiner = profitMatrix.reduce((best, current) => {
    const currentResult = current.results?.find(r => r.rate === referenceRate);
    const bestResult = best.results?.find(r => r.rate === referenceRate);
    
    if (!currentResult) return best;
    if (!bestResult) return current;
    
    return currentResult.netProfit > bestResult.netProfit ? current : best;
  }, profitMatrix[0]);
  
  // Find most efficient
  const mostEfficient = miners.reduce((best, current) => 
    (current.efficiency || Infinity) < (best.efficiency || Infinity) ? current : best
  , miners[0]);
  
  // Calculate average breakeven electricity rate
  const breakevenRates = profitMatrix.map(row => {
    const profitable = row.results?.filter(r => r.netProfit > 0) || [];
    return profitable.length > 0 ? profitable[profitable.length - 1].rate : null;
  }).filter(rate => rate !== null);
  
  const avgBreakeven = breakevenRates.length > 0 
    ? breakevenRates.reduce((sum, rate) => sum + rate, 0) / breakevenRates.length
    : 0;
  
  const bestResult = bestProfitMiner.results?.find(r => r.rate === referenceRate);
  
  return {
    mostProfitable: bestProfitMiner.miner?.name || 'Unknown',
    mostProfitableROI: bestResult?.roi || 0,
    mostEfficient: mostEfficient.name || 'Unknown',
    mostEfficientValue: mostEfficient.efficiency || 0,
    avgBreakevenElectricity: avgBreakeven,
    totalMiners: miners.length,
  };
};

/**
 * Get cell color class based on value and metric
 * 
 * @param {number} value - The value to color-code
 * @param {string} metric - The metric type ('roi', 'profit', etc.)
 * @returns {string} Tailwind CSS class name
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
 * 
 * @param {Object} result - Result object with various profit metrics
 * @param {string} metric - Metric to display
 * @param {boolean} [isTwoYear=false] - Whether this is a 2-year result
 * @returns {number} The value to display
 */
export const getDisplayValue = (result, metric, isTwoYear = false) => {
  switch (metric) {
    case 'operationalProfit':
      return result.operationalProfit || 0;
    case 'afterTaxProfit':
      return result.afterTaxProfit || 0;
    case 'roi':
      return isTwoYear ? (result.annualizedRoi || 0) : (result.roi || 0);
    case 'netProfit':
    default:
      return result.netProfit || 0;
  }
};

