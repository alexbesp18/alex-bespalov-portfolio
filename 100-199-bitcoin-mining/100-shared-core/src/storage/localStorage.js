/**
 * LocalStorage Utilities
 * 
 * Type-safe localStorage wrapper with namespacing and error handling.
 * 
 * @module storage/localStorage
 */

/**
 * Check if localStorage is available
 * 
 * @returns {boolean} Whether localStorage is available
 */
export const isLocalStorageAvailable = () => {
  try {
    const test = '__storage_test__';
    window.localStorage.setItem(test, test);
    window.localStorage.removeItem(test);
    return true;
  } catch {
    return false;
  }
};

/**
 * Create a namespaced storage manager
 * 
 * @param {string} namespace - Namespace prefix for all keys
 * @returns {Object} Storage manager with get, set, remove, clear methods
 * @example
 * const storage = createStorageManager('myApp');
 * storage.set('user', { name: 'John' });
 * const user = storage.get('user');
 */
export const createStorageManager = (namespace) => {
  const prefix = namespace ? `${namespace}_` : '';
  
  return {
    /**
     * Get a value from storage
     * 
     * @param {string} key - Storage key
     * @param {*} [defaultValue=null] - Default value if key doesn't exist
     * @returns {*} Stored value or default
     */
    get: (key, defaultValue = null) => {
      if (!isLocalStorageAvailable()) return defaultValue;
      
      try {
        const item = window.localStorage.getItem(`${prefix}${key}`);
        if (item === null) return defaultValue;
        return JSON.parse(item);
      } catch (error) {
        console.warn(`Error reading from localStorage: ${key}`, error);
        return defaultValue;
      }
    },
    
    /**
     * Set a value in storage
     * 
     * @param {string} key - Storage key
     * @param {*} value - Value to store (will be JSON serialized)
     * @returns {boolean} Whether the operation succeeded
     */
    set: (key, value) => {
      if (!isLocalStorageAvailable()) return false;
      
      try {
        window.localStorage.setItem(`${prefix}${key}`, JSON.stringify(value));
        return true;
      } catch (error) {
        console.warn(`Error writing to localStorage: ${key}`, error);
        return false;
      }
    },
    
    /**
     * Remove a value from storage
     * 
     * @param {string} key - Storage key to remove
     * @returns {boolean} Whether the operation succeeded
     */
    remove: (key) => {
      if (!isLocalStorageAvailable()) return false;
      
      try {
        window.localStorage.removeItem(`${prefix}${key}`);
        return true;
      } catch (error) {
        console.warn(`Error removing from localStorage: ${key}`, error);
        return false;
      }
    },
    
    /**
     * Clear all values in this namespace
     * 
     * @returns {boolean} Whether the operation succeeded
     */
    clear: () => {
      if (!isLocalStorageAvailable()) return false;
      
      try {
        const keys = Object.keys(window.localStorage);
        keys.forEach(key => {
          if (key.startsWith(prefix)) {
            window.localStorage.removeItem(key);
          }
        });
        return true;
      } catch (error) {
        console.warn('Error clearing localStorage', error);
        return false;
      }
    },
    
    /**
     * Get all keys in this namespace
     * 
     * @returns {string[]} Array of keys (without prefix)
     */
    keys: () => {
      if (!isLocalStorageAvailable()) return [];
      
      try {
        return Object.keys(window.localStorage)
          .filter(key => key.startsWith(prefix))
          .map(key => key.slice(prefix.length));
      } catch {
        return [];
      }
    },
    
    /**
     * Get all values in this namespace
     * 
     * @returns {Object} Object with all key-value pairs
     */
    getAll: () => {
      if (!isLocalStorageAvailable()) return {};
      
      const result = {};
      const keys = Object.keys(window.localStorage)
        .filter(key => key.startsWith(prefix));
      
      keys.forEach(key => {
        try {
          const shortKey = key.slice(prefix.length);
          result[shortKey] = JSON.parse(window.localStorage.getItem(key));
        } catch {
          // Skip invalid entries
        }
      });
      
      return result;
    },
    
    /**
     * Check if a key exists
     * 
     * @param {string} key - Key to check
     * @returns {boolean} Whether the key exists
     */
    has: (key) => {
      if (!isLocalStorageAvailable()) return false;
      return window.localStorage.getItem(`${prefix}${key}`) !== null;
    },
    
    /**
     * Get storage size for this namespace in bytes
     * 
     * @returns {number} Size in bytes
     */
    getSize: () => {
      if (!isLocalStorageAvailable()) return 0;
      
      let size = 0;
      const keys = Object.keys(window.localStorage)
        .filter(key => key.startsWith(prefix));
      
      keys.forEach(key => {
        const value = window.localStorage.getItem(key);
        size += key.length + (value ? value.length : 0);
      });
      
      return size * 2; // UTF-16 = 2 bytes per character
    },
  };
};

/**
 * Default storage manager (no namespace)
 */
export const storage = createStorageManager('');

/**
 * Get remaining localStorage quota in bytes
 * 
 * @returns {number} Remaining bytes (approximate)
 */
export const getRemainingQuota = () => {
  if (!isLocalStorageAvailable()) return 0;
  
  // Most browsers have 5MB limit
  const maxSize = 5 * 1024 * 1024;
  
  let currentSize = 0;
  Object.keys(window.localStorage).forEach(key => {
    const value = window.localStorage.getItem(key);
    currentSize += key.length + (value ? value.length : 0);
  });
  
  return Math.max(0, maxSize - (currentSize * 2));
};

/**
 * Safely parse JSON with fallback
 * 
 * @param {string} str - String to parse
 * @param {*} [fallback=null] - Fallback value on parse error
 * @returns {*} Parsed value or fallback
 */
export const safeJSONParse = (str, fallback = null) => {
  try {
    return JSON.parse(str);
  } catch {
    return fallback;
  }
};

/**
 * Safely stringify value
 * 
 * @param {*} value - Value to stringify
 * @param {string} [fallback='null'] - Fallback on stringify error
 * @returns {string} JSON string
 */
export const safeJSONStringify = (value, fallback = 'null') => {
  try {
    return JSON.stringify(value);
  } catch {
    return fallback;
  }
};

