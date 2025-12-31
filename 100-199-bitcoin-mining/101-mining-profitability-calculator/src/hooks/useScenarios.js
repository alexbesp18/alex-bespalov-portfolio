/**
 * Custom hook for managing scenarios (save/load/delete)
 */

import { useState, useCallback } from 'react';
import { PRESET_SCENARIOS } from '../utils/constants';
import { useLocalStorage } from './useLocalStorage';
import { STORAGE_KEYS } from '../utils/constants';

export const useScenarios = () => {
  const [savedScenarios, setSavedScenarios] = useLocalStorage(STORAGE_KEYS.SCENARIOS, {});
  const [showScenarioModal, setShowScenarioModal] = useState(false);
  const [newScenarioName, setNewScenarioName] = useState('');

  // Load preset scenario
  const loadPreset = useCallback((presetKey, setParams) => {
    const preset = PRESET_SCENARIOS[presetKey];
    if (preset && setParams) {
      setParams(prev => ({ ...prev, ...preset.params }));
    }
  }, []);

  // Save current scenario
  const saveScenario = useCallback((params, miners, minerPrices) => {
    if (!newScenarioName.trim()) {
      alert("Please enter a scenario name!");
      return false;
    }
    
    const scenarioData = {
      params,
      miners,
      prices: minerPrices,
      savedDate: new Date().toISOString()
    };
    
    setSavedScenarios(prev => ({
      ...prev,
      [newScenarioName]: scenarioData
    }));
    
    setNewScenarioName('');
    setShowScenarioModal(false);
    alert(`Scenario "${newScenarioName}" saved!`);
    return true;
  }, [newScenarioName, setSavedScenarios, setShowScenarioModal]);

  // Load scenario
  const loadScenario = useCallback((scenarioName, setParams, setMiners, setMinerPrices) => {
    const scenario = savedScenarios[scenarioName];
    if (scenario) {
      if (setParams) setParams(scenario.params);
      if (setMiners && scenario.miners) setMiners(scenario.miners);
      if (setMinerPrices && scenario.prices) setMinerPrices(scenario.prices);
      alert(`Scenario "${scenarioName}" loaded!`);
      return true;
    }
    return false;
  }, [savedScenarios]);

  // Delete scenario
  const deleteScenario = useCallback((scenarioName) => {
    if (window.confirm(`Delete scenario "${scenarioName}"?`)) {
      setSavedScenarios(prev => {
        const newScenarios = { ...prev };
        delete newScenarios[scenarioName];
        return newScenarios;
      });
      return true;
    }
    return false;
  }, [setSavedScenarios]);

  return {
    savedScenarios,
    showScenarioModal,
    setShowScenarioModal,
    newScenarioName,
    setNewScenarioName,
    loadPreset,
    saveScenario,
    loadScenario,
    deleteScenario
  };
};
