/**
 * useScenarios Hook
 * 
 * React hook for managing market scenarios.
 * 
 * @module hooks/useScenarios
 */

import { useState, useCallback, useMemo } from 'react';
import { useLocalStorage } from './useLocalStorage.js';
import { PRESET_SCENARIOS, createScenario, validateScenarioParams } from '../data/scenarios.js';
import { DEFAULT_PARAMS } from '../constants/defaults.js';

/**
 * Hook for managing market scenarios
 * 
 * @param {string} [storageKey='savedScenarios'] - localStorage key for custom scenarios
 * @param {Object} [initialParams] - Initial parameters
 * @returns {Object} Scenario management functions and state
 * 
 * @example
 * const {
 *   currentScenario,
 *   params,
 *   setParams,
 *   loadScenario,
 *   saveScenario,
 *   deleteScenario,
 *   customScenarios,
 * } = useScenarios();
 */
export const useScenarios = (storageKey = 'savedScenarios', initialParams = DEFAULT_PARAMS) => {
  // Current parameters state
  const [params, setParams] = useState(initialParams);
  
  // Track currently loaded scenario
  const [currentScenario, setCurrentScenario] = useState(null);
  
  // Custom scenarios stored in localStorage
  const [customScenarios, setCustomScenarios] = useLocalStorage(storageKey, {});
  
  // All available scenarios (presets + custom)
  const allScenarios = useMemo(() => {
    const scenarios = { ...PRESET_SCENARIOS };
    
    for (const [key, scenario] of Object.entries(customScenarios)) {
      scenarios[key] = { ...scenario, isCustom: true };
    }
    
    return scenarios;
  }, [customScenarios]);
  
  // Load a scenario by key
  const loadScenario = useCallback((key) => {
    const scenario = allScenarios[key];
    
    if (scenario) {
      setParams(prev => ({
        ...prev,
        ...scenario.params,
      }));
      setCurrentScenario(key);
      return true;
    }
    
    return false;
  }, [allScenarios]);
  
  // Save current params as a new scenario
  const saveScenario = useCallback((name, description = '') => {
    if (!name || typeof name !== 'string') {
      return { success: false, error: 'Scenario name is required' };
    }
    
    const key = name.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
    
    // Validate params
    const validation = validateScenarioParams(params);
    if (!validation.isValid) {
      return { success: false, error: validation.errors[0] };
    }
    
    const scenario = createScenario(name, description, params);
    
    setCustomScenarios(prev => ({
      ...prev,
      [key]: scenario,
    }));
    
    setCurrentScenario(key);
    
    return { success: true, key };
  }, [params, setCustomScenarios]);
  
  // Delete a custom scenario
  const deleteScenario = useCallback((key) => {
    if (PRESET_SCENARIOS[key]) {
      return { success: false, error: 'Cannot delete preset scenarios' };
    }
    
    if (!customScenarios[key]) {
      return { success: false, error: 'Scenario not found' };
    }
    
    setCustomScenarios(prev => {
      const newScenarios = { ...prev };
      delete newScenarios[key];
      return newScenarios;
    });
    
    if (currentScenario === key) {
      setCurrentScenario(null);
    }
    
    return { success: true };
  }, [customScenarios, currentScenario, setCustomScenarios]);
  
  // Reset to default params
  const resetParams = useCallback(() => {
    setParams(initialParams);
    setCurrentScenario(null);
  }, [initialParams]);
  
  // Update a single param
  const updateParam = useCallback((key, value) => {
    setParams(prev => ({
      ...prev,
      [key]: value,
    }));
    setCurrentScenario(null); // Mark as modified
  }, []);
  
  // Update multiple params
  const updateParams = useCallback((updates) => {
    setParams(prev => ({
      ...prev,
      ...updates,
    }));
    setCurrentScenario(null);
  }, []);
  
  // Check if current params match a scenario
  const matchesScenario = useCallback((key) => {
    const scenario = allScenarios[key];
    if (!scenario) return false;
    
    return Object.keys(scenario.params).every(
      paramKey => params[paramKey] === scenario.params[paramKey]
    );
  }, [allScenarios, params]);
  
  // Get list of preset scenario keys
  const presetKeys = useMemo(() => Object.keys(PRESET_SCENARIOS), []);
  
  // Get list of custom scenario keys
  const customKeys = useMemo(() => Object.keys(customScenarios), [customScenarios]);
  
  // Export scenarios to JSON
  const exportScenarios = useCallback(() => {
    return {
      customScenarios,
      currentParams: params,
      exportDate: new Date().toISOString(),
    };
  }, [customScenarios, params]);
  
  // Import scenarios from JSON
  const importScenarios = useCallback((data, options = {}) => {
    const { merge = true, loadFirst = true } = options;
    
    if (!data || typeof data !== 'object') {
      return { success: false, error: 'Invalid data format' };
    }
    
    if (data.customScenarios) {
      if (merge) {
        setCustomScenarios(prev => ({
          ...prev,
          ...data.customScenarios,
        }));
      } else {
        setCustomScenarios(data.customScenarios);
      }
    }
    
    if (data.currentParams && loadFirst) {
      setParams(prev => ({
        ...prev,
        ...data.currentParams,
      }));
    }
    
    return { success: true };
  }, [setCustomScenarios]);
  
  return {
    // State
    params,
    currentScenario,
    allScenarios,
    customScenarios,
    presetKeys,
    customKeys,
    
    // Actions
    setParams,
    updateParam,
    updateParams,
    loadScenario,
    saveScenario,
    deleteScenario,
    resetParams,
    
    // Utilities
    matchesScenario,
    exportScenarios,
    importScenarios,
  };
};

export default useScenarios;

