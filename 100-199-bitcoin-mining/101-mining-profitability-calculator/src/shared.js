/**
 * Shared Core Bridge
 * 
 * Re-exports from @btc-mining/shared-core for use in this project.
 * This file serves as the integration point with the shared-core library.
 */

// Constants
export {
  BLOCK_REWARD,
  BLOCKS_PER_DAY,
  DAYS_PER_YEAR,
  DAYS_PER_MONTH,
  getEffectiveBlockReward,
  HALVING_DATES,
} from '@btc-mining/shared-core';

export {
  MACRS_RATES,
  calculateDepreciation,
  calculateTaxLiability,
} from '@btc-mining/shared-core';

export {
  ELECTRICITY_RATES,
  ELECTRICITY_RATES_EXTENDED,
  ELECTRICITY_PRESETS,
  calculateMonthlyElectricityCost,
  calculateAnnualElectricityCost,
} from '@btc-mining/shared-core';

export {
  DEFAULT_PARAMS,
  STORAGE_KEYS,
  createParams,
  validateParams,
} from '@btc-mining/shared-core';

// Data
export {
  MINER_DATABASE,
  getAllMiners,
  getMinerById,
  getMinersBy,
  calculateEfficiency,
} from '@btc-mining/shared-core';

export {
  PRESET_SCENARIOS,
  getScenario,
  getScenarioKeys,
  createScenario,
  calculateGrowthRates,
  calculateEndValues,
} from '@btc-mining/shared-core';

// Calculations
export {
  calculateNetworkShare,
  calculateDailyBtcMined,
  calculateMonthlyBtcMined,
  calculateElectricityCost,
  calculateMonthlyElectricity,
  calculatePoolFee,
  calculateMonthlyProfit,
  getCalculatedEndValues,
  calculateMonthlyGrowth,
  calculateAnnualIncreases,
  calculateBreakevenElectricityRate,
  calculateBreakevenBtcPrice,
  interpolateValue,
} from '@btc-mining/shared-core';

export {
  calculateMonthlyDetails,
  calculateYearlyProfit,
  calculateTwoYearProfit,
  calculateThreeYearProfit,
  calculateMultiYearProjection,
  calculatePaybackPeriod,
} from '@btc-mining/shared-core';

export {
  calculateMiningTax,
  calculateAfterTaxWithEquipment,
  calculateDepreciationSchedule,
  calculateMaxAcquisitionPrice,
} from '@btc-mining/shared-core';

export {
  calculateIRR,
  calculateNPV,
  calculateRiskMetrics,
  calculateQuickInsights,
  getCellColor,
  getDisplayValue,
} from '@btc-mining/shared-core';

// Formatters
export {
  formatCurrency,
  formatBTC,
  formatElectricityRate,
  formatElectricityRateWithUnit,
  formatPrice,
} from '@btc-mining/shared-core';

export {
  formatNumber,
  formatPercentage,
  formatDecimalAsPercentage,
  formatHashrate,
  formatPower,
  formatEfficiency,
  formatCompact,
} from '@btc-mining/shared-core';

export {
  formatDate,
  formatDateHuman,
  formatDateTime,
  formatRelativeTime,
} from '@btc-mining/shared-core';

// Validation
export {
  validateNumber,
  validatePositive,
  validatePercentage,
  isValidNumber,
  isPositiveNumber,
  roundTo,
  clamp,
  safeDivide,
  parseNumeric,
} from '@btc-mining/shared-core';

export {
  validateMiner,
  sanitizeMiner,
  validateMiners,
  isSameMiner,
  mergeMinerData,
} from '@btc-mining/shared-core';

// Storage
export {
  createStorageManager,
  isLocalStorageAvailable,
  safeJSONParse,
  safeJSONStringify,
} from '@btc-mining/shared-core';

export {
  compressData,
  decompressData,
  smartCompress,
  smartDecompress,
} from '@btc-mining/shared-core';

// Export
export {
  exportToJSON,
  importFromJSON,
  createJSONImportHandler,
  createExportFilename,
} from '@btc-mining/shared-core';

export {
  exportToCSV,
  importFromCSV,
  parseCSV,
} from '@btc-mining/shared-core';

// Hooks
export {
  useLocalStorage,
  useLocalStorageObject,
} from '@btc-mining/shared-core';

export {
  useMiningCalculations,
} from '@btc-mining/shared-core';

export {
  useScenarios,
} from '@btc-mining/shared-core';

/**
 * Default preset miners (re-exported from shared-core database)
 * This provides backward compatibility with existing code.
 */
export const DEFAULT_PRESET_MINERS = [
  { id: 1, name: "S21 XP+ Hyd", fullName: "Bitmain Antminer S21 XP+ Hyd", hashrate: 500, power: 5500, efficiency: 11, defaultPrice: 14530, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2024, series: "S21" },
  { id: 2, name: "S21 XP Hyd", fullName: "Bitmain Antminer S21 XP Hyd", hashrate: 473, power: 5676, efficiency: 12, defaultPrice: 10800, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2024, series: "S21" },
  { id: 3, name: "S21e XP Hyd 3U", fullName: "Bitmain Antminer S21e XP Hyd 3U", hashrate: 860, power: 11180, efficiency: 13, defaultPrice: 19450, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2024, series: "S21" },
  { id: 4, name: "S21 XP", fullName: "Bitmain Antminer S21 XP", hashrate: 270, power: 3645, efficiency: 13.5, defaultPrice: 6833, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
  { id: 5, name: "S21+ Hyd", fullName: "Bitmain Antminer S21+ Hyd", hashrate: 319, power: 4785, efficiency: 15, defaultPrice: 5780, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2024, series: "S21" },
  { id: 6, name: "S21+ Hyd 338", fullName: "Bitmain Antminer S21+ Hyd 338", hashrate: 338, power: 5070, efficiency: 15.0, defaultPrice: 5780, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2024, series: "S21" },
  { id: 7, name: "S21 Pro", fullName: "Bitmain Antminer S21 Pro", hashrate: 234, power: 3510, efficiency: 15, defaultPrice: 4271, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
  { id: 8, name: "S21 Pro 245", fullName: "Bitmain Antminer S21 Pro 245", hashrate: 245, power: 3675, efficiency: 15.0, defaultPrice: 4393, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
  { id: 9, name: "S21 Pro 220", fullName: "Bitmain Antminer S21 Pro 220", hashrate: 220, power: 3300, efficiency: 15.0, defaultPrice: 4648, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
  { id: 10, name: "S21 Hyd", fullName: "Bitmain Antminer S21 Hyd", hashrate: 335, power: 5360, efficiency: 16, defaultPrice: 5863, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2024, series: "S21" },
  { id: 11, name: "S21+", fullName: "Bitmain Antminer S21+", hashrate: 216, power: 3564, efficiency: 16.5, defaultPrice: 3251, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
  { id: 12, name: "S21+ 225", fullName: "Bitmain Antminer S21+ 225", hashrate: 225, power: 3712, efficiency: 16.5, defaultPrice: 3337, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
  { id: 13, name: "S21+ 235", fullName: "Bitmain Antminer S21+ 235", hashrate: 235, power: 3878, efficiency: 16.5, defaultPrice: 3511, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
  { id: 14, name: "S21e Hyd", fullName: "Bitmain Antminer S21e Hyd", hashrate: 288, power: 4896, efficiency: 17.0, defaultPrice: 3887, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2024, series: "S21" },
  { id: 15, name: "S21", fullName: "Bitmain Antminer S21", hashrate: 200, power: 3500, efficiency: 17.5, defaultPrice: 4830, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
  { id: 16, name: "S21 188", fullName: "Bitmain Antminer S21 188", hashrate: 188, power: 3290, efficiency: 17.5, defaultPrice: 4457, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
  { id: 17, name: "S21 Immersion", fullName: "Bitmain Antminer S21 Immersion", hashrate: 301, power: 5569, efficiency: 18.5, defaultPrice: 6318, manufacturer: "Bitmain", coolingType: "Immersion", releaseYear: 2024, series: "S21" },
  { id: 18, name: "S21 Immersion 302", fullName: "Bitmain Antminer S21 Immersion 302", hashrate: 302, power: 5587, efficiency: 18.5, defaultPrice: 5863, manufacturer: "Bitmain", coolingType: "Immersion", releaseYear: 2024, series: "S21" },
  { id: 19, name: "S19 XP+ Hyd", fullName: "Bitmain Antminer S19 XP+ Hyd", hashrate: 279, power: 5301, efficiency: 19, defaultPrice: 3181, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2023, series: "S19" },
  { id: 20, name: "S19 XP Hyd 257", fullName: "Bitmain Antminer S19 XP Hydro 257", hashrate: 257, power: 5418, efficiency: 21.1, defaultPrice: 2360, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2023, series: "S19" }
];

