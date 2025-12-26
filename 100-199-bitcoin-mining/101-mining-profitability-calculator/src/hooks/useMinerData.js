/**
 * Custom hook for managing miner data (CRUD operations)
 */

import { useState, useCallback } from 'react';
import { DEFAULT_PRESET_MINERS } from '../utils/constants';
import { useLocalStorage } from './useLocalStorage';
import { STORAGE_KEYS } from '../utils/constants';

export const useMinerData = () => {
  const [miners, setMiners] = useLocalStorage(STORAGE_KEYS.MINERS, DEFAULT_PRESET_MINERS);
  const [minerPrices, setMinerPrices] = useLocalStorage(STORAGE_KEYS.PRICES, () => {
    const initialPrices = {};
    DEFAULT_PRESET_MINERS.forEach(miner => {
      initialPrices[miner.id] = miner.defaultPrice;
    });
    return initialPrices;
  });

  // Update miner property
  const updateMinerProperty = useCallback((minerId, property, value) => {
    setMiners(prev => prev.map(miner => {
      if (miner.id === minerId) {
        const updatedMiner = { ...miner, [property]: parseFloat(value) || 0 };
        
        // Auto-calculate efficiency when hashrate or power changes
        if (property === 'hashrate' || property === 'power') {
          if (updatedMiner.hashrate > 0 && updatedMiner.power > 0) {
            updatedMiner.efficiency = Math.round((updatedMiner.power / updatedMiner.hashrate) * 10) / 10;
          }
        }
        
        return updatedMiner;
      }
      return miner;
    }));
  }, [setMiners]);

  // Update miner price
  const updateMinerPrice = useCallback((minerId, price) => {
    setMinerPrices(prev => ({
      ...prev,
      [minerId]: parseFloat(price) || 0
    }));
  }, [setMinerPrices]);

  // Add new miner
  const addNewMiner = useCallback(() => {
    const newId = Math.max(...miners.map(m => m.id), 0) + 1;
    const newMiner = {
      id: newId,
      name: `Custom Miner ${newId}`,
      fullName: `Custom Miner ${newId}`,
      hashrate: 200,
      power: 3000,
      efficiency: 15,
      defaultPrice: 5000,
      manufacturer: "Custom",
      coolingType: "Air",
      releaseYear: 2024,
      series: "Custom"
    };
    
    setMiners(prev => [...prev, newMiner]);
    setMinerPrices(prev => ({ ...prev, [newId]: newMiner.defaultPrice }));
  }, [miners, setMiners, setMinerPrices]);

  // Remove miner
  const removeMiner = useCallback((minerId) => {
    if (miners.length <= 1) {
      alert("Cannot remove the last miner!");
      return;
    }
    
    if (window.confirm("Are you sure you want to remove this miner?")) {
      setMiners(prev => prev.filter(m => m.id !== minerId));
      setMinerPrices(prev => {
        const newPrices = { ...prev };
        delete newPrices[minerId];
        return newPrices;
      });
    }
  }, [miners.length, setMiners, setMinerPrices]);

  // Reset to defaults
  const resetMiners = useCallback(() => {
    setMiners(DEFAULT_PRESET_MINERS);
    const defaultPrices = {};
    DEFAULT_PRESET_MINERS.forEach(miner => {
      defaultPrices[miner.id] = miner.defaultPrice;
    });
    setMinerPrices(defaultPrices);
  }, [setMiners, setMinerPrices]);

  return {
    miners,
    minerPrices,
    updateMinerProperty,
    updateMinerPrice,
    addNewMiner,
    removeMiner,
    resetMiners
  };
};
