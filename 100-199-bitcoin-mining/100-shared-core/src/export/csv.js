/**
 * CSV Export/Import Utilities
 * 
 * Functions for exporting and importing data as CSV files.
 * 
 * @module export/csv
 */

/**
 * Convert array of objects to CSV string
 * 
 * @param {Object[]} data - Array of objects to convert
 * @param {Object} [options={}] - Conversion options
 * @param {string[]} [options.columns] - Specific columns to include (default: all)
 * @param {Object} [options.headers] - Custom header labels { fieldName: 'Label' }
 * @param {string} [options.delimiter=','] - Field delimiter
 * @returns {string} CSV string
 */
export const arrayToCSV = (data, options = {}) => {
  if (!Array.isArray(data) || data.length === 0) {
    return '';
  }
  
  const { 
    columns = Object.keys(data[0]), 
    headers = {},
    delimiter = ',' 
  } = options;
  
  // Create header row
  const headerRow = columns
    .map(col => headers[col] || col)
    .map(escapeCSVField)
    .join(delimiter);
  
  // Create data rows
  const dataRows = data.map(row => {
    return columns
      .map(col => {
        const value = row[col];
        return escapeCSVField(formatCSVValue(value));
      })
      .join(delimiter);
  });
  
  return [headerRow, ...dataRows].join('\n');
};

/**
 * Escape a CSV field value
 * 
 * @param {string} field - Field value
 * @returns {string} Escaped field
 */
const escapeCSVField = (field) => {
  const str = String(field);
  
  // Quote if contains comma, quote, or newline
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  
  return str;
};

/**
 * Format a value for CSV output
 * 
 * @param {*} value - Value to format
 * @returns {string} Formatted string
 */
const formatCSVValue = (value) => {
  if (value === null || value === undefined) {
    return '';
  }
  
  if (typeof value === 'object') {
    return JSON.stringify(value);
  }
  
  return String(value);
};

/**
 * Export data to CSV file download
 * 
 * @param {Object[]} data - Array of objects to export
 * @param {string} filename - Filename (without .csv extension)
 * @param {Object} [options={}] - Export options
 * @returns {boolean} Whether export succeeded
 */
export const exportToCSV = (data, filename, options = {}) => {
  try {
    const csv = arrayToCSV(data, options);
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
    return true;
  } catch (error) {
    console.error('CSV export failed:', error);
    return false;
  }
};

/**
 * Parse CSV string to array of objects
 * 
 * @param {string} csvString - CSV string to parse
 * @param {Object} [options={}] - Parse options
 * @param {string} [options.delimiter=','] - Field delimiter
 * @param {boolean} [options.hasHeader=true] - Whether first row is header
 * @param {string[]} [options.headers] - Custom headers (if no header row)
 * @returns {Object[]} Array of parsed objects
 */
export const parseCSV = (csvString, options = {}) => {
  const { delimiter = ',', hasHeader = true, headers: customHeaders } = options;
  
  if (!csvString || typeof csvString !== 'string') {
    return [];
  }
  
  const lines = csvString.split(/\r?\n/).filter(line => line.trim());
  
  if (lines.length === 0) {
    return [];
  }
  
  const parseRow = (line) => {
    const fields = [];
    let field = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      
      if (char === '"') {
        if (inQuotes && line[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = !inQuotes;
        }
      } else if (char === delimiter && !inQuotes) {
        fields.push(field.trim());
        field = '';
      } else {
        field += char;
      }
    }
    
    fields.push(field.trim());
    return fields;
  };
  
  let headers;
  let dataStartIndex;
  
  if (hasHeader) {
    headers = parseRow(lines[0]);
    dataStartIndex = 1;
  } else if (customHeaders) {
    headers = customHeaders;
    dataStartIndex = 0;
  } else {
    // Generate headers: col0, col1, etc.
    const firstRow = parseRow(lines[0]);
    headers = firstRow.map((_, i) => `col${i}`);
    dataStartIndex = 0;
  }
  
  const result = [];
  
  for (let i = dataStartIndex; i < lines.length; i++) {
    const values = parseRow(lines[i]);
    const row = {};
    
    headers.forEach((header, index) => {
      const value = values[index];
      row[header] = parseCSVValue(value);
    });
    
    result.push(row);
  }
  
  return result;
};

/**
 * Parse a CSV value to appropriate type
 * 
 * @param {string} value - String value to parse
 * @returns {*} Parsed value
 */
const parseCSVValue = (value) => {
  if (value === '' || value === undefined) {
    return null;
  }
  
  // Try number
  const num = Number(value);
  if (!isNaN(num) && value.trim() !== '') {
    return num;
  }
  
  // Try boolean
  const lower = value.toLowerCase();
  if (lower === 'true') return true;
  if (lower === 'false') return false;
  
  // Return as string
  return value;
};

/**
 * Import data from CSV file
 * 
 * @param {File} file - CSV file to import
 * @param {Object} [options={}] - Parse options
 * @returns {Promise<Object[]>} Promise resolving to parsed data
 */
export const importFromCSV = (file, options = {}) => {
  return new Promise((resolve, reject) => {
    if (!file) {
      reject(new Error('No file provided'));
      return;
    }
    
    const reader = new FileReader();
    
    reader.onload = (event) => {
      try {
        const data = parseCSV(event.target.result, options);
        resolve(data);
      } catch (error) {
        reject(new Error(`Failed to parse CSV: ${error.message}`));
      }
    };
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    
    reader.readAsText(file);
  });
};

/**
 * Create a CSV import handler
 * 
 * @param {Function} onImport - Callback with imported data
 * @param {Function} [onError] - Error callback
 * @param {Object} [options={}] - Parse options
 * @returns {Function} File input onChange handler
 */
export const createCSVImportHandler = (onImport, onError, options = {}) => {
  return async (event) => {
    const file = event.target.files?.[0];
    
    if (!file) return;
    
    try {
      const data = await importFromCSV(file, options);
      onImport(data);
    } catch (error) {
      if (onError) {
        onError(error);
      } else {
        console.error('CSV import error:', error);
        alert(`Import failed: ${error.message}`);
      }
    }
    
    if (event.target) {
      event.target.value = '';
    }
  };
};

