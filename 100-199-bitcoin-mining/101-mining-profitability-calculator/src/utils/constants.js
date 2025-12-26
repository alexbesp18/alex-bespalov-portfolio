/**
 * Constants for Bitcoin Mining Calculator
 * All hardcoded values and configuration constants
 */

/**
 * Default preset miners data
 * @type {Array<Object>}
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

/**
 * Preset scenarios for quick parameter loading
 * @type {Object}
 */
export const PRESET_SCENARIOS = {
  'current': {
    name: 'Current Market',
    params: {
      btcPriceStart: 100000,
      btcPriceEnd: 150000,
      networkHashrateStart: 900,
      networkHashrateEnd: 1100,
      poolFee: 2,
      taxRate: 35,
      stateRate: 0,
      useBonusDepreciation: true
    }
  },
  'conservative': {
    name: 'Conservative',
    params: {
      btcPriceStart: 100000,
      btcPriceEnd: 120000,
      networkHashrateStart: 900,
      networkHashrateEnd: 1200,
      poolFee: 2,
      taxRate: 35,
      stateRate: 5,
      useBonusDepreciation: true
    }
  },
  'bullish': {
    name: 'Bullish 2025',
    params: {
      btcPriceStart: 100000,
      btcPriceEnd: 200000,
      networkHashrateStart: 900,
      networkHashrateEnd: 1300,
      poolFee: 2,
      taxRate: 35,
      stateRate: 0,
      useBonusDepreciation: true
    }
  }
};

/**
 * Electricity rates for matrix columns (in $/kWh)
 * @type {Array<number>}
 */
export const ELECTRICITY_RATES = [0.047, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10];

/**
 * Default calculation parameters
 * @type {Object}
 */
export const DEFAULT_PARAMS = {
  btcPriceStart: 110000,
  btcPriceEnd: 150000,
  networkHashrateStart: 900,
  networkHashrateEnd: 1100,
  poolFee: 2,
  taxRate: 35,
  stateRate: 0,
  useBonusDepreciation: true,
  annualBtcPriceIncrease: 36.4,
  annualDifficultyIncrease: 22.2,
  useAnnualIncreases: false
};

/**
 * Bitcoin network constants
 */
export const BLOCK_REWARD = 3.125; // BTC per block (post-halving)
export const BLOCKS_PER_DAY = 144; // Average blocks per day
export const DAYS_PER_YEAR = 365;

/**
 * MACRS 5-year depreciation schedule
 * Year 1: 20%, Year 2: 32%, Year 3: 19.2%, Year 4: 11.52%, Year 5: 11.52%, Year 6: 5.76%
 * @type {Array<number>}
 */
export const MACRS_RATES = [0.20, 0.32, 0.192, 0.1152, 0.1152, 0.0576];

/**
 * LocalStorage keys
 */
export const STORAGE_KEYS = {
  MINERS: 'minerProfitMatrix_miners',
  PRICES: 'minerProfitMatrix_prices',
  PARAMS: 'minerProfitMatrix_params',
  SCENARIOS: 'minerProfitMatrix_scenarios',
  HAS_VISITED: 'hasVisited'
};
