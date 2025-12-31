/**
 * Custom hook for mining calculations
 * Encapsulates all calculation logic
 */

import { useMemo, useCallback } from 'react';
import {
  calculateYearlyProfit,
  calculateTwoYearProfit,
  calculateQuickInsights,
  getCalculatedEndValues,
  calculateMonthlyGrowth
} from '../utils/calculations';
import { ELECTRICITY_RATES } from '../utils/constants';

export const useMiningCalculations = (miners, minerPrices, params, showTwoYearAnalysis) => {
  // Calculate end values
  const endValues = useMemo(() => {
    return getCalculatedEndValues(params);
  }, [params]);

  // Calculate monthly growth
  const monthlyGrowth = useMemo(() => {
    return calculateMonthlyGrowth(params.networkHashrateStart, endValues.networkHashrateEnd);
  }, [params.networkHashrateStart, endValues.networkHashrateEnd]);

  // Calculate yearly profit for a miner
  const calculateYearly = useCallback((miner, electricityRate) => {
    return calculateYearlyProfit(miner, electricityRate, params, minerPrices);
  }, [params, minerPrices]);

  // Calculate 2-year profit for a miner
  const calculateTwoYear = useCallback((miner, electricityRate) => {
    return calculateTwoYearProfit(miner, electricityRate, params, minerPrices);
  }, [params, minerPrices]);

  // Calculate profit matrix
  const profitMatrix = useMemo(() => {
    const matrix = [];
    
    for (const miner of miners) {
      const row = {
        miner: miner,
        results: []
      };
      
      for (const rate of ELECTRICITY_RATES) {
        const result = calculateYearlyProfit(miner, rate, params, minerPrices);
        row.results.push({
          rate,
          ...result
        });
      }
      
      matrix.push(row);
    }
    
    return matrix;
  }, [params, minerPrices, miners]);

  // Calculate 2-year profit matrix
  const twoYearProfitMatrix = useMemo(() => {
    if (!showTwoYearAnalysis) return [];
    
    const matrix = [];
    
    for (const miner of miners) {
      const row = {
        miner: miner,
        results: []
      };
      
      for (const rate of ELECTRICITY_RATES) {
        const result = calculateTwoYearProfit(miner, rate, params, minerPrices);
        row.results.push({
          rate,
          ...result
        });
      }
      
      matrix.push(row);
    }
    
    return matrix;
  }, [params, minerPrices, showTwoYearAnalysis, miners]);

  // Calculate quick insights
  const quickInsights = useMemo(() => {
    return calculateQuickInsights(profitMatrix, miners);
  }, [profitMatrix, miners]);

  return {
    endValues,
    monthlyGrowth,
    calculateYearly,
    calculateTwoYear,
    profitMatrix,
    twoYearProfitMatrix,
    quickInsights
  };
};
