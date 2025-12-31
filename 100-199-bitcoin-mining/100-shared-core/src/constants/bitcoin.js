/**
 * Bitcoin Network Constants
 * 
 * Core constants related to Bitcoin mining and network parameters.
 * These values are used across all mining calculation tools.
 * 
 * @module constants/bitcoin
 */

/**
 * Current block reward in BTC (post-April 2024 halving)
 * @constant {number}
 */
export const BLOCK_REWARD = 3.125;

/**
 * Average number of blocks mined per day
 * @constant {number}
 */
export const BLOCKS_PER_DAY = 144;

/**
 * Days in a year for annual calculations
 * @constant {number}
 */
export const DAYS_PER_YEAR = 365;

/**
 * Average days in a month for monthly calculations
 * @constant {number}
 */
export const DAYS_PER_MONTH = 30.42;

/**
 * Number of blocks between each halving event
 * @constant {number}
 */
export const HALVING_BLOCK_INTERVAL = 210000;

/**
 * Historical and projected halving dates
 * @constant {Object}
 */
export const HALVING_DATES = {
  2012: new Date('2012-11-28'),
  2016: new Date('2016-07-09'),
  2020: new Date('2020-05-11'),
  2024: new Date('2024-04-20'),
  2028: new Date('2028-04-01'), // Projected
};

/**
 * Block rewards by era (in BTC)
 * @constant {Object}
 */
export const BLOCK_REWARDS_BY_ERA = {
  0: 50,      // Genesis to first halving
  1: 25,      // 2012-2016
  2: 12.5,    // 2016-2020
  3: 6.25,    // 2020-2024
  4: 3.125,   // 2024-2028 (current)
  5: 1.5625,  // 2028-2032 (projected)
};

/**
 * Get the effective block reward for a given date
 * Accounts for halving events
 * 
 * @param {Date} [date=new Date()] - Date to check
 * @returns {number} Block reward in BTC
 * @example
 * getEffectiveBlockReward(new Date('2025-01-01')) // Returns 3.125
 * getEffectiveBlockReward(new Date('2029-01-01')) // Returns 1.5625
 */
export const getEffectiveBlockReward = (date = new Date()) => {
  const halvingDates = Object.entries(HALVING_DATES).sort((a, b) => a[0] - b[0]);
  
  let era = 0;
  for (const [, halvingDate] of halvingDates) {
    if (date >= halvingDate) {
      era++;
    } else {
      break;
    }
  }
  
  return BLOCK_REWARDS_BY_ERA[era] ?? BLOCK_REWARDS_BY_ERA[Object.keys(BLOCK_REWARDS_BY_ERA).length - 1];
};

/**
 * Check if a halving occurs within a date range
 * 
 * @param {Date} startDate - Start of date range
 * @param {Date} endDate - End of date range
 * @returns {Object|null} Halving info if found, null otherwise
 */
export const getHalvingInRange = (startDate, endDate) => {
  for (const [year, halvingDate] of Object.entries(HALVING_DATES)) {
    if (halvingDate >= startDate && halvingDate <= endDate) {
      const era = parseInt(year) <= 2012 ? 1 : 
                  parseInt(year) <= 2016 ? 2 :
                  parseInt(year) <= 2020 ? 3 :
                  parseInt(year) <= 2024 ? 4 : 5;
      return {
        date: halvingDate,
        year: parseInt(year),
        rewardBefore: BLOCK_REWARDS_BY_ERA[era - 1],
        rewardAfter: BLOCK_REWARDS_BY_ERA[era],
      };
    }
  }
  return null;
};

/**
 * Calculate daily BTC production for the entire network
 * 
 * @param {number} [blockReward=BLOCK_REWARD] - Current block reward
 * @returns {number} Daily BTC produced by entire network
 */
export const getDailyNetworkProduction = (blockReward = BLOCK_REWARD) => {
  return BLOCKS_PER_DAY * blockReward;
};

/**
 * Convert hashrate between units
 * 
 * @param {number} value - Hashrate value
 * @param {string} from - Source unit ('TH', 'PH', 'EH')
 * @param {string} to - Target unit ('TH', 'PH', 'EH')
 * @returns {number} Converted hashrate
 */
export const convertHashrate = (value, from, to) => {
  const units = { TH: 1, PH: 1000, EH: 1000000 };
  return value * (units[from] / units[to]);
};

