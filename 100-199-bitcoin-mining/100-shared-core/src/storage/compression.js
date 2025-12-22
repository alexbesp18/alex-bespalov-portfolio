/**
 * Data Compression Utilities
 * 
 * LZ-based compression for localStorage optimization.
 * 
 * @module storage/compression
 */

/**
 * Simple LZ-based string compression
 * Useful for reducing localStorage usage for large datasets
 * 
 * @param {string} input - String to compress
 * @returns {string} Compressed string
 */
export const compressString = (input) => {
  if (!input || typeof input !== 'string') return input;
  
  try {
    const dict = {};
    const data = (input + '').split('');
    const out = [];
    let currChar;
    let phrase = data[0];
    let code = 256;
    
    for (let i = 1; i < data.length; i++) {
      currChar = data[i];
      if (dict[phrase + currChar] != null) {
        phrase += currChar;
      } else {
        out.push(phrase.length > 1 ? dict[phrase] : phrase.charCodeAt(0));
        dict[phrase + currChar] = code;
        code++;
        phrase = currChar;
      }
    }
    out.push(phrase.length > 1 ? dict[phrase] : phrase.charCodeAt(0));
    
    return out.map(c => String.fromCharCode(c)).join('');
  } catch (error) {
    console.warn('Compression failed, returning original', error);
    return input;
  }
};

/**
 * Decompress LZ-compressed string
 * 
 * @param {string} input - Compressed string
 * @returns {string} Decompressed string
 */
export const decompressString = (input) => {
  if (!input || typeof input !== 'string') return input;
  
  try {
    const dict = {};
    const data = (input + '').split('');
    let currChar = data[0];
    let oldPhrase = currChar;
    const out = [currChar];
    let code = 256;
    let phrase;
    
    for (let i = 1; i < data.length; i++) {
      const currCode = data[i].charCodeAt(0);
      if (currCode < 256) {
        phrase = data[i];
      } else {
        phrase = dict[currCode] ? dict[currCode] : oldPhrase + currChar;
      }
      out.push(phrase);
      currChar = phrase.charAt(0);
      dict[code] = oldPhrase + currChar;
      code++;
      oldPhrase = phrase;
    }
    
    return out.join('');
  } catch (error) {
    console.warn('Decompression failed, returning original', error);
    return input;
  }
};

/**
 * Compress data object to string
 * 
 * @param {*} data - Data to compress (will be JSON serialized first)
 * @returns {string} Compressed string
 */
export const compressData = (data) => {
  try {
    const jsonStr = JSON.stringify(data);
    return compressString(jsonStr);
  } catch (error) {
    console.warn('Data compression failed', error);
    return JSON.stringify(data);
  }
};

/**
 * Decompress string to data object
 * 
 * @param {string} compressed - Compressed string
 * @param {*} [fallback=null] - Fallback value on error
 * @returns {*} Decompressed and parsed data
 */
export const decompressData = (compressed, fallback = null) => {
  try {
    const jsonStr = decompressString(compressed);
    return JSON.parse(jsonStr);
  } catch (error) {
    console.warn('Data decompression failed', error);
    return fallback;
  }
};

/**
 * Calculate compression ratio
 * 
 * @param {string} original - Original string
 * @param {string} compressed - Compressed string
 * @returns {number} Compression ratio (0-1, lower is better)
 */
export const getCompressionRatio = (original, compressed) => {
  if (!original || !compressed) return 1;
  return compressed.length / original.length;
};

/**
 * Check if compression is beneficial
 * Compression has overhead, so it's not always worth it
 * 
 * @param {string} data - Data to check
 * @param {number} [minSavings=0.2] - Minimum savings ratio to be beneficial
 * @returns {boolean} Whether compression is beneficial
 */
export const isCompressionBeneficial = (data, minSavings = 0.2) => {
  if (!data || data.length < 100) return false;
  
  const jsonStr = typeof data === 'string' ? data : JSON.stringify(data);
  const compressed = compressString(jsonStr);
  const ratio = getCompressionRatio(jsonStr, compressed);
  
  return ratio < (1 - minSavings);
};

/**
 * Smart compress - only compress if beneficial
 * 
 * @param {*} data - Data to potentially compress
 * @returns {Object} { compressed: boolean, data: string }
 */
export const smartCompress = (data) => {
  const jsonStr = typeof data === 'string' ? data : JSON.stringify(data);
  
  if (jsonStr.length < 100) {
    return { compressed: false, data: jsonStr };
  }
  
  const compressed = compressString(jsonStr);
  
  if (compressed.length < jsonStr.length * 0.8) {
    return { compressed: true, data: compressed };
  }
  
  return { compressed: false, data: jsonStr };
};

/**
 * Smart decompress - handle both compressed and uncompressed data
 * 
 * @param {Object} wrapper - { compressed: boolean, data: string }
 * @param {*} [fallback=null] - Fallback on error
 * @returns {*} Decompressed and parsed data
 */
export const smartDecompress = (wrapper, fallback = null) => {
  try {
    if (!wrapper) return fallback;
    
    const { compressed, data } = wrapper;
    const jsonStr = compressed ? decompressString(data) : data;
    return JSON.parse(jsonStr);
  } catch (error) {
    console.warn('Smart decompression failed', error);
    return fallback;
  }
};

