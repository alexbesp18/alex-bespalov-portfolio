/**
 * Electricity Rate Constants
 * 
 * Predefined electricity rates and presets for mining calculations.
 * 
 * @module constants/electricity
 */

/**
 * Standard electricity rates for matrix comparisons ($/kWh)
 * @constant {number[]}
 */
export const ELECTRICITY_RATES = [0.047, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10];

/**
 * Extended electricity rates for detailed analysis ($/kWh)
 * @constant {number[]}
 */
export const ELECTRICITY_RATES_EXTENDED = [
  0.03, 0.04, 0.047, 0.05, 0.055, 0.06, 0.065, 
  0.07, 0.075, 0.08, 0.085, 0.09, 0.095, 0.10, 0.11, 0.12
];

/**
 * Electricity rate presets by region/type
 * @constant {Object}
 */
export const ELECTRICITY_PRESETS = {
  cheap: {
    name: 'Cheap (Flared Gas/Hydro)',
    rate: 0.03,
    description: 'Behind-the-meter, stranded energy'
  },
  industrial_low: {
    name: 'Industrial Low',
    rate: 0.047,
    description: 'Best commercial rates in favorable regions'
  },
  industrial_average: {
    name: 'Industrial Average',
    rate: 0.065,
    description: 'Average commercial/industrial rate'
  },
  hosting_competitive: {
    name: 'Competitive Hosting',
    rate: 0.075,
    description: 'Competitive hosting facility rates'
  },
  hosting_premium: {
    name: 'Premium Hosting',
    rate: 0.085,
    description: 'Premium hosting with better uptime/service'
  },
  residential: {
    name: 'Residential',
    rate: 0.12,
    description: 'Typical residential electricity rate'
  },
  expensive: {
    name: 'Expensive',
    rate: 0.15,
    description: 'High-cost regions (CA, HI, parts of EU)'
  }
};

/**
 * Regional electricity rate averages ($/kWh)
 * @constant {Object}
 */
export const REGIONAL_ELECTRICITY_RATES = {
  // United States
  US_TX: 0.065,    // Texas
  US_WY: 0.070,    // Wyoming
  US_GA: 0.068,    // Georgia
  US_KY: 0.062,    // Kentucky
  US_MT: 0.058,    // Montana
  US_PA: 0.072,    // Pennsylvania
  US_NY: 0.098,    // New York
  US_CA: 0.145,    // California
  
  // International
  CA_QC: 0.045,    // Quebec, Canada (hydro)
  CA_AB: 0.065,    // Alberta, Canada
  IS: 0.035,       // Iceland (geothermal/hydro)
  NO: 0.048,       // Norway (hydro)
  RU: 0.038,       // Russia
  KZ: 0.035,       // Kazakhstan
  AE: 0.070,       // UAE
  PY: 0.042,       // Paraguay (hydro)
};

/**
 * Convert electricity rate between units
 * 
 * @param {number} rate - Rate value
 * @param {string} from - Source unit ('kWh', 'MWh')
 * @param {string} to - Target unit ('kWh', 'MWh')
 * @returns {number} Converted rate
 */
export const convertElectricityRate = (rate, from, to) => {
  if (from === to) return rate;
  if (from === 'kWh' && to === 'MWh') return rate * 1000;
  if (from === 'MWh' && to === 'kWh') return rate / 1000;
  return rate;
};

/**
 * Calculate monthly electricity cost
 * 
 * @param {number} powerWatts - Power consumption in watts
 * @param {number} ratePerKwh - Electricity rate in $/kWh
 * @param {number} [hoursPerDay=24] - Operating hours per day
 * @param {number} [daysPerMonth=30.42] - Days per month
 * @returns {number} Monthly electricity cost in USD
 */
export const calculateMonthlyElectricityCost = (powerWatts, ratePerKwh, hoursPerDay = 24, daysPerMonth = 30.42) => {
  const powerKw = powerWatts / 1000;
  return powerKw * hoursPerDay * daysPerMonth * ratePerKwh;
};

/**
 * Calculate annual electricity cost
 * 
 * @param {number} powerWatts - Power consumption in watts
 * @param {number} ratePerKwh - Electricity rate in $/kWh
 * @param {number} [uptimePercent=100] - Uptime percentage
 * @returns {number} Annual electricity cost in USD
 */
export const calculateAnnualElectricityCost = (powerWatts, ratePerKwh, uptimePercent = 100) => {
  const powerKw = powerWatts / 1000;
  const hoursPerYear = 8760 * (uptimePercent / 100);
  return powerKw * hoursPerYear * ratePerKwh;
};

