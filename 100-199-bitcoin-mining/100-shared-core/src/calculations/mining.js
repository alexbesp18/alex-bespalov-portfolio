/**
 * Core Mining Calculation Functions
 * 
 * Pure calculation functions for Bitcoin mining profitability.
 * All functions are pure (no side effects, deterministic).
 * 
 * @module calculations/mining
 */

import { BLOCK_REWARD, BLOCKS_PER_DAY, DAYS_PER_MONTH, getEffectiveBlockReward } from '../constants/bitcoin.js';
import { validateNumber } from '../validation/numbers.js';

/**
 * Calculate the share of network hashrate for a miner
 * 
 * @param {number} minerHashrateTH - Miner hashrate in TH/s
 * @param {number} networkHashrateEH - Network hashrate in EH/s
 * @returns {number} Share of network (decimal, e.g., 0.000001)
 */
export const calculateNetworkShare = (minerHashrateTH, networkHashrateEH) => {
  if (!networkHashrateEH || networkHashrateEH <= 0) return 0;
  // Convert EH to TH: 1 EH = 1,000,000 TH
  return minerHashrateTH / (networkHashrateEH * 1000000);
};

/**
 * Calculate daily BTC mined by a miner
 * 
 * @param {number} minerHashrateTH - Miner hashrate in TH/s
 * @param {number} networkHashrateEH - Network hashrate in EH/s
 * @param {number} [blockReward=BLOCK_REWARD] - Block reward in BTC
 * @param {number} [uptimePercent=100] - Uptime percentage
 * @returns {number} Daily BTC mined
 */
export const calculateDailyBtcMined = (
  minerHashrateTH, 
  networkHashrateEH, 
  blockReward = BLOCK_REWARD,
  uptimePercent = 100
) => {
  const share = calculateNetworkShare(minerHashrateTH, networkHashrateEH);
  const uptime = validateNumber(uptimePercent, 0, 100) / 100;
  return share * BLOCKS_PER_DAY * blockReward * uptime;
};

/**
 * Calculate monthly BTC mined
 * 
 * @param {number} minerHashrateTH - Miner hashrate in TH/s
 * @param {number} networkHashrateEH - Network hashrate in EH/s
 * @param {number} [blockReward=BLOCK_REWARD] - Block reward
 * @param {number} [uptimePercent=100] - Uptime percentage
 * @returns {number} Monthly BTC mined
 */
export const calculateMonthlyBtcMined = (
  minerHashrateTH, 
  networkHashrateEH, 
  blockReward = BLOCK_REWARD,
  uptimePercent = 100
) => {
  return calculateDailyBtcMined(minerHashrateTH, networkHashrateEH, blockReward, uptimePercent) * DAYS_PER_MONTH;
};

/**
 * Calculate electricity cost for a period
 * 
 * @param {number} powerWatts - Power consumption in watts
 * @param {number} ratePerKwh - Electricity rate in $/kWh
 * @param {number} [hours=24] - Operating hours
 * @returns {number} Electricity cost in USD
 */
export const calculateElectricityCost = (powerWatts, ratePerKwh, hours = 24) => {
  const powerKw = powerWatts / 1000;
  return powerKw * hours * ratePerKwh;
};

/**
 * Calculate monthly electricity cost
 * 
 * @param {number} powerWatts - Power consumption in watts
 * @param {number} ratePerKwh - Electricity rate in $/kWh
 * @returns {number} Monthly electricity cost in USD
 */
export const calculateMonthlyElectricity = (powerWatts, ratePerKwh) => {
  return calculateElectricityCost(powerWatts, ratePerKwh, 24 * DAYS_PER_MONTH);
};

/**
 * Calculate pool fee amount
 * 
 * @param {number} grossRevenue - Gross revenue before fees
 * @param {number} poolFeePercent - Pool fee as percentage
 * @returns {number} Pool fee amount
 */
export const calculatePoolFee = (grossRevenue, poolFeePercent) => {
  return grossRevenue * (validateNumber(poolFeePercent, 0, 100) / 100);
};

/**
 * Calculate monthly mining profit for a single month
 * 
 * @param {Object} miner - Miner object with hashrate and power
 * @param {Object} params - Calculation parameters
 * @param {number} params.btcPrice - Bitcoin price in USD
 * @param {number} params.networkHashrate - Network hashrate in EH/s
 * @param {number} params.electricityRate - Electricity rate in $/kWh
 * @param {number} [params.poolFee=2] - Pool fee percentage
 * @param {number} [params.uptime=100] - Uptime percentage
 * @param {number} [params.blockReward=BLOCK_REWARD] - Block reward
 * @returns {Object} Monthly profit breakdown
 */
export const calculateMonthlyProfit = (miner, params) => {
  const {
    btcPrice,
    networkHashrate,
    electricityRate,
    poolFee = 2,
    uptime = 100,
    blockReward = BLOCK_REWARD,
  } = params;
  
  // Calculate BTC mined
  const btcMined = calculateMonthlyBtcMined(
    miner.hashrate, 
    networkHashrate, 
    blockReward,
    uptime
  );
  
  // Calculate revenue
  const grossRevenue = btcMined * btcPrice;
  const poolFees = calculatePoolFee(grossRevenue, poolFee);
  const netRevenue = grossRevenue - poolFees;
  const btcMinedNet = btcMined * (1 - poolFee / 100);
  
  // Calculate costs
  const electricityCost = calculateMonthlyElectricity(miner.power, electricityRate);
  
  // Calculate profit
  const operationalProfit = netRevenue - electricityCost;
  
  return {
    btcMined,
    btcMinedNet,
    grossRevenue,
    poolFees,
    netRevenue,
    electricityCost,
    operationalProfit,
  };
};

/**
 * Calculate end values based on annual increases or direct values
 * 
 * @param {Object} params - Calculation parameters
 * @param {number} params.btcPriceStart - Starting BTC price
 * @param {number} params.btcPriceEnd - Ending BTC price (if useAnnualIncreases is false)
 * @param {number} params.networkHashrateStart - Starting network hashrate
 * @param {number} params.networkHashrateEnd - Ending network hashrate (if useAnnualIncreases is false)
 * @param {number} [params.annualBtcPriceIncrease] - Annual BTC price increase %
 * @param {number} [params.annualDifficultyIncrease] - Annual difficulty increase %
 * @param {boolean} [params.useAnnualIncreases=false] - Whether to use annual increases
 * @returns {Object} { btcPriceEnd, networkHashrateEnd }
 */
export const getCalculatedEndValues = (params) => {
  if (params.useAnnualIncreases) {
    return {
      btcPriceEnd: params.btcPriceStart * (1 + (params.annualBtcPriceIncrease || 0) / 100),
      networkHashrateEnd: params.networkHashrateStart * (1 + (params.annualDifficultyIncrease || 0) / 100),
    };
  }
  
  return {
    btcPriceEnd: params.btcPriceEnd,
    networkHashrateEnd: params.networkHashrateEnd,
  };
};

/**
 * Calculate monthly growth rate
 * 
 * @param {number} startValue - Starting value
 * @param {number} endValue - Ending value
 * @param {number} [months=12] - Number of months
 * @returns {number} Monthly growth percentage
 */
export const calculateMonthlyGrowth = (startValue, endValue, months = 12) => {
  if (!startValue || startValue === 0) return 0;
  return ((endValue - startValue) / startValue) * 100 / months;
};

/**
 * Calculate annual increases from start/end values
 * 
 * @param {Object} params - Parameters with start/end values
 * @returns {Object} { annualBtcPriceIncrease, annualDifficultyIncrease }
 */
export const calculateAnnualIncreases = (params) => {
  const btcIncrease = ((params.btcPriceEnd - params.btcPriceStart) / params.btcPriceStart) * 100;
  const difficultyIncrease = ((params.networkHashrateEnd - params.networkHashrateStart) / params.networkHashrateStart) * 100;
  
  return {
    annualBtcPriceIncrease: Math.round(btcIncrease * 10) / 10,
    annualDifficultyIncrease: Math.round(difficultyIncrease * 10) / 10,
  };
};

/**
 * Linearly interpolate between two values based on progress
 * 
 * @param {number} start - Start value
 * @param {number} end - End value
 * @param {number} progress - Progress (0-1)
 * @returns {number} Interpolated value
 */
export const interpolateValue = (start, end, progress) => {
  return start + (end - start) * progress;
};

/**
 * Calculate electricity-only cost per BTC mined
 * 
 * @param {number} totalElectricity - Total electricity cost
 * @param {number} totalBtcMined - Total BTC mined
 * @returns {number} Electricity cost per BTC
 */
export const calculateElectricityPerBtc = (totalElectricity, totalBtcMined) => {
  if (!totalBtcMined || totalBtcMined <= 0) return 0;
  return totalElectricity / totalBtcMined;
};

/**
 * Calculate breakeven electricity rate
 * The electricity rate at which profit equals zero
 * 
 * @param {Object} miner - Miner with hashrate and power
 * @param {number} btcPrice - BTC price in USD
 * @param {number} networkHashrate - Network hashrate in EH/s
 * @param {number} [poolFee=2] - Pool fee percentage
 * @returns {number} Breakeven electricity rate in $/kWh
 */
export const calculateBreakevenElectricityRate = (miner, btcPrice, networkHashrate, poolFee = 2) => {
  const monthlyBtc = calculateMonthlyBtcMined(miner.hashrate, networkHashrate);
  const netBtc = monthlyBtc * (1 - poolFee / 100);
  const netRevenue = netBtc * btcPrice;
  
  // Electricity cost = Revenue at breakeven
  // powerKw * 24 * 30.42 * rate = netRevenue
  const hoursPerMonth = 24 * DAYS_PER_MONTH;
  const powerKw = miner.power / 1000;
  
  if (powerKw * hoursPerMonth === 0) return 0;
  
  return netRevenue / (powerKw * hoursPerMonth);
};

/**
 * Calculate breakeven BTC price
 * The BTC price at which profit equals zero
 * 
 * @param {Object} miner - Miner with hashrate and power
 * @param {number} networkHashrate - Network hashrate in EH/s
 * @param {number} electricityRate - Electricity rate in $/kWh
 * @param {number} [poolFee=2] - Pool fee percentage
 * @returns {number} Breakeven BTC price in USD
 */
export const calculateBreakevenBtcPrice = (miner, networkHashrate, electricityRate, poolFee = 2) => {
  const monthlyBtc = calculateMonthlyBtcMined(miner.hashrate, networkHashrate);
  const netBtc = monthlyBtc * (1 - poolFee / 100);
  const electricityCost = calculateMonthlyElectricity(miner.power, electricityRate);
  
  if (!netBtc || netBtc <= 0) return Infinity;
  
  return electricityCost / netBtc;
};

