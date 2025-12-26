/**
 * Power Consumption Database
 * 
 * Reference database for miner power consumption used to fill in missing data.
 * Based on manufacturer specifications and real-world measurements.
 * 
 * @module data/powerDatabase
 */

/**
 * Power consumption reference by miner model
 * Key is a normalized miner name pattern, value is power in watts
 * @constant {Object}
 */
export const POWER_DATABASE = {
  // S21 Series
  'S21 XP+ Hydro': 5500,
  'S21 XP Hyd': 5676,
  'S21e XP Hyd': 11180,
  'S21 XP': 3645,
  'S21+ Hyd': 4785,
  'S21 Pro': 3510,
  'S21 Hyd': 5360,
  'S21+': 3564,
  'S21e Hyd': 4896,
  'S21 Immersion': 5569,
  'S21': 3500,
  
  // S19 Series
  'S19 XP+ Hyd': 5301,
  'S19 XP Hyd': 5418,
  'S19 XP': 3010,
  'S19j Pro+': 3355,
  'S19j Pro': 3068,
  'S19 Pro+ Hyd': 5445,
  'S19 Pro Hyd': 5226,
  'S19 Pro': 3250,
  'S19': 3250,
  
  // Whatsminer M60 Series
  'M60S++': 3422,
  'M60S+': 3600,
  'M60S': 3422,
  'M60': 3420,
  
  // Whatsminer M50 Series
  'M50S++': 3296,
  'M50S+': 3276,
  'M50S': 3276,
  'M50': 3276,
  
  // Whatsminer M30 Series
  'M30S++': 3472,
  'M30S+': 3400,
  'M30S': 3268,
  
  // Avalon Series
  'A1566': 3420,
  'A1466': 3300,
  'A1366': 3250,
  'A1246': 3420,
  'A1166 Pro': 3400,
};

/**
 * Normalize a miner name for lookup
 * 
 * @param {string} name - Miner name
 * @returns {string} Normalized name
 */
const normalizeName = (name) => {
  if (!name) return '';
  
  return name
    .replace(/Bitmain\s*Antminer\s*/i, '')
    .replace(/MicroBT\s*Whatsminer\s*/i, '')
    .replace(/Canaan\s*Avalon\s*/i, '')
    .replace(/\s+/g, ' ')
    .trim();
};

/**
 * Get power consumption for a miner by name
 * 
 * @param {string} minerName - Miner name or model
 * @returns {number|null} Power consumption in watts, or null if not found
 */
export const getPowerByName = (minerName) => {
  const normalized = normalizeName(minerName);
  
  // Try exact match first
  if (POWER_DATABASE[normalized]) {
    return POWER_DATABASE[normalized];
  }
  
  // Try partial match
  for (const [key, value] of Object.entries(POWER_DATABASE)) {
    if (normalized.includes(key) || key.includes(normalized)) {
      return value;
    }
  }
  
  return null;
};

/**
 * Estimate power consumption based on hashrate and efficiency target
 * 
 * @param {number} hashrate - Hashrate in TH/s
 * @param {number} [targetEfficiency=18] - Target efficiency in J/TH
 * @returns {number} Estimated power in watts
 */
export const estimatePower = (hashrate, targetEfficiency = 18) => {
  return Math.round(hashrate * targetEfficiency);
};

/**
 * Get efficiency rating category
 * 
 * @param {number} efficiency - Efficiency in J/TH
 * @returns {string} Rating category
 */
export const getEfficiencyRating = (efficiency) => {
  if (efficiency <= 12) return 'excellent';
  if (efficiency <= 15) return 'very-good';
  if (efficiency <= 18) return 'good';
  if (efficiency <= 22) return 'average';
  if (efficiency <= 28) return 'below-average';
  return 'poor';
};

/**
 * Get efficiency color class for UI
 * 
 * @param {number} efficiency - Efficiency in J/TH
 * @returns {string} Tailwind CSS color class
 */
export const getEfficiencyColorClass = (efficiency) => {
  const rating = getEfficiencyRating(efficiency);
  const colors = {
    'excellent': 'text-green-600',
    'very-good': 'text-green-500',
    'good': 'text-blue-500',
    'average': 'text-yellow-500',
    'below-average': 'text-orange-500',
    'poor': 'text-red-500',
  };
  return colors[rating] || 'text-gray-500';
};

/**
 * Efficiency thresholds for different years
 * Lower is better
 * @constant {Object}
 */
export const EFFICIENCY_THRESHOLDS = {
  2024: {
    excellent: 12,
    good: 16,
    acceptable: 20,
  },
  2023: {
    excellent: 18,
    good: 22,
    acceptable: 28,
  },
  2022: {
    excellent: 22,
    good: 28,
    acceptable: 34,
  },
};

/**
 * Check if a miner meets efficiency threshold for a given year
 * 
 * @param {number} efficiency - Miner efficiency in J/TH
 * @param {string} threshold - Threshold level ('excellent', 'good', 'acceptable')
 * @param {number} [year=2024] - Reference year
 * @returns {boolean} Whether miner meets threshold
 */
export const meetsEfficiencyThreshold = (efficiency, threshold, year = 2024) => {
  const thresholds = EFFICIENCY_THRESHOLDS[year] || EFFICIENCY_THRESHOLDS[2024];
  return efficiency <= thresholds[threshold];
};

