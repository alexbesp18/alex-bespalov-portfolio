/**
 * JSON Export/Import Utilities
 * 
 * Functions for exporting and importing data as JSON files.
 * 
 * @module export/json
 */

/**
 * Export data to a JSON file download
 * 
 * @param {*} data - Data to export (will be JSON serialized)
 * @param {string} filename - Filename (without .json extension)
 * @param {Object} [options={}] - Export options
 * @param {boolean} [options.pretty=true] - Pretty print JSON
 * @param {boolean} [options.includeMetadata=true] - Include export metadata
 * @returns {boolean} Whether export succeeded
 */
export const exportToJSON = (data, filename, options = {}) => {
  const { pretty = true, includeMetadata = true } = options;
  
  try {
    const exportData = includeMetadata ? {
      data,
      metadata: {
        exportDate: new Date().toISOString(),
        version: '1.0',
      },
    } : data;
    
    const jsonString = pretty 
      ? JSON.stringify(exportData, null, 2)
      : JSON.stringify(exportData);
    
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
    return true;
  } catch (error) {
    console.error('JSON export failed:', error);
    return false;
  }
};

/**
 * Import data from a JSON file
 * 
 * @param {File} file - File to import
 * @param {Object} [options={}] - Import options
 * @param {Function} [options.validator] - Optional validator function
 * @param {boolean} [options.unwrapMetadata=true] - Unwrap metadata wrapper if present
 * @returns {Promise<Object>} Promise resolving to imported data
 */
export const importFromJSON = (file, options = {}) => {
  const { validator, unwrapMetadata = true } = options;
  
  return new Promise((resolve, reject) => {
    if (!file) {
      reject(new Error('No file provided'));
      return;
    }
    
    if (!file.name.endsWith('.json')) {
      reject(new Error('File must be a JSON file'));
      return;
    }
    
    const reader = new FileReader();
    
    reader.onload = (event) => {
      try {
        let data = JSON.parse(event.target.result);
        
        // Unwrap metadata if present
        if (unwrapMetadata && data.metadata && data.data) {
          data = data.data;
        }
        
        // Run validator if provided
        if (validator) {
          const isValid = validator(data);
          if (!isValid) {
            reject(new Error('Data validation failed'));
            return;
          }
        }
        
        resolve(data);
      } catch (error) {
        reject(new Error(`Failed to parse JSON: ${error.message}`));
      }
    };
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    
    reader.readAsText(file);
  });
};

/**
 * Create a JSON file input handler
 * 
 * @param {Function} onImport - Callback with imported data
 * @param {Function} [onError] - Callback for errors
 * @param {Object} [options={}] - Import options
 * @returns {Function} File input onChange handler
 */
export const createJSONImportHandler = (onImport, onError, options = {}) => {
  return async (event) => {
    const file = event.target.files?.[0];
    
    if (!file) return;
    
    try {
      const data = await importFromJSON(file, options);
      onImport(data);
    } catch (error) {
      if (onError) {
        onError(error);
      } else {
        console.error('Import error:', error);
        alert(`Import failed: ${error.message}`);
      }
    }
    
    // Reset file input
    if (event.target) {
      event.target.value = '';
    }
  };
};

/**
 * Validate JSON structure against expected shape
 * 
 * @param {*} data - Data to validate
 * @param {Object} schema - Expected structure (keys -> types or validators)
 * @returns {boolean} Whether data matches schema
 */
export const validateJSONStructure = (data, schema) => {
  if (!data || typeof data !== 'object') {
    return false;
  }
  
  for (const [key, validator] of Object.entries(schema)) {
    const value = data[key];
    
    if (typeof validator === 'string') {
      // Type check
      if (typeof value !== validator) {
        return false;
      }
    } else if (typeof validator === 'function') {
      // Custom validator
      if (!validator(value)) {
        return false;
      }
    } else if (validator === null) {
      // Optional field, skip
      continue;
    }
  }
  
  return true;
};

/**
 * Deep merge two objects
 * 
 * @param {Object} target - Target object
 * @param {Object} source - Source object
 * @returns {Object} Merged object
 */
export const deepMerge = (target, source) => {
  const result = { ...target };
  
  for (const [key, value] of Object.entries(source)) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      result[key] = deepMerge(result[key] || {}, value);
    } else {
      result[key] = value;
    }
  }
  
  return result;
};

/**
 * Create a dated export filename
 * 
 * @param {string} prefix - Filename prefix
 * @returns {string} Filename with date
 */
export const createExportFilename = (prefix) => {
  const date = new Date().toISOString().split('T')[0];
  return `${prefix}-${date}`;
};

