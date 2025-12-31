/**
 * useLocalStorage Hook
 * 
 * React hook for persistent state with localStorage.
 * 
 * @module hooks/useLocalStorage
 */

import { useState, useEffect, useCallback } from 'react';
import { isLocalStorageAvailable, safeJSONParse, safeJSONStringify } from '../storage/localStorage.js';

/**
 * Hook for syncing state with localStorage
 * 
 * @param {string} key - Storage key
 * @param {*} initialValue - Initial/default value
 * @param {Object} [options={}] - Options
 * @param {boolean} [options.serialize=true] - Whether to JSON serialize
 * @param {Function} [options.onError] - Error handler
 * @returns {[any, Function, Function]} [value, setValue, removeValue]
 * 
 * @example
 * const [miners, setMiners] = useLocalStorage('miners', []);
 * const [params, setParams, removeParams] = useLocalStorage('params', defaultParams);
 */
export const useLocalStorage = (key, initialValue, options = {}) => {
  const { serialize = true, onError } = options;
  
  // Get initial value from storage or use default
  const getStoredValue = useCallback(() => {
    if (!isLocalStorageAvailable()) {
      return initialValue;
    }
    
    try {
      const item = window.localStorage.getItem(key);
      
      if (item === null) {
        return initialValue;
      }
      
      return serialize ? safeJSONParse(item, initialValue) : item;
    } catch (error) {
      if (onError) onError(error);
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  }, [key, initialValue, serialize, onError]);
  
  const [storedValue, setStoredValue] = useState(getStoredValue);
  
  // Update localStorage when value changes
  const setValue = useCallback((value) => {
    try {
      // Allow functional updates
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      
      setStoredValue(valueToStore);
      
      if (isLocalStorageAvailable()) {
        const stringValue = serialize ? safeJSONStringify(valueToStore) : String(valueToStore);
        window.localStorage.setItem(key, stringValue);
      }
    } catch (error) {
      if (onError) onError(error);
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, serialize, storedValue, onError]);
  
  // Remove from localStorage
  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue);
      
      if (isLocalStorageAvailable()) {
        window.localStorage.removeItem(key);
      }
    } catch (error) {
      if (onError) onError(error);
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue, onError]);
  
  // Listen for storage changes from other tabs/windows
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === key && e.newValue !== null) {
        try {
          const newValue = serialize ? safeJSONParse(e.newValue, initialValue) : e.newValue;
          setStoredValue(newValue);
        } catch (error) {
          console.warn('Error parsing storage event:', error);
        }
      } else if (e.key === key && e.newValue === null) {
        setStoredValue(initialValue);
      }
    };
    
    if (isLocalStorageAvailable()) {
      window.addEventListener('storage', handleStorageChange);
      return () => window.removeEventListener('storage', handleStorageChange);
    }
  }, [key, initialValue, serialize]);
  
  return [storedValue, setValue, removeValue];
};

/**
 * Hook for multiple localStorage keys with a namespace
 * 
 * @param {string} namespace - Namespace prefix
 * @param {Object} defaults - Default values by key
 * @returns {Object} { values, setValue, setValues, reset }
 */
export const useLocalStorageObject = (namespace, defaults) => {
  const getStoredValues = () => {
    if (!isLocalStorageAvailable()) return defaults;
    
    const values = { ...defaults };
    
    for (const key of Object.keys(defaults)) {
      const storageKey = `${namespace}_${key}`;
      const item = window.localStorage.getItem(storageKey);
      
      if (item !== null) {
        try {
          values[key] = JSON.parse(item);
        } catch {
          // Keep default
        }
      }
    }
    
    return values;
  };
  
  const [values, setValuesState] = useState(getStoredValues);
  
  const setValue = useCallback((key, value) => {
    setValuesState(prev => {
      const newValues = { ...prev, [key]: value };
      
      if (isLocalStorageAvailable()) {
        const storageKey = `${namespace}_${key}`;
        window.localStorage.setItem(storageKey, JSON.stringify(value));
      }
      
      return newValues;
    });
  }, [namespace]);
  
  const setValues = useCallback((newValues) => {
    setValuesState(prev => {
      const merged = { ...prev, ...newValues };
      
      if (isLocalStorageAvailable()) {
        for (const [key, value] of Object.entries(newValues)) {
          const storageKey = `${namespace}_${key}`;
          window.localStorage.setItem(storageKey, JSON.stringify(value));
        }
      }
      
      return merged;
    });
  }, [namespace]);
  
  const reset = useCallback(() => {
    setValuesState(defaults);
    
    if (isLocalStorageAvailable()) {
      for (const key of Object.keys(defaults)) {
        const storageKey = `${namespace}_${key}`;
        window.localStorage.removeItem(storageKey);
      }
    }
  }, [namespace, defaults]);
  
  return { values, setValue, setValues, reset };
};

export default useLocalStorage;

