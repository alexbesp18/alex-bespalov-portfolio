/**
 * useMiningCalculations Hook
 * 
 * React hook for mining profit calculations.
 * Encapsulates all calculation logic with memoization.
 * 
 * @module hooks/useMiningCalculations
 */

import { useMemo, useCallback } from 'react';
import {
  calculateYearlyProfit,
  calculateTwoYearProfit,
  calculateThreeYearProfit,
  getCalculatedEndValues,
  calculateMonthlyDetails,
} from '../calculations/projections.js';
import { calculateMonthlyGrowth } from '../calculations/mining.js';
import { calculateQuickInsights } from '../calculations/risk.js';
import { ELECTRICITY_RATES } from '../constants/electricity.js';

/**
 * Hook for mining calculations
 * 
 * @param {Object[]} miners - Array of miner objects
 * @param {Object} minerPrices - Map of miner ID to price
 * @param {Object} params - Calculation parameters
 * @param {Object} [options={}] - Options
 * @param {boolean} [options.showTwoYearAnalysis=false] - Calculate 2-year projections
 * @param {boolean} [options.showThreeYearAnalysis=false] - Calculate 3-year projections
 * @param {number[]} [options.electricityRates] - Custom electricity rates
 * @returns {Object} Calculation results and helper functions
 * 
 * @example
 * const { profitMatrix, quickInsights, calculateYearly } = useMiningCalculations(
 *   miners,
 *   minerPrices,
 *   params,
 *   { showTwoYearAnalysis: true }
 * );
 */
export const useMiningCalculations = (miners, minerPrices, params, options = {}) => {
  const {
    showTwoYearAnalysis = false,
    showThreeYearAnalysis = false,
    electricityRates = ELECTRICITY_RATES,
  } = options;
  
  // Calculate end values
  const endValues = useMemo(() => {
    return getCalculatedEndValues(params);
  }, [params]);
  
  // Calculate monthly growth
  const monthlyGrowth = useMemo(() => {
    return calculateMonthlyGrowth(params.networkHashrateStart, endValues.networkHashrateEnd);
  }, [params.networkHashrateStart, endValues.networkHashrateEnd]);
  
  // Calculate yearly profit for a miner (memoized callback)
  const calculateYearly = useCallback((miner, electricityRate) => {
    return calculateYearlyProfit(miner, electricityRate, params, minerPrices);
  }, [params, minerPrices]);
  
  // Calculate 2-year profit for a miner
  const calculateTwoYear = useCallback((miner, electricityRate) => {
    return calculateTwoYearProfit(miner, electricityRate, params, minerPrices);
  }, [params, minerPrices]);
  
  // Calculate 3-year profit for a miner
  const calculateThreeYear = useCallback((miner, electricityRate) => {
    return calculateThreeYearProfit(miner, electricityRate, params, minerPrices);
  }, [params, minerPrices]);
  
  // Calculate monthly details for a specific miner and rate
  const calculateDetails = useCallback((miner, electricityRate, year = 1, previousYearEnd = null) => {
    return calculateMonthlyDetails(miner, electricityRate, params, minerPrices, year, previousYearEnd);
  }, [params, minerPrices]);
  
  // Calculate profit matrix for all miners and rates
  const profitMatrix = useMemo(() => {
    if (!miners || miners.length === 0) return [];
    
    return miners.map(miner => ({
      miner,
      results: electricityRates.map(rate => ({
        rate,
        ...calculateYearlyProfit(miner, rate, params, minerPrices),
      })),
    }));
  }, [miners, params, minerPrices, electricityRates]);
  
  // Calculate 2-year profit matrix
  const twoYearProfitMatrix = useMemo(() => {
    if (!showTwoYearAnalysis || !miners || miners.length === 0) return [];
    
    return miners.map(miner => ({
      miner,
      results: electricityRates.map(rate => ({
        rate,
        ...calculateTwoYearProfit(miner, rate, params, minerPrices),
      })),
    }));
  }, [miners, params, minerPrices, showTwoYearAnalysis, electricityRates]);
  
  // Calculate 3-year profit matrix
  const threeYearProfitMatrix = useMemo(() => {
    if (!showThreeYearAnalysis || !miners || miners.length === 0) return [];
    
    return miners.map(miner => ({
      miner,
      results: electricityRates.map(rate => ({
        rate,
        ...calculateThreeYearProfit(miner, rate, params, minerPrices),
      })),
    }));
  }, [miners, params, minerPrices, showThreeYearAnalysis, electricityRates]);
  
  // Calculate quick insights
  const quickInsights = useMemo(() => {
    return calculateQuickInsights(profitMatrix, miners);
  }, [profitMatrix, miners]);
  
  // Find best miner at a specific rate
  const findBestMiner = useCallback((electricityRate, metric = 'netProfit') => {
    if (profitMatrix.length === 0) return null;
    
    return profitMatrix.reduce((best, current) => {
      const currentResult = current.results.find(r => r.rate === electricityRate);
      const bestResult = best.results.find(r => r.rate === electricityRate);
      
      if (!currentResult) return best;
      if (!bestResult) return current;
      
      return (currentResult[metric] || 0) > (bestResult[metric] || 0) ? current : best;
    }, profitMatrix[0]);
  }, [profitMatrix]);
  
  // Get summary statistics
  const summary = useMemo(() => {
    if (profitMatrix.length === 0) {
      return {
        totalMiners: 0,
        profitableAt5c: 0,
        profitableAt10c: 0,
        avgROI: 0,
      };
    }
    
    const profitableAt5c = profitMatrix.filter(row => {
      const result = row.results.find(r => r.rate === 0.05);
      return result && result.netProfit > 0;
    }).length;
    
    const profitableAt10c = profitMatrix.filter(row => {
      const result = row.results.find(r => r.rate === 0.10);
      return result && result.netProfit > 0;
    }).length;
    
    const rois = profitMatrix.map(row => {
      const result = row.results.find(r => r.rate === 0.05);
      return result?.roi || 0;
    });
    
    const avgROI = rois.length > 0 
      ? rois.reduce((sum, roi) => sum + roi, 0) / rois.length 
      : 0;
    
    return {
      totalMiners: miners.length,
      profitableAt5c,
      profitableAt10c,
      avgROI,
    };
  }, [profitMatrix, miners]);
  
  return {
    // Calculated values
    endValues,
    monthlyGrowth,
    profitMatrix,
    twoYearProfitMatrix,
    threeYearProfitMatrix,
    quickInsights,
    summary,
    
    // Helper functions
    calculateYearly,
    calculateTwoYear,
    calculateThreeYear,
    calculateDetails,
    findBestMiner,
    
    // Config
    electricityRates,
  };
};

export default useMiningCalculations;

