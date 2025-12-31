/**
 * Custom hook for profit matrix calculations with loading state
 * This is a wrapper around useMiningCalculations that adds loading state management
 */

import { useState, useMemo } from 'react';
import { useMiningCalculations } from './useMiningCalculations';

export const useProfitMatrix = (miners, minerPrices, params, showTwoYearAnalysis) => {
  const [isCalculating, setIsCalculating] = useState(false);

  const calculations = useMiningCalculations(miners, minerPrices, params, showTwoYearAnalysis);

  // Wrap profit matrix calculation with loading state
  const profitMatrix = useMemo(() => {
    setIsCalculating(true);
    const matrix = calculations.profitMatrix;
    // Use setTimeout to allow UI to update
    setTimeout(() => setIsCalculating(false), 0);
    return matrix;
  }, [calculations.profitMatrix]);

  return {
    ...calculations,
    profitMatrix,
    isCalculating
  };
};
