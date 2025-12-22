/**
 * Excel Export/Import Utilities
 * 
 * Functions for handling Excel files (primarily import/parsing).
 * For export, we typically use CSV as a universal format.
 * 
 * @module export/excel
 */

import { parseCSV } from './csv.js';

/**
 * Detect if a file is an Excel file
 * 
 * @param {File} file - File to check
 * @returns {boolean} Whether file is Excel format
 */
export const isExcelFile = (file) => {
  if (!file) return false;
  
  const name = file.name.toLowerCase();
  return name.endsWith('.xlsx') || name.endsWith('.xls') || name.endsWith('.xlsm');
};

/**
 * Detect file type from file object
 * 
 * @param {File} file - File to check
 * @returns {string} File type ('csv', 'excel', or 'unknown')
 */
export const detectFileType = (file) => {
  if (!file) return 'unknown';
  
  const name = file.name.toLowerCase();
  
  if (name.endsWith('.csv')) return 'csv';
  if (name.endsWith('.xlsx') || name.endsWith('.xls')) return 'excel';
  if (name.endsWith('.json')) return 'json';
  
  return 'unknown';
};

/**
 * Parse Excel/CSV file to array of objects
 * Note: For true Excel parsing, you'd need a library like xlsx.
 * This provides a basic implementation that works with CSV exports from Excel.
 * 
 * @param {File} file - File to parse
 * @param {Object} [options={}] - Parse options
 * @returns {Promise<Object[]>} Parsed data
 */
export const parseSpreadsheetFile = async (file, options = {}) => {
  const fileType = detectFileType(file);
  
  if (fileType === 'csv') {
    return parseCSVFile(file, options);
  }
  
  if (fileType === 'excel') {
    // For actual Excel parsing, we'd need xlsx library
    // This is a placeholder that could be extended
    console.warn('Native Excel parsing requires xlsx library. Attempting to read as text.');
    return parseCSVFile(file, options);
  }
  
  throw new Error(`Unsupported file type: ${file.name}`);
};

/**
 * Parse a CSV file
 * 
 * @param {File} file - CSV file
 * @param {Object} [options={}] - Parse options
 * @returns {Promise<Object[]>} Parsed data
 */
const parseCSVFile = (file, options = {}) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (event) => {
      try {
        const data = parseCSV(event.target.result, options);
        resolve(data);
      } catch (error) {
        reject(error);
      }
    };
    
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
};

/**
 * Create a universal spreadsheet import handler
 * Handles both CSV and Excel files
 * 
 * @param {Function} onImport - Callback with imported data
 * @param {Function} [onError] - Error callback
 * @param {Object} [options={}] - Options
 * @returns {Function} File input onChange handler
 */
export const createSpreadsheetImportHandler = (onImport, onError, options = {}) => {
  return async (event) => {
    const file = event.target.files?.[0];
    
    if (!file) return;
    
    try {
      const data = await parseSpreadsheetFile(file, options);
      onImport(data);
    } catch (error) {
      if (onError) {
        onError(error);
      } else {
        console.error('Import error:', error);
        alert(`Import failed: ${error.message}`);
      }
    }
    
    if (event.target) {
      event.target.value = '';
    }
  };
};

/**
 * Extract column headers from spreadsheet data
 * 
 * @param {Object[]} data - Parsed spreadsheet data
 * @returns {string[]} Column headers
 */
export const extractHeaders = (data) => {
  if (!Array.isArray(data) || data.length === 0) {
    return [];
  }
  
  return Object.keys(data[0]);
};

/**
 * Map spreadsheet columns to expected structure
 * 
 * @param {Object[]} data - Parsed data
 * @param {Object} columnMap - Mapping of source columns to target fields
 * @returns {Object[]} Transformed data
 * @example
 * mapColumns(data, { 'Miner Name': 'name', 'TH/s': 'hashrate' })
 */
export const mapColumns = (data, columnMap) => {
  if (!Array.isArray(data)) return [];
  
  return data.map(row => {
    const mapped = {};
    
    for (const [sourceCol, targetField] of Object.entries(columnMap)) {
      if (row[sourceCol] !== undefined) {
        mapped[targetField] = row[sourceCol];
      }
    }
    
    return mapped;
  });
};

/**
 * Normalize column names (lowercase, remove spaces)
 * 
 * @param {Object[]} data - Data with varied column names
 * @returns {Object[]} Data with normalized column names
 */
export const normalizeColumnNames = (data) => {
  if (!Array.isArray(data)) return [];
  
  return data.map(row => {
    const normalized = {};
    
    for (const [key, value] of Object.entries(row)) {
      const normalizedKey = key
        .toLowerCase()
        .replace(/\s+/g, '_')
        .replace(/[^a-z0-9_]/g, '');
      normalized[normalizedKey] = value;
    }
    
    return normalized;
  });
};

/**
 * Find matching column in data using fuzzy matching
 * 
 * @param {string[]} headers - Available headers
 * @param {string[]} candidates - Possible column names to match
 * @returns {string|null} Matching header or null
 */
export const findMatchingColumn = (headers, candidates) => {
  const lowerHeaders = headers.map(h => h.toLowerCase().replace(/\s+/g, ''));
  
  for (const candidate of candidates) {
    const lowerCandidate = candidate.toLowerCase().replace(/\s+/g, '');
    
    const index = lowerHeaders.findIndex(h => 
      h === lowerCandidate || 
      h.includes(lowerCandidate) || 
      lowerCandidate.includes(h)
    );
    
    if (index !== -1) {
      return headers[index];
    }
  }
  
  return null;
};

/**
 * Auto-detect column mappings based on common patterns
 * 
 * @param {string[]} headers - Column headers from file
 * @returns {Object} Detected column mappings
 */
export const autoDetectMinerColumns = (headers) => {
  const mappings = {};
  
  const patterns = {
    name: ['name', 'model', 'miner', 'miner name', 'model name'],
    hashrate: ['hashrate', 'th', 'th/s', 'hash rate', 'ths'],
    power: ['power', 'watts', 'w', 'watt', 'power consumption'],
    price: ['price', 'cost', 'usd', 'value', 'msrp'],
    efficiency: ['efficiency', 'j/th', 'w/th', 'j per th'],
  };
  
  for (const [field, candidates] of Object.entries(patterns)) {
    const match = findMatchingColumn(headers, candidates);
    if (match) {
      mappings[match] = field;
    }
  }
  
  return mappings;
};

