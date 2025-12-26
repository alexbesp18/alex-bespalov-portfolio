/**
 * Canonical Miner Database
 * 
 * Single source of truth for miner specifications used across all calculators.
 * 
 * @module data/miners
 */

/**
 * @typedef {Object} Miner
 * @property {string} id - Unique identifier
 * @property {string} name - Short display name
 * @property {string} fullName - Full model name
 * @property {number} hashrate - Hashrate in TH/s
 * @property {number} power - Power consumption in watts
 * @property {number} efficiency - Efficiency in J/TH (W/TH)
 * @property {number} defaultPrice - Default/MSRP price in USD
 * @property {string} manufacturer - Manufacturer name
 * @property {string} coolingType - Cooling type (Air, Hydro, Immersion)
 * @property {number} releaseYear - Year of release
 * @property {string} series - Product series
 */

/**
 * Complete miner database with all supported models
 * @type {Miner[]}
 */
export const MINER_DATABASE = [
  // S21 Series - Latest Generation
  { id: 'S21_XP_PLUS_HYD', name: 'S21 XP+ Hyd', fullName: 'Bitmain Antminer S21 XP+ Hyd', hashrate: 500, power: 5500, efficiency: 11, defaultPrice: 14530, manufacturer: 'Bitmain', coolingType: 'Hydro', releaseYear: 2024, series: 'S21' },
  { id: 'S21_XP_HYD', name: 'S21 XP Hyd', fullName: 'Bitmain Antminer S21 XP Hyd', hashrate: 473, power: 5676, efficiency: 12, defaultPrice: 10800, manufacturer: 'Bitmain', coolingType: 'Hydro', releaseYear: 2024, series: 'S21' },
  { id: 'S21E_XP_HYD_3U', name: 'S21e XP Hyd 3U', fullName: 'Bitmain Antminer S21e XP Hyd 3U', hashrate: 860, power: 11180, efficiency: 13, defaultPrice: 19450, manufacturer: 'Bitmain', coolingType: 'Hydro', releaseYear: 2024, series: 'S21' },
  { id: 'S21_XP', name: 'S21 XP', fullName: 'Bitmain Antminer S21 XP', hashrate: 270, power: 3645, efficiency: 13.5, defaultPrice: 6833, manufacturer: 'Bitmain', coolingType: 'Air', releaseYear: 2024, series: 'S21' },
  { id: 'S21_PLUS_HYD', name: 'S21+ Hyd', fullName: 'Bitmain Antminer S21+ Hyd', hashrate: 319, power: 4785, efficiency: 15, defaultPrice: 5780, manufacturer: 'Bitmain', coolingType: 'Hydro', releaseYear: 2024, series: 'S21' },
  { id: 'S21_PLUS_HYD_338', name: 'S21+ Hyd 338', fullName: 'Bitmain Antminer S21+ Hyd 338', hashrate: 338, power: 5070, efficiency: 15.0, defaultPrice: 5780, manufacturer: 'Bitmain', coolingType: 'Hydro', releaseYear: 2024, series: 'S21' },
  { id: 'S21_PRO', name: 'S21 Pro', fullName: 'Bitmain Antminer S21 Pro', hashrate: 234, power: 3510, efficiency: 15, defaultPrice: 4271, manufacturer: 'Bitmain', coolingType: 'Air', releaseYear: 2024, series: 'S21' },
  { id: 'S21_PRO_245', name: 'S21 Pro 245', fullName: 'Bitmain Antminer S21 Pro 245', hashrate: 245, power: 3675, efficiency: 15.0, defaultPrice: 4393, manufacturer: 'Bitmain', coolingType: 'Air', releaseYear: 2024, series: 'S21' },
  { id: 'S21_PRO_220', name: 'S21 Pro 220', fullName: 'Bitmain Antminer S21 Pro 220', hashrate: 220, power: 3300, efficiency: 15.0, defaultPrice: 4648, manufacturer: 'Bitmain', coolingType: 'Air', releaseYear: 2024, series: 'S21' },
  { id: 'S21_HYD', name: 'S21 Hyd', fullName: 'Bitmain Antminer S21 Hyd', hashrate: 335, power: 5360, efficiency: 16, defaultPrice: 5863, manufacturer: 'Bitmain', coolingType: 'Hydro', releaseYear: 2024, series: 'S21' },
  { id: 'S21_PLUS', name: 'S21+', fullName: 'Bitmain Antminer S21+', hashrate: 216, power: 3564, efficiency: 16.5, defaultPrice: 3251, manufacturer: 'Bitmain', coolingType: 'Air', releaseYear: 2024, series: 'S21' },
  { id: 'S21_PLUS_225', name: 'S21+ 225', fullName: 'Bitmain Antminer S21+ 225', hashrate: 225, power: 3712, efficiency: 16.5, defaultPrice: 3337, manufacturer: 'Bitmain', coolingType: 'Air', releaseYear: 2024, series: 'S21' },
  { id: 'S21_PLUS_235', name: 'S21+ 235', fullName: 'Bitmain Antminer S21+ 235', hashrate: 235, power: 3878, efficiency: 16.5, defaultPrice: 3511, manufacturer: 'Bitmain', coolingType: 'Air', releaseYear: 2024, series: 'S21' },
  { id: 'S21E_HYD', name: 'S21e Hyd', fullName: 'Bitmain Antminer S21e Hyd', hashrate: 288, power: 4896, efficiency: 17.0, defaultPrice: 3887, manufacturer: 'Bitmain', coolingType: 'Hydro', releaseYear: 2024, series: 'S21' },
  { id: 'S21', name: 'S21', fullName: 'Bitmain Antminer S21', hashrate: 200, power: 3500, efficiency: 17.5, defaultPrice: 4830, manufacturer: 'Bitmain', coolingType: 'Air', releaseYear: 2024, series: 'S21' },
  { id: 'S21_188', name: 'S21 188', fullName: 'Bitmain Antminer S21 188', hashrate: 188, power: 3290, efficiency: 17.5, defaultPrice: 4457, manufacturer: 'Bitmain', coolingType: 'Air', releaseYear: 2024, series: 'S21' },
  { id: 'S21_IMMERSION', name: 'S21 Immersion', fullName: 'Bitmain Antminer S21 Immersion', hashrate: 301, power: 5569, efficiency: 18.5, defaultPrice: 6318, manufacturer: 'Bitmain', coolingType: 'Immersion', releaseYear: 2024, series: 'S21' },
  { id: 'S21_IMMERSION_302', name: 'S21 Immersion 302', fullName: 'Bitmain Antminer S21 Immersion 302', hashrate: 302, power: 5587, efficiency: 18.5, defaultPrice: 5863, manufacturer: 'Bitmain', coolingType: 'Immersion', releaseYear: 2024, series: 'S21' },
  
  // S19 Series - Previous Generation
  { id: 'S19_XP_PLUS_HYD', name: 'S19 XP+ Hyd', fullName: 'Bitmain Antminer S19 XP+ Hyd', hashrate: 279, power: 5301, efficiency: 19, defaultPrice: 3181, manufacturer: 'Bitmain', coolingType: 'Hydro', releaseYear: 2023, series: 'S19' },
  { id: 'S19_XP_HYD_257', name: 'S19 XP Hyd 257', fullName: 'Bitmain Antminer S19 XP Hydro 257', hashrate: 257, power: 5418, efficiency: 21.1, defaultPrice: 2360, manufacturer: 'Bitmain', coolingType: 'Hydro', releaseYear: 2023, series: 'S19' },
  { id: 'S19_XP', name: 'S19 XP', fullName: 'Bitmain Antminer S19 XP', hashrate: 140, power: 3010, efficiency: 21.5, defaultPrice: 2000, manufacturer: 'Bitmain', coolingType: 'Air', releaseYear: 2023, series: 'S19' },
  { id: 'S19J_PRO_PLUS', name: 'S19j Pro+', fullName: 'Bitmain Antminer S19j Pro+', hashrate: 122, power: 3355, efficiency: 27.5, defaultPrice: 1500, manufacturer: 'Bitmain', coolingType: 'Air', releaseYear: 2022, series: 'S19' },
  { id: 'S19J_PRO', name: 'S19j Pro', fullName: 'Bitmain Antminer S19j Pro', hashrate: 104, power: 3068, efficiency: 29.5, defaultPrice: 1200, manufacturer: 'Bitmain', coolingType: 'Air', releaseYear: 2021, series: 'S19' },
  
  // Whatsminer Series
  { id: 'M60S', name: 'M60S', fullName: 'MicroBT Whatsminer M60S', hashrate: 186, power: 3422, efficiency: 18.4, defaultPrice: 4200, manufacturer: 'MicroBT', coolingType: 'Air', releaseYear: 2024, series: 'M60' },
  { id: 'M60S_PLUS', name: 'M60S+', fullName: 'MicroBT Whatsminer M60S+', hashrate: 200, power: 3600, efficiency: 18, defaultPrice: 4500, manufacturer: 'MicroBT', coolingType: 'Air', releaseYear: 2024, series: 'M60' },
  { id: 'M50S_PLUS_PLUS', name: 'M50S++', fullName: 'MicroBT Whatsminer M50S++', hashrate: 148, power: 3296, efficiency: 22.3, defaultPrice: 2800, manufacturer: 'MicroBT', coolingType: 'Air', releaseYear: 2023, series: 'M50' },
  { id: 'M50S', name: 'M50S', fullName: 'MicroBT Whatsminer M50S', hashrate: 126, power: 3276, efficiency: 26, defaultPrice: 2200, manufacturer: 'MicroBT', coolingType: 'Air', releaseYear: 2023, series: 'M50' },
  
  // Canaan Avalon Series
  { id: 'A1566', name: 'A1566', fullName: 'Canaan Avalon A1566', hashrate: 185, power: 3420, efficiency: 18.5, defaultPrice: 3800, manufacturer: 'Canaan', coolingType: 'Air', releaseYear: 2024, series: 'Avalon' },
  { id: 'A1466', name: 'A1466', fullName: 'Canaan Avalon A1466', hashrate: 150, power: 3300, efficiency: 22, defaultPrice: 2900, manufacturer: 'Canaan', coolingType: 'Air', releaseYear: 2023, series: 'Avalon' },
];

/**
 * Get all miners from the database
 * @returns {Miner[]} All miners
 */
export const getAllMiners = () => [...MINER_DATABASE];

/**
 * Get a miner by ID
 * 
 * @param {string} id - Miner ID
 * @returns {Miner|undefined} Miner object or undefined
 */
export const getMinerById = (id) => {
  return MINER_DATABASE.find(m => m.id === id);
};

/**
 * Get a miner by name (partial match)
 * 
 * @param {string} name - Miner name to search
 * @returns {Miner|undefined} First matching miner
 */
export const getMinerByName = (name) => {
  const lowerName = name.toLowerCase();
  return MINER_DATABASE.find(m => 
    m.name.toLowerCase().includes(lowerName) || 
    m.fullName.toLowerCase().includes(lowerName)
  );
};

/**
 * Get miners by filter criteria
 * 
 * @param {Object} filter - Filter criteria
 * @param {string} [filter.manufacturer] - Filter by manufacturer
 * @param {string} [filter.coolingType] - Filter by cooling type
 * @param {string} [filter.series] - Filter by series
 * @param {number} [filter.minHashrate] - Minimum hashrate
 * @param {number} [filter.maxHashrate] - Maximum hashrate
 * @param {number} [filter.maxEfficiency] - Maximum efficiency (lower is better)
 * @param {number} [filter.releaseYear] - Filter by release year
 * @returns {Miner[]} Filtered miners
 */
export const getMinersBy = (filter) => {
  return MINER_DATABASE.filter(miner => {
    if (filter.manufacturer && miner.manufacturer !== filter.manufacturer) return false;
    if (filter.coolingType && miner.coolingType !== filter.coolingType) return false;
    if (filter.series && miner.series !== filter.series) return false;
    if (filter.minHashrate && miner.hashrate < filter.minHashrate) return false;
    if (filter.maxHashrate && miner.hashrate > filter.maxHashrate) return false;
    if (filter.maxEfficiency && miner.efficiency > filter.maxEfficiency) return false;
    if (filter.releaseYear && miner.releaseYear !== filter.releaseYear) return false;
    return true;
  });
};

/**
 * Get all unique manufacturers
 * @returns {string[]} List of manufacturers
 */
export const getManufacturers = () => {
  return [...new Set(MINER_DATABASE.map(m => m.manufacturer))];
};

/**
 * Get all unique cooling types
 * @returns {string[]} List of cooling types
 */
export const getCoolingTypes = () => {
  return [...new Set(MINER_DATABASE.map(m => m.coolingType))];
};

/**
 * Get all unique series
 * @returns {string[]} List of series
 */
export const getSeries = () => {
  return [...new Set(MINER_DATABASE.map(m => m.series))];
};

/**
 * Sort miners by a field
 * 
 * @param {Miner[]} miners - Miners to sort
 * @param {string} field - Field to sort by
 * @param {boolean} [ascending=true] - Sort direction
 * @returns {Miner[]} Sorted miners
 */
export const sortMiners = (miners, field, ascending = true) => {
  return [...miners].sort((a, b) => {
    const aVal = a[field];
    const bVal = b[field];
    
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return ascending ? aVal - bVal : bVal - aVal;
    }
    
    const comparison = String(aVal).localeCompare(String(bVal));
    return ascending ? comparison : -comparison;
  });
};

/**
 * Calculate efficiency from power and hashrate
 * 
 * @param {number} power - Power in watts
 * @param {number} hashrate - Hashrate in TH/s
 * @returns {number} Efficiency in J/TH
 */
export const calculateEfficiency = (power, hashrate) => {
  if (!hashrate || hashrate <= 0) return 0;
  return Math.round((power / hashrate) * 10) / 10;
};

/**
 * Convert legacy miner format (numeric ID) to new format
 * 
 * @param {Object} legacyMiner - Miner with numeric ID
 * @returns {Miner} Miner with string ID
 */
export const convertLegacyMiner = (legacyMiner) => {
  const found = MINER_DATABASE.find(m => 
    m.name === legacyMiner.name || 
    m.fullName === legacyMiner.fullName
  );
  
  if (found) {
    return { ...found, ...legacyMiner, id: found.id };
  }
  
  // Create ID from name if not found
  const id = (legacyMiner.name || legacyMiner.fullName || 'CUSTOM')
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '_');
  
  return {
    ...legacyMiner,
    id,
    efficiency: calculateEfficiency(legacyMiner.power, legacyMiner.hashrate),
  };
};

