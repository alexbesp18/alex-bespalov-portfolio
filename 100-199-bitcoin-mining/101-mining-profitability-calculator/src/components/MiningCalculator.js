import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { Calculator, TrendingUp, Settings, Info, X, Download, Upload, Save, Plus, Trash2, Share2, Loader2, AlertCircle, Zap, Target } from 'lucide-react';

// Import from shared-core for modular reuse
import {
  // Constants
  BLOCK_REWARD,
  BLOCKS_PER_DAY,
  // Core calculation functions
  calculateMonthlyBtcMined,
  calculateMonthlyElectricity,
  calculatePoolFee,
  getCalculatedEndValues as sharedGetCalculatedEndValues,
  interpolateValue,
  // Tax calculations
  calculateDepreciation,
  calculateTaxLiability,
  // Risk/UI helpers
  getCellColor,
  getDisplayValue,
} from '@btc-mining/shared-core';

// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Calculator error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="text-center p-8 bg-red-50 rounded-lg">
          <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-red-600 mb-2">Something went wrong</h2>
          <p className="text-gray-600 mb-4">Please refresh the page to try again</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Refresh Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

const EnhancedMinerProfitMatrix = () => {
  // State for loading
  const [isCalculating, setIsCalculating] = useState(false);
  const [showWelcome, setShowWelcome] = useState(() => {
    return !localStorage.getItem('hasVisited');
  });

  // Enhanced preset miners data
  const DEFAULT_PRESET_MINERS = [
    { id: 1, name: "S21 XP+ Hyd", fullName: "Bitmain Antminer S21 XP+ Hyd", hashrate: 500, power: 5500, efficiency: 11, defaultPrice: 14530, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2024, series: "S21" },
    { id: 2, name: "S21 XP Hyd", fullName: "Bitmain Antminer S21 XP Hyd", hashrate: 473, power: 5676, efficiency: 12, defaultPrice: 10800, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2024, series: "S21" },
    { id: 3, name: "S21e XP Hyd 3U", fullName: "Bitmain Antminer S21e XP Hyd 3U", hashrate: 860, power: 11180, efficiency: 13, defaultPrice: 19450, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2024, series: "S21" },
    { id: 4, name: "S21 XP", fullName: "Bitmain Antminer S21 XP", hashrate: 270, power: 3645, efficiency: 13.5, defaultPrice: 6833, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
    { id: 5, name: "S21+ Hyd", fullName: "Bitmain Antminer S21+ Hyd", hashrate: 319, power: 4785, efficiency: 15, defaultPrice: 5780, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2024, series: "S21" },
    { id: 6, name: "S21+ Hyd 338", fullName: "Bitmain Antminer S21+ Hyd 338", hashrate: 338, power: 5070, efficiency: 15.0, defaultPrice: 5780, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2024, series: "S21" },
    { id: 7, name: "S21 Pro", fullName: "Bitmain Antminer S21 Pro", hashrate: 234, power: 3510, efficiency: 15, defaultPrice: 4271, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
    { id: 8, name: "S21 Pro 245", fullName: "Bitmain Antminer S21 Pro 245", hashrate: 245, power: 3675, efficiency: 15.0, defaultPrice: 4393, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
    { id: 9, name: "S21 Pro 220", fullName: "Bitmain Antminer S21 Pro 220", hashrate: 220, power: 3300, efficiency: 15.0, defaultPrice: 4648, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
    { id: 10, name: "S21 Hyd", fullName: "Bitmain Antminer S21 Hyd", hashrate: 335, power: 5360, efficiency: 16, defaultPrice: 5863, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2024, series: "S21" },
    { id: 11, name: "S21+", fullName: "Bitmain Antminer S21+", hashrate: 216, power: 3564, efficiency: 16.5, defaultPrice: 3251, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
    { id: 12, name: "S21+ 225", fullName: "Bitmain Antminer S21+ 225", hashrate: 225, power: 3712, efficiency: 16.5, defaultPrice: 3337, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
    { id: 13, name: "S21+ 235", fullName: "Bitmain Antminer S21+ 235", hashrate: 235, power: 3878, efficiency: 16.5, defaultPrice: 3511, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
    { id: 14, name: "S21e Hyd", fullName: "Bitmain Antminer S21e Hyd", hashrate: 288, power: 4896, efficiency: 17.0, defaultPrice: 3887, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2024, series: "S21" },
    { id: 15, name: "S21", fullName: "Bitmain Antminer S21", hashrate: 200, power: 3500, efficiency: 17.5, defaultPrice: 4830, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
    { id: 16, name: "S21 188", fullName: "Bitmain Antminer S21 188", hashrate: 188, power: 3290, efficiency: 17.5, defaultPrice: 4457, manufacturer: "Bitmain", coolingType: "Air", releaseYear: 2024, series: "S21" },
    { id: 17, name: "S21 Immersion", fullName: "Bitmain Antminer S21 Immersion", hashrate: 301, power: 5569, efficiency: 18.5, defaultPrice: 6318, manufacturer: "Bitmain", coolingType: "Immersion", releaseYear: 2024, series: "S21" },
    { id: 18, name: "S21 Immersion 302", fullName: "Bitmain Antminer S21 Immersion 302", hashrate: 302, power: 5587, efficiency: 18.5, defaultPrice: 5863, manufacturer: "Bitmain", coolingType: "Immersion", releaseYear: 2024, series: "S21" },
    { id: 19, name: "S19 XP+ Hyd", fullName: "Bitmain Antminer S19 XP+ Hyd", hashrate: 279, power: 5301, efficiency: 19, defaultPrice: 3181, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2023, series: "S19" },
    { id: 20, name: "S19 XP Hyd 257", fullName: "Bitmain Antminer S19 XP Hydro 257", hashrate: 257, power: 5418, efficiency: 21.1, defaultPrice: 2360, manufacturer: "Bitmain", coolingType: "Hydro", releaseYear: 2023, series: "S19" }
  ];

  // Preset scenarios
  const PRESET_SCENARIOS = {
    'current': {
      name: 'Current Market',
      params: {
        btcPriceStart: 100000,
        btcPriceEnd: 150000,
        networkHashrateStart: 900,
        networkHashrateEnd: 1100,
        poolFee: 2,
        taxRate: 35,
        stateRate: 0,
        useBonusDepreciation: true
      }
    },
    'conservative': {
      name: 'Conservative',
      params: {
        btcPriceStart: 100000,
        btcPriceEnd: 120000,
        networkHashrateStart: 900,
        networkHashrateEnd: 1200,
        poolFee: 2,
        taxRate: 35,
        stateRate: 5,
        useBonusDepreciation: true
      }
    },
    'bullish': {
      name: 'Bullish 2025',
      params: {
        btcPriceStart: 100000,
        btcPriceEnd: 200000,
        networkHashrateStart: 900,
        networkHashrateEnd: 1300,
        poolFee: 2,
        taxRate: 35,
        stateRate: 0,
        useBonusDepreciation: true
      }
    }
  };

  // Load miners from localStorage or use defaults
  const [miners, setMiners] = useState(() => {
    const savedMiners = localStorage.getItem('minerProfitMatrix_miners');
    return savedMiners ? JSON.parse(savedMiners) : DEFAULT_PRESET_MINERS;
  });

  // Electricity rates for columns
  const ELECTRICITY_RATES = [0.047, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10];

  // State for miner prices (editable)
  const [minerPrices, setMinerPrices] = useState(() => {
    const savedPrices = localStorage.getItem('minerProfitMatrix_prices');
    if (savedPrices) {
      return JSON.parse(savedPrices);
    }
    const initialPrices = {};
    miners.forEach(miner => {
      initialPrices[miner.id] = miner.defaultPrice;
    });
    return initialPrices;
  });

  // Default parameters
  const DEFAULT_PARAMS = {
    btcPriceStart: 110000,
    btcPriceEnd: 150000,
    networkHashrateStart: 900,
    networkHashrateEnd: 1100,
    poolFee: 2,
    taxRate: 35,
    stateRate: 0,
    useBonusDepreciation: true,
    annualBtcPriceIncrease: 36.4,
    annualDifficultyIncrease: 22.2,
    useAnnualIncreases: false
  };

  // State for parameters
  const [params, setParams] = useState(() => {
    const savedParams = localStorage.getItem('minerProfitMatrix_params');
    return savedParams ? JSON.parse(savedParams) : DEFAULT_PARAMS;
  });

  // State for saved scenarios
  const [savedScenarios, setSavedScenarios] = useState(() => {
    const saved = localStorage.getItem('minerProfitMatrix_scenarios');
    return saved ? JSON.parse(saved) : {};
  });

  // State for scenario management
  const [showScenarioModal, setShowScenarioModal] = useState(false);
  const [newScenarioName, setNewScenarioName] = useState('');

  // State for modal
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [displayMetric, setDisplayMetric] = useState('netProfit');
  const [showTwoYearAnalysis, setShowTwoYearAnalysis] = useState(false);

  // Acquisition Mode state
  const [calculatorMode, setCalculatorMode] = useState('profitability'); // 'profitability' or 'acquisition'
  const [targetProfit, setTargetProfit] = useState(500); // Target profit in USD for acquisition mode

  // Constants - imported from shared-core at top of file
  // BLOCK_REWARD, BLOCKS_PER_DAY, MACRS_RATES are now imported from @btc-mining/shared-core

  // Save to localStorage whenever state changes
  useEffect(() => {
    localStorage.setItem('minerProfitMatrix_miners', JSON.stringify(miners));
  }, [miners]);

  useEffect(() => {
    localStorage.setItem('minerProfitMatrix_prices', JSON.stringify(minerPrices));
  }, [minerPrices]);

  useEffect(() => {
    localStorage.setItem('minerProfitMatrix_params', JSON.stringify(params));
  }, [params]);

  useEffect(() => {
    localStorage.setItem('minerProfitMatrix_scenarios', JSON.stringify(savedScenarios));
  }, [savedScenarios]);

  // Update miner property
  const updateMinerProperty = (minerId, property, value) => {
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
  };

  // Update miner price
  const updateMinerPrice = (minerId, price) => {
    setMinerPrices(prev => ({
      ...prev,
      [minerId]: parseFloat(price) || 0
    }));
  };

  // Add new miner
  const addNewMiner = () => {
    const newId = Math.max(...miners.map(m => m.id)) + 1;
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
  };

  // Remove miner
  const removeMiner = (minerId) => {
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
  };

  // Load preset scenario
  const loadPreset = (presetKey) => {
    const preset = PRESET_SCENARIOS[presetKey];
    if (preset) {
      setParams(prev => ({ ...prev, ...preset.params }));
    }
  };

  // Share results
  const shareResults = () => {
    const bestMiner = profitMatrix.reduce((best, current) => {
      const currentBest = current.results.find(r => r.rate === 0.05);
      const prevBest = best.results.find(r => r.rate === 0.05);
      return currentBest.netProfit > prevBest.netProfit ? current : best;
    });

    const url = window.location.href;
    const text = `Bitcoin Mining Calculator Results:
Most profitable: ${bestMiner.miner.name}
ROI: ${bestMiner.results[1].roi.toFixed(1)}%
At $${params.btcPriceStart} BTC
Try it: ${url}`;
    
    navigator.clipboard.writeText(text);
    alert('Results copied to clipboard! You can now paste it anywhere.');
  };

  // Export miners to JSON
  const exportMiners = () => {
    const exportData = {
      miners,
      prices: minerPrices,
      params,
      exportDate: new Date().toISOString()
    };
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `miner-data-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
  };

  // Import miners from JSON
  const importMiners = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importData = JSON.parse(e.target.result);
        
        if (importData.miners && Array.isArray(importData.miners)) {
          setMiners(importData.miners);
          
          if (importData.prices) {
            setMinerPrices(importData.prices);
          }
          
          if (importData.params) {
            setParams(importData.params);
          }
          
          alert("Data imported successfully!");
        } else {
          alert("Invalid file format!");
        }
      } catch (error) {
        alert("Error reading file: " + error.message);
      }
    };
    reader.readAsText(file);
    
    // Reset file input
    event.target.value = '';
  };

  // Save current scenario
  const saveScenario = () => {
    if (!newScenarioName.trim()) {
      alert("Please enter a scenario name!");
      return;
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
  };

  // Load scenario
  const loadScenario = (scenarioName) => {
    const scenario = savedScenarios[scenarioName];
    if (scenario) {
      setParams(scenario.params);
      if (scenario.miners) setMiners(scenario.miners);
      if (scenario.prices) setMinerPrices(scenario.prices);
      alert(`Scenario "${scenarioName}" loaded!`);
    }
  };

  // Delete scenario
  const deleteScenario = (scenarioName) => {
    if (window.confirm(`Delete scenario "${scenarioName}"?`)) {
      setSavedScenarios(prev => {
        const newScenarios = { ...prev };
        delete newScenarios[scenarioName];
        return newScenarios;
      });
    }
  };

  // Reset to defaults
  const resetToDefaults = () => {
    if (window.confirm("Reset all data to defaults? This will clear all custom miners and scenarios.")) {
      setMiners(DEFAULT_PRESET_MINERS);
      setParams(DEFAULT_PARAMS);
      setSavedScenarios({});
      
      const defaultPrices = {};
      DEFAULT_PRESET_MINERS.forEach(miner => {
        defaultPrices[miner.id] = miner.defaultPrice;
      });
      setMinerPrices(defaultPrices);
    }
  };

  // Calculate end values based on annual increases - uses shared-core function
  const getCalculatedEndValues = () => {
    return sharedGetCalculatedEndValues(params);
  };

  // Calculate monthly details - refactored to use shared-core calculation functions
  const calculateMonthlyDetails = useCallback((miner, electricityRate, year = 1) => {
    const { btcPriceEnd, networkHashrateEnd } = getCalculatedEndValues();
    const minerPrice = minerPrices[miner.id] || miner.defaultPrice;

    let btcPriceStart = params.btcPriceStart;
    let networkHashrateStart = params.networkHashrateStart;
    let currentBtcPriceEnd = btcPriceEnd;
    let currentNetworkHashrateEnd = networkHashrateEnd;

    // For year 2, start where year 1 ended
    if (year === 2) {
      btcPriceStart = btcPriceEnd;
      networkHashrateStart = networkHashrateEnd;

      if (params.useAnnualIncreases) {
        currentBtcPriceEnd = btcPriceStart * (1 + params.annualBtcPriceIncrease / 100);
        currentNetworkHashrateEnd = networkHashrateStart * (1 + params.annualDifficultyIncrease / 100);
      } else {
        currentBtcPriceEnd = btcPriceStart * (btcPriceEnd / params.btcPriceStart);
        currentNetworkHashrateEnd = networkHashrateStart * (networkHashrateEnd / params.networkHashrateStart);
      }
    }

    const monthlyData = [];
    let totalBtcMined = 0;
    let totalRevenue = 0;
    let totalElectricity = 0;
    let totalPoolFees = 0;

    for (let month = 0; month < 12; month++) {
      const progress = month / 11;

      // Use shared-core interpolation
      const btcPrice = interpolateValue(btcPriceStart, currentBtcPriceEnd, progress);
      const networkHashrate = interpolateValue(networkHashrateStart, currentNetworkHashrateEnd, progress);

      // Use shared-core calculation functions
      const btcPerMonth = calculateMonthlyBtcMined(miner.hashrate, networkHashrate, BLOCK_REWARD);
      const grossRevenue = btcPerMonth * btcPrice;
      const poolFees = calculatePoolFee(grossRevenue, params.poolFee || 2);
      const netRevenue = grossRevenue - poolFees;
      const electricityCost = calculateMonthlyElectricity(miner.power, electricityRate);
      const operationalProfit = netRevenue - electricityCost;

      monthlyData.push({
        month: month + 1,
        btcPrice,
        networkHashrate,
        btcMined: btcPerMonth,
        btcMinedNet: btcPerMonth * (1 - (params.poolFee || 2) / 100),
        grossRevenue,
        poolFees,
        netRevenue,
        electricityCost,
        operationalProfit
      });

      totalBtcMined += btcPerMonth * (1 - (params.poolFee || 2) / 100);
      totalRevenue += netRevenue;
      totalElectricity += electricityCost;
      totalPoolFees += poolFees;
    }

    const totalOperationalProfit = totalRevenue - totalElectricity;

    // Use shared-core depreciation calculation
    const depreciation = calculateDepreciation(minerPrice, year, params.useBonusDepreciation);

    // Use shared-core tax calculation
    const taxableIncome = Math.max(0, totalOperationalProfit - depreciation);
    const { federalTax, stateTax, totalTax } = calculateTaxLiability(
      taxableIncome,
      params.taxRate || 35,
      params.stateRate || 0
    );

    const afterTaxProfit = totalOperationalProfit - totalTax;

    return {
      monthlyData,
      totalBtcMined,
      totalRevenue,
      totalElectricity,
      totalPoolFees,
      totalOperationalProfit,
      depreciation,
      taxableIncome,
      federalTax,
      stateTax,
      totalTax,
      afterTaxProfit,
      minerPrice,
      year
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, minerPrices]);

  // Calculate yearly profit
  const calculateYearlyProfit = useCallback((miner, electricityRate) => {
    const details = calculateMonthlyDetails(miner, electricityRate, 1);
    const netProfit = details.afterTaxProfit - details.minerPrice;
    const roi = details.minerPrice > 0 ? (netProfit / details.minerPrice) * 100 : 0;
    
    return {
      ...details,
      netProfit,
      roi,
      electricityOnlyBtcCost: details.totalBtcMined > 0 ? details.totalElectricity / details.totalBtcMined : 0
    };
  }, [calculateMonthlyDetails]);

  // Calculate 2-year cumulative profit
  const calculateTwoYearProfit = useCallback((miner, electricityRate) => {
    const year1Details = calculateMonthlyDetails(miner, electricityRate, 1);
    const year2Details = calculateMonthlyDetails(miner, electricityRate, 2);
    
    const totalBtcMined = year1Details.totalBtcMined + year2Details.totalBtcMined;
    const totalOperationalProfit = year1Details.totalOperationalProfit + year2Details.totalOperationalProfit;
    const totalAfterTaxProfit = year1Details.afterTaxProfit + year2Details.afterTaxProfit;
    const totalNetProfit = totalAfterTaxProfit - year1Details.minerPrice;
    const twoYearRoi = year1Details.minerPrice > 0 ? (totalNetProfit / year1Details.minerPrice) * 100 : 0;
    const annualizedRoi = twoYearRoi / 2;
    
    return {
      year1Details,
      year2Details,
      totalBtcMined,
      operationalProfit: totalOperationalProfit,
      afterTaxProfit: totalAfterTaxProfit,
      netProfit: totalNetProfit,
      roi: twoYearRoi,
      annualizedRoi,
      electricityOnlyBtcCost: totalBtcMined > 0
        ? (year1Details.totalElectricity + year2Details.totalElectricity) / totalBtcMined
        : 0,
      minerPrice: year1Details.minerPrice
    };
  }, [calculateMonthlyDetails]);

  // Calculate maximum acquisition price to achieve target profit
  // This reverses the profitability calculation: given target profit, what's the max we can pay?
  const calculateMaxAcquisitionPrice = useCallback((miner, electricityRate, targetProfitAmount) => {
    const { btcPriceEnd, networkHashrateEnd } = getCalculatedEndValues();

    // Calculate total revenue and costs for a year (without miner cost)
    let totalRevenue = 0;
    let totalElectricity = 0;

    for (let month = 0; month < 12; month++) {
      const progress = month / 11;
      const btcPrice = params.btcPriceStart + (btcPriceEnd - params.btcPriceStart) * progress;
      const networkHashrate = params.networkHashrateStart + (networkHashrateEnd - params.networkHashrateStart) * progress;

      const shareOfNetwork = miner.hashrate / (networkHashrate * 1000000);
      const btcPerMonth = shareOfNetwork * BLOCKS_PER_DAY * BLOCK_REWARD * 30.42;

      const grossRevenue = btcPerMonth * btcPrice;
      const poolFees = grossRevenue * (params.poolFee / 100);
      const netRevenue = grossRevenue - poolFees;

      const powerKw = miner.power / 1000;
      const electricityCost = powerKw * 24 * 30.42 * electricityRate;

      totalRevenue += netRevenue;
      totalElectricity += electricityCost;
    }

    const operationalProfit = totalRevenue - totalElectricity;

    // With bonus depreciation: afterTaxProfit = operationalProfit - tax
    // tax = (operationalProfit - minerPrice) * taxRate (if operationalProfit > minerPrice)
    // netProfit = afterTaxProfit - minerPrice = targetProfitAmount
    //
    // If using bonus depreciation (100% year 1):
    // taxableIncome = max(0, operationalProfit - minerPrice)
    // tax = taxableIncome * totalTaxRate
    // afterTaxProfit = operationalProfit - tax
    // netProfit = afterTaxProfit - minerPrice = targetProfitAmount
    //
    // Solving for minerPrice:
    // If operationalProfit > minerPrice (taxable):
    //   tax = (operationalProfit - minerPrice) * taxRate
    //   afterTaxProfit = operationalProfit - tax = operationalProfit - (operationalProfit - minerPrice) * taxRate
    //   netProfit = afterTaxProfit - minerPrice = targetProfitAmount
    //   operationalProfit - (operationalProfit - minerPrice) * taxRate - minerPrice = targetProfitAmount
    //   operationalProfit - operationalProfit * taxRate + minerPrice * taxRate - minerPrice = targetProfitAmount
    //   operationalProfit * (1 - taxRate) + minerPrice * (taxRate - 1) = targetProfitAmount
    //   minerPrice * (taxRate - 1) = targetProfitAmount - operationalProfit * (1 - taxRate)
    //   minerPrice = (operationalProfit * (1 - taxRate) - targetProfitAmount) / (1 - taxRate)
    //   minerPrice = operationalProfit - targetProfitAmount / (1 - taxRate)

    const totalTaxRate = (params.taxRate + params.stateRate) / 100;

    let maxAcquisitionPrice;

    if (params.useBonusDepreciation) {
      // With bonus depreciation, the entire miner cost offsets taxable income in year 1
      // netProfit = operationalProfit * (1 - taxRate) + minerPrice * taxRate - minerPrice
      // netProfit = operationalProfit * (1 - taxRate) - minerPrice * (1 - taxRate)
      // targetProfitAmount = (operationalProfit - minerPrice) * (1 - taxRate)
      // minerPrice = operationalProfit - targetProfitAmount / (1 - taxRate)
      maxAcquisitionPrice = operationalProfit - targetProfitAmount / (1 - totalTaxRate);
    } else {
      // Without bonus depreciation, use MACRS (20% year 1)
      // This is more complex, so we'll approximate
      const year1Depreciation = 0.20; // MACRS year 1
      // Simplified: assume taxable income = operationalProfit - (minerPrice * year1Depreciation)
      // tax = taxableIncome * taxRate
      // netProfit = operationalProfit - tax - minerPrice = targetProfitAmount
      // This requires iterative solving, but for simplicity:
      maxAcquisitionPrice = (operationalProfit - targetProfitAmount) / (1 + (1 - year1Depreciation) * totalTaxRate);
    }

    // Ensure non-negative
    maxAcquisitionPrice = Math.max(0, maxAcquisitionPrice);

    // Calculate what the ROI would be at this acquisition price
    const impliedROI = maxAcquisitionPrice > 0 ? (targetProfitAmount / maxAcquisitionPrice) * 100 : 0;

    // Calculate $/TH for this acquisition price
    const dollarPerTH = maxAcquisitionPrice / miner.hashrate;

    return {
      maxAcquisitionPrice: Math.round(maxAcquisitionPrice),
      dollarPerTH: Math.round(dollarPerTH * 100) / 100,
      impliedROI,
      operationalProfit,
      targetProfit: targetProfitAmount,
      miner,
      electricityRate
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, BLOCK_REWARD, BLOCKS_PER_DAY]);

  // Calculate the acquisition matrix
  const acquisitionMatrix = useMemo(() => {
    if (calculatorMode !== 'acquisition') return [];

    const matrix = [];

    for (const miner of miners) {
      const row = {
        miner: miner,
        results: []
      };

      for (const rate of ELECTRICITY_RATES) {
        const result = calculateMaxAcquisitionPrice(miner, rate, targetProfit);
        row.results.push({
          rate,
          ...result
        });
      }

      matrix.push(row);
    }

    return matrix;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [miners, calculatorMode, targetProfit, calculateMaxAcquisitionPrice]);

  // Calculate the profit matrix with loading state
  const profitMatrix = useMemo(() => {
    setIsCalculating(true);
    const matrix = [];
    
    for (const miner of miners) {
      const row = {
        miner: miner,
        results: []
      };
      
      for (const rate of ELECTRICITY_RATES) {
        const result = calculateYearlyProfit(miner, rate);
        row.results.push({
          rate,
          ...result
        });
      }
      
      matrix.push(row);
    }
    
    setIsCalculating(false);
    return matrix;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, minerPrices, miners, calculateYearlyProfit]);

  // Calculate the 2-year profit matrix
  const twoYearProfitMatrix = useMemo(() => {
    if (!showTwoYearAnalysis) return [];
    
    const matrix = [];
    
    for (const miner of miners) {
      const row = {
        miner: miner,
        results: []
      };
      
      for (const rate of ELECTRICITY_RATES) {
        const result = calculateTwoYearProfit(miner, rate);
        row.results.push({
          rate,
          ...result
        });
      }
      
      matrix.push(row);
    }
    
    return matrix;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, minerPrices, showTwoYearAnalysis, miners, calculateTwoYearProfit]);

  // Calculate best performers and insights
  const quickInsights = useMemo(() => {
    if (!profitMatrix || profitMatrix.length === 0) return null;
    
    // Find most profitable at $0.05/kWh
    const bestProfitMiner = profitMatrix.reduce((best, current) => {
      const currentBest = current.results.find(r => r.rate === 0.05);
      const prevBest = best.results.find(r => r.rate === 0.05);
      return currentBest.netProfit > prevBest.netProfit ? current : best;
    });
    
    // Find most efficient
    const mostEfficient = miners.reduce((best, current) => 
      current.efficiency < best.efficiency ? current : best
    );
    
    // Calculate average breakeven price
    const breakevenPrices = profitMatrix.map(row => {
      const profitable = row.results.filter(r => r.netProfit > 0);
      return profitable.length > 0 ? profitable[profitable.length - 1].rate : null;
    }).filter(price => price !== null);
    
    const avgBreakeven = breakevenPrices.length > 0 
      ? (breakevenPrices.reduce((sum, price) => sum + price, 0) / breakevenPrices.length)
      : 0;
    
    return {
      mostProfitable: bestProfitMiner.miner.name,
      mostProfitableROI: bestProfitMiner.results.find(r => r.rate === 0.05).roi,
      mostEfficient: mostEfficient.name,
      mostEfficientValue: mostEfficient.efficiency,
      avgBreakevenElectricity: avgBreakeven
    };
  }, [profitMatrix, miners]);

  // Hashrate/Difficulty Widget
  const HashrateWidget = () => {
    const { networkHashrateEnd } = getCalculatedEndValues();
    const monthlyGrowth = ((networkHashrateEnd - params.networkHashrateStart) / params.networkHashrateStart) * 100 / 12;
    
    return (
      <div className="bg-yellow-50 rounded-lg p-4 mb-6">
        <h3 className="font-semibold mb-2 flex items-center gap-2">
          <Zap className="w-4 h-4" />
          Network Difficulty Trend
        </h3>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Current:</span>
            <span className="font-bold block">{params.networkHashrateStart} EH/s</span>
          </div>
          <div>
            <span className="text-gray-600">Monthly Growth:</span>
            <span className="font-bold block">{monthlyGrowth.toFixed(1)}%</span>
          </div>
          <div>
            <span className="text-gray-600">Year End Est:</span>
            <span className="font-bold block">{networkHashrateEnd.toFixed(0)} EH/s</span>
          </div>
        </div>
      </div>
    );
  };

  // getCellColor and getDisplayValue are now imported from @btc-mining/shared-core

  // Handle cell click
  const handleCellClick = (miner, rate, isTwoYear = false) => {
    const details = isTwoYear 
      ? calculateTwoYearProfit(miner, rate)
      : calculateYearlyProfit(miner, rate);
    
    setSelectedDetail({
      miner,
      rate,
      isTwoYear,
      details
    });
  };

  // Update annual increases from current values
  const updateAnnualIncreases = () => {
    const btcIncrease = ((params.btcPriceEnd - params.btcPriceStart) / params.btcPriceStart) * 100;
    const difficultyIncrease = ((params.networkHashrateEnd - params.networkHashrateStart) / params.networkHashrateStart) * 100;
    
    setParams(prev => ({
      ...prev,
      annualBtcPriceIncrease: Math.round(btcIncrease * 10) / 10,
      annualDifficultyIncrease: Math.round(difficultyIncrease * 10) / 10
    }));
  };

  const { btcPriceEnd, networkHashrateEnd } = getCalculatedEndValues();

  // Table Row Component with memo for performance
  const MinerRow = React.memo(({ row, idx, displayMetric, onCellClick }) => {
    return (
      <tr className="border-t hover:bg-gray-50">
        <td className="sticky left-0 bg-white px-4 py-3 border-r">
          <div className="flex items-center justify-between mb-2">
            <div className="font-medium">{row.miner.name}</div>
            <button
              onClick={() => removeMiner(row.miner.id)}
              className="text-red-500 hover:text-red-700 p-1"
              title="Remove miner"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
          
          <div className="text-xs text-gray-500 mb-2">
            <span className="inline-block w-20">{row.miner.manufacturer}</span>
            <span className="inline-block w-16">{row.miner.coolingType}</span>
            <span>{row.miner.releaseYear}</span>
          </div>
          
          {/* Editable fields */}
          <div className="grid grid-cols-3 gap-1 mb-2 text-xs">
            <div>
              <span className="text-gray-500">TH/s:</span>
              <input
                type="number"
                value={row.miner.hashrate}
                onChange={(e) => updateMinerProperty(row.miner.id, 'hashrate', e.target.value)}
                className="w-full px-1 py-0.5 text-xs border border-gray-300 rounded"
                step="1"
              />
            </div>
            <div>
              <span className="text-gray-500">Watts:</span>
              <input
                type="number"
                value={row.miner.power}
                onChange={(e) => updateMinerProperty(row.miner.id, 'power', e.target.value)}
                className="w-full px-1 py-0.5 text-xs border border-gray-300 rounded"
                step="10"
              />
            </div>
            <div>
              <span className="text-gray-500">J/TH:</span>
              <span className="text-xs font-semibold">{row.miner.efficiency}</span>
            </div>
          </div>
          
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-500">$</span>
            <input
              type="number"
              value={minerPrices[row.miner.id] || row.miner.defaultPrice}
              onChange={(e) => updateMinerPrice(row.miner.id, e.target.value)}
              className="w-24 px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              step="100"
            />
          </div>
        </td>

        {row.results.map((result, ridx) => {
          const value = getDisplayValue(result, displayMetric);
          const cellColor = getCellColor(value, displayMetric);
          
          return (
            <td 
              key={ridx} 
              className={`px-4 py-3 text-center ${cellColor} cursor-pointer hover:opacity-80 transition-opacity`}
              onClick={() => onCellClick(row.miner, result.rate, false)}
            >
              <div className="font-semibold">
                {displayMetric === 'roi' 
                  ? `${value.toFixed(1)}%`
                  : `${Math.round(value).toLocaleString()}`
                }
              </div>
              <div className="text-xs opacity-75">
                {result.totalBtcMined.toFixed(3)} BTC
              </div>
            </td>
          );
        })}
      </tr>
    );
  });

  return (
    <div className="w-full p-6 bg-gray-50 min-h-screen">
      {/* Welcome Modal */}
      {showWelcome && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-md shadow-2xl">
            <h2 className="text-2xl font-bold mb-4">Welcome to Bitcoin Mining Calculator!</h2>
            <ul className="space-y-2 mb-6 text-sm">
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">✓</span>
                <span>Compare 20+ popular Bitcoin miners</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">✓</span>
                <span>Adjust electricity rates for your location</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">✓</span>
                <span>See 2-year projections with tax calculations</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">✓</span>
                <span>Save and compare different scenarios</span>
              </li>
            </ul>
            <button 
              onClick={() => {
                setShowWelcome(false);
                localStorage.setItem('hasVisited', 'true');
              }}
              className="w-full bg-orange-600 text-white py-3 rounded-lg hover:bg-orange-700 transition-colors font-semibold"
            >
              Get Started
            </button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-lg p-8 relative">
        {/* Loading Overlay */}
        {isCalculating && (
          <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-10 rounded-lg">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="w-12 h-12 animate-spin text-orange-600" />
              <span className="text-gray-600">Calculating...</span>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <Calculator className="w-8 h-8 text-orange-600" />
          <h1 className="text-3xl font-bold text-gray-900">Bitcoin Mining Profitability Calculator</h1>
        </div>

        <p className="text-gray-600 mb-6">
          Calculate after-tax profits for mining hardware. Click any cell for detailed monthly breakdown.
          <span className="text-sm text-blue-600 ml-2">(Tax-optimized with 2-year projections)</span>
        </p>

        {/* Calculator Mode Toggle */}
        <div className="bg-gradient-to-r from-orange-50 to-yellow-50 border border-orange-200 rounded-lg p-4 mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <span className="font-medium text-gray-700">Calculator Mode:</span>
              <div className="flex rounded-lg overflow-hidden border border-orange-300">
                <button
                  onClick={() => setCalculatorMode('profitability')}
                  className={`px-4 py-2 text-sm font-medium flex items-center gap-2 transition-colors ${
                    calculatorMode === 'profitability'
                      ? 'bg-orange-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-orange-50'
                  }`}
                >
                  <Calculator className="w-4 h-4" />
                  Profitability
                </button>
                <button
                  onClick={() => setCalculatorMode('acquisition')}
                  className={`px-4 py-2 text-sm font-medium flex items-center gap-2 transition-colors ${
                    calculatorMode === 'acquisition'
                      ? 'bg-orange-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-orange-50'
                  }`}
                >
                  <Target className="w-4 h-4" />
                  Acquisition
                </button>
              </div>
            </div>
            {calculatorMode === 'acquisition' && (
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700">Target Profit ($):</label>
                <input
                  type="number"
                  value={targetProfit}
                  onChange={(e) => setTargetProfit(Math.max(0, parseFloat(e.target.value) || 0))}
                  className="w-28 px-3 py-2 border border-orange-300 rounded-md text-sm focus:ring-2 focus:ring-orange-500"
                  step="100"
                  min="0"
                />
              </div>
            )}
          </div>
          <p className="text-sm text-gray-600 mt-2">
            {calculatorMode === 'profitability'
              ? 'Shows net profit after taxes for each miner at different electricity rates.'
              : 'Shows maximum acquisition price to achieve your target profit at each electricity rate.'}
          </p>
        </div>

        {/* Quick Actions Bar */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex flex-wrap gap-3 items-center justify-between">
          <div className="flex gap-3">
            <button
              onClick={() => loadPreset('current')}
              className="text-sm bg-white px-3 py-1 rounded border hover:bg-gray-50 transition-colors"
            >
              Current Market
            </button>
            <button
              onClick={() => loadPreset('conservative')}
              className="text-sm bg-white px-3 py-1 rounded border hover:bg-gray-50 transition-colors"
            >
              Conservative
            </button>
            <button
              onClick={() => loadPreset('bullish')}
              className="text-sm bg-white px-3 py-1 rounded border hover:bg-gray-50 transition-colors"
            >
              Bullish 2025
            </button>
          </div>
          <button
            onClick={shareResults}
            className="text-sm bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 flex items-center gap-1 transition-colors"
          >
            <Share2 className="w-3 h-3" /> Share Results
          </button>
        </div>

        {/* Quick Insights Summary */}
        {quickInsights && (
          <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4 mb-6">
            <h3 className="text-lg font-semibold mb-2">Quick Insights</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Most Profitable:</span>
                <span className="font-bold text-green-600 block">{quickInsights.mostProfitable}</span>
                <span className="text-xs text-gray-500">ROI: {quickInsights.mostProfitableROI.toFixed(1)}%</span>
              </div>
              <div>
                <span className="text-gray-600">Best Efficiency:</span>
                <span className="font-bold text-blue-600 block">{quickInsights.mostEfficient}</span>
                <span className="text-xs text-gray-500">{quickInsights.mostEfficientValue} J/TH</span>
              </div>
              <div>
                <span className="text-gray-600">Avg Breakeven:</span>
                <span className="font-bold block">${quickInsights.avgBreakevenElectricity.toFixed(3)}/kWh</span>
                <span className="text-xs text-gray-500">Electricity rate</span>
              </div>
              <div>
                <span className="text-gray-600">Total Miners:</span>
                <span className="font-bold block">{miners.length} models</span>
                <span className="text-xs text-gray-500">In comparison</span>
              </div>
            </div>
          </div>
        )}

        {/* Network Hashrate Widget */}
        <HashrateWidget />

        {/* Data Management Controls */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Save className="w-5 h-5" />
            Data Management
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Scenario Management */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Saved Scenarios</label>
              <div className="flex gap-2">
                <select 
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                  onChange={(e) => e.target.value && loadScenario(e.target.value)}
                  value=""
                >
                  <option value="">Load Scenario...</option>
                  {Object.keys(savedScenarios).map(name => (
                    <option key={name} value={name}>{name}</option>
                  ))}
                </select>
                <button
                  onClick={() => setShowScenarioModal(true)}
                  className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                  title="Save Current Scenario"
                >
                  <Save className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Import/Export */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Import/Export</label>
              <div className="flex gap-2">
                <button
                  onClick={exportMiners}
                  className="flex-1 px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm flex items-center gap-1"
                >
                  <Download className="w-4 h-4" />
                  Export
                </button>
                <label className="flex-1 px-3 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 text-sm flex items-center gap-1 cursor-pointer">
                  <Upload className="w-4 h-4" />
                  Import
                  <input
                    type="file"
                    accept=".json"
                    onChange={importMiners}
                    className="hidden"
                  />
                </label>
              </div>
            </div>

            {/* Miner Management */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Miners</label>
              <div className="flex gap-2">
                <button
                  onClick={addNewMiner}
                  className="flex-1 px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm flex items-center gap-1"
                >
                  <Plus className="w-4 h-4" />
                  Add Miner
                </button>
                <span className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md text-sm flex items-center">
                  {miners.length} total
                </span>
              </div>
            </div>

            {/* Reset */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Reset</label>
              <button
                onClick={resetToDefaults}
                className="w-full px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
              >
                Reset All Data
              </button>
            </div>
          </div>
        </div>

        {/* Parameters */}
        <div className="bg-gray-50 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Global Parameters
          </h2>
          
          {/* Depreciation Toggle */}
          <div className="mb-4 p-4 bg-indigo-50 rounded-lg">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={params.useBonusDepreciation}
                onChange={(e) => setParams({...params, useBonusDepreciation: e.target.checked})}
                className="w-4 h-4 text-indigo-600"
              />
              <span className="font-medium text-indigo-900">
                {params.useBonusDepreciation ? '100% Bonus Depreciation (Year 1)' : 'MACRS 5-Year Depreciation'}
              </span>
            </label>
            {!params.useBonusDepreciation && (
              <div className="mt-2 text-sm text-indigo-700">
                Year 1: 20%, Year 2: 32%, Year 3: 19.2%, Year 4: 11.52%, Year 5: 11.52%, Year 6: 5.76%
              </div>
            )}
          </div>
          
          {/* Mode Toggle */}
          <div className="mb-4 p-4 bg-blue-50 rounded-lg">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={params.useAnnualIncreases}
                onChange={(e) => setParams({...params, useAnnualIncreases: e.target.checked})}
                className="w-4 h-4 text-blue-600"
              />
              <span className="font-medium text-blue-900">Use Annual Increase Rates (%) instead of End Values</span>
            </label>
            {!params.useAnnualIncreases && (
              <button
                onClick={updateAnnualIncreases}
                className="mt-2 text-sm text-blue-600 hover:text-blue-800"
              >
                Calculate increases from current start/end values →
              </button>
            )}
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                BTC Price Start ($)
              </label>
              <input
                type="number"
                value={params.btcPriceStart}
                onChange={(e) => setParams({...params, btcPriceStart: parseFloat(e.target.value) || 0})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            
            {params.useAnnualIncreases ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Annual BTC Price Increase (%)
                </label>
                <input
                  type="number"
                  value={params.annualBtcPriceIncrease}
                  onChange={(e) => setParams({...params, annualBtcPriceIncrease: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  step="0.1"
                />
                <div className="text-xs text-gray-500 mt-1">
                  End: ${btcPriceEnd.toLocaleString()}
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  BTC Price End ($)
                </label>
                <input
                  type="number"
                  value={params.btcPriceEnd}
                  onChange={(e) => setParams({...params, btcPriceEnd: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Network Hashrate Start (EH/s)
              </label>
              <input
                type="number"
                value={params.networkHashrateStart}
                onChange={(e) => setParams({...params, networkHashrateStart: parseFloat(e.target.value) || 0})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            
            {params.useAnnualIncreases ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Annual Difficulty Increase (%)
                </label>
                <input
                  type="number"
                  value={params.annualDifficultyIncrease}
                  onChange={(e) => setParams({...params, annualDifficultyIncrease: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  step="0.1"
                />
                <div className="text-xs text-gray-500 mt-1">
                  End: {networkHashrateEnd.toFixed(0)} EH/s
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Network Hashrate End (EH/s)
                </label>
                <input
                  type="number"
                  value={params.networkHashrateEnd}
                  onChange={(e) => setParams({...params, networkHashrateEnd: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Pool Fee (%)
              </label>
              <input
                type="number"
                value={params.poolFee}
                onChange={(e) => setParams({...params, poolFee: parseFloat(e.target.value) || 0})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Federal Tax Rate (%)
              </label>
              <input
                type="number"
                value={params.taxRate}
                onChange={(e) => setParams({...params, taxRate: parseFloat(e.target.value) || 0})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                State Tax Rate (%)
              </label>
              <input
                type="number"
                value={params.stateRate}
                onChange={(e) => setParams({...params, stateRate: parseFloat(e.target.value) || 0})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>
        </div>

        {/* Metric Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Display Metric:</label>
          <div className="flex gap-4 flex-wrap">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                value="netProfit"
                checked={displayMetric === 'netProfit'}
                onChange={(e) => setDisplayMetric(e.target.value)}
                className="text-blue-600"
              />
              <span>Net Profit (After Tax - Purchase Price)</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                value="afterTaxProfit"
                checked={displayMetric === 'afterTaxProfit'}
                onChange={(e) => setDisplayMetric(e.target.value)}
                className="text-blue-600"
              />
              <span>After-Tax Profit</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                value="operationalProfit"
                checked={displayMetric === 'operationalProfit'}
                onChange={(e) => setDisplayMetric(e.target.value)}
                className="text-blue-600"
              />
              <span>Operational Profit</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                value="roi"
                checked={displayMetric === 'roi'}
                onChange={(e) => setDisplayMetric(e.target.value)}
                className="text-blue-600"
              />
              <span>ROI % (Annualized for 2-year)</span>
            </label>
          </div>
        </div>

        {/* Toggle for 2-year analysis (only in profitability mode) */}
        {calculatorMode === 'profitability' && (
          <div className="mb-6">
            <button
              onClick={() => setShowTwoYearAnalysis(!showTwoYearAnalysis)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <TrendingUp className="w-4 h-4" />
              {showTwoYearAnalysis ? 'Hide' : 'Show'} 2-Year Cumulative Analysis
            </button>
          </div>
        )}

        {/* Acquisition Matrix Table (when in acquisition mode) */}
        {calculatorMode === 'acquisition' && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-4 text-orange-900">
              <Target className="w-5 h-5 inline mr-2" />
              Maximum Acquisition Price Matrix
              <span className="text-sm font-normal text-orange-600 ml-2">
                (Target: ${targetProfit.toLocaleString()} profit)
              </span>
            </h3>
            <div className="bg-orange-50 rounded-lg p-4 mb-4">
              <h4 className="font-semibold text-orange-900 mb-2">How to Read This:</h4>
              <ul className="text-sm text-orange-800 space-y-1">
                <li>• Each cell shows the <strong>maximum price</strong> you can pay for that miner to achieve ${targetProfit.toLocaleString()} profit</li>
                <li>• $/TH shows the price per terahash at that acquisition price</li>
                <li>• Higher values mean more room to pay for the miner</li>
                <li>• Compare to current market prices to find deals</li>
              </ul>
            </div>
            <div className="overflow-x-auto border border-orange-200 rounded-lg">
              <table className="w-full">
                <thead className="bg-orange-100">
                  <tr>
                    <th className="sticky left-0 bg-orange-100 px-4 py-3 text-left font-semibold border-r min-w-[280px]">
                      Miner Model
                    </th>
                    {ELECTRICITY_RATES.map(rate => (
                      <th key={rate} className="px-4 py-3 text-center font-semibold min-w-[120px]">
                        ${rate.toFixed(3)}/kWh
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {acquisitionMatrix.map((row, idx) => (
                    <tr key={row.miner.id} className="border-t hover:bg-orange-50">
                      <td className="sticky left-0 bg-white px-4 py-3 border-r">
                        <div className="font-medium">{row.miner.name}</div>
                        <div className="text-xs text-gray-500 mb-1">
                          {row.miner.hashrate} TH/s | {row.miner.power}W | {row.miner.efficiency} J/TH
                        </div>
                        <div className="text-xs text-blue-600">
                          Current: ${(minerPrices[row.miner.id] || row.miner.defaultPrice).toLocaleString()}
                        </div>
                      </td>
                      {row.results.map((result, ridx) => {
                        const currentPrice = minerPrices[row.miner.id] || row.miner.defaultPrice;
                        const isGoodDeal = result.maxAcquisitionPrice > currentPrice;
                        const cellColor = result.maxAcquisitionPrice > currentPrice * 1.2
                          ? 'bg-green-200'
                          : result.maxAcquisitionPrice > currentPrice
                          ? 'bg-green-100'
                          : result.maxAcquisitionPrice > currentPrice * 0.8
                          ? 'bg-yellow-100'
                          : result.maxAcquisitionPrice > 0
                          ? 'bg-red-100'
                          : 'bg-red-200';

                        return (
                          <td
                            key={ridx}
                            className={`px-4 py-3 text-center ${cellColor} cursor-pointer hover:opacity-80 transition-opacity`}
                            title={`Op. Profit: $${Math.round(result.operationalProfit).toLocaleString()}`}
                          >
                            <div className="font-semibold">
                              ${result.maxAcquisitionPrice.toLocaleString()}
                            </div>
                            <div className="text-xs opacity-75">
                              ${result.dollarPerTH}/TH
                            </div>
                            {isGoodDeal && (
                              <div className="text-xs text-green-700 font-medium">
                                +${(result.maxAcquisitionPrice - currentPrice).toLocaleString()} margin
                              </div>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Profit Matrix Table (when in profitability mode) */}
        {calculatorMode === 'profitability' && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-4">
              Year 1 Profitability Matrix
              <span className="text-sm font-normal text-gray-600 ml-2">({miners.length} miners)</span>
            </h3>
            <div className="overflow-x-auto border border-gray-200 rounded-lg">
              <table className="w-full">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="sticky left-0 bg-gray-100 px-4 py-3 text-left font-semibold border-r min-w-[280px]">
                      Miner Model
                    </th>
                    {ELECTRICITY_RATES.map(rate => (
                      <th key={rate} className="px-4 py-3 text-center font-semibold min-w-[100px]">
                        ${rate.toFixed(3)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {profitMatrix.map((row, idx) => (
                    <MinerRow
                      key={row.miner.id}
                      row={row}
                      idx={idx}
                      displayMetric={displayMetric}
                      onCellClick={handleCellClick}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 2-Year Profit Matrix Table (only in profitability mode) */}
        {calculatorMode === 'profitability' && showTwoYearAnalysis && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-4 text-purple-900">Years 1+2 Cumulative Profitability Matrix</h3>
            <div className="bg-purple-50 rounded-lg p-4 mb-4">
              <h4 className="font-semibold text-purple-900 mb-2">2-Year Analysis Notes:</h4>
              <ul className="text-sm text-purple-800 space-y-1">
                <li>• <strong>Depreciation: </strong>
                  {params.useBonusDepreciation 
                    ? '100% in Year 1, none in Year 2'
                    : 'Year 1: 20%, Year 2: 32% (MACRS)'}
                </li>
                <li>• Taxes apply to both years' operational profits</li>
                <li>• ROI shown is annualized (total 2-year ROI ÷ 2)</li>
                <li>• Year 2 continues growth trends from Year 1</li>
              </ul>
            </div>
            <div className="overflow-x-auto border border-purple-200 rounded-lg">
              <table className="w-full">
                <thead className="bg-purple-100">
                  <tr>
                    <th className="sticky left-0 bg-purple-100 px-4 py-3 text-left font-semibold border-r min-w-[220px]">
                      Miner Model
                    </th>
                    {ELECTRICITY_RATES.map(rate => (
                      <th key={rate} className="px-4 py-3 text-center font-semibold min-w-[100px]">
                        ${rate.toFixed(3)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {twoYearProfitMatrix.map((row, idx) => (
                    <tr key={idx} className="border-t hover:bg-purple-50">
                      <td className="sticky left-0 bg-white px-4 py-3 border-r">
                        <div className="font-medium">{row.miner.name}</div>
                        <div className="text-xs text-gray-500 mb-2">
                          {row.miner.efficiency} J/TH | {row.miner.hashrate} TH/s
                        </div>
                        <div className="text-xs text-purple-600">
                          Price: ${(minerPrices[row.miner.id] || row.miner.defaultPrice).toLocaleString()}
                        </div>
                      </td>

                      {row.results.map((result, ridx) => {
                        const value = getDisplayValue(result, displayMetric, true);
                        const cellColor = getCellColor(value, displayMetric);
                        
                        return (
                          <td 
                            key={ridx} 
                            className={`px-4 py-3 text-center ${cellColor} cursor-pointer hover:opacity-80 transition-opacity`}
                            onClick={() => handleCellClick(row.miner, result.rate, true)}
                          >
                            <div className="font-semibold">
                              {displayMetric === 'roi' 
                                ? `${value.toFixed(1)}%`
                                : `${Math.round(value).toLocaleString()}`
                              }
                            </div>
                            <div className="text-xs opacity-75">
                              {result.totalBtcMined.toFixed(3)} BTC
                            </div>
                            {displayMetric === 'roi' && (
                              <div className="text-xs opacity-60">
                                {result.roi.toFixed(1)}% total
                              </div>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <Info className="w-4 h-4" />
              Color Legend
            </h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-300 rounded"></div>
                <span>Excellent Returns</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-200 rounded"></div>
                <span>Very Good</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-100 rounded"></div>
                <span>Good</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-50 rounded"></div>
                <span>Profitable</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-50 rounded"></div>
                <span>Small Loss</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-100 rounded"></div>
                <span>Moderate Loss</span>
              </div>
            </div>
          </div>
          
          <div className="bg-blue-50 rounded-lg p-4">
            <h3 className="font-semibold mb-2">Key Features</h3>
            <ul className="text-sm space-y-1">
              <li>• <strong>Edit All Values:</strong> Click on any miner property to edit</li>
              <li>• <strong>Tax Calculations:</strong> Includes bonus depreciation & tax rates</li>
              <li>• <strong>Save Scenarios:</strong> Compare different market conditions</li>
              <li>• <strong>2-Year Analysis:</strong> See longer-term profitability</li>
              <li>• <strong>Auto-Save:</strong> All changes save to your browser</li>
              <li>• BTC: ${params.btcPriceStart.toLocaleString()} → ${btcPriceEnd.toLocaleString()}</li>
              <li>• Hashrate: {params.networkHashrateStart} → {networkHashrateEnd.toFixed(0)} EH/s</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Scenario Save Modal */}
      {showScenarioModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="px-6 py-4 border-b flex items-center justify-between">
              <h3 className="text-lg font-semibold">Save Current Scenario</h3>
              <button
                onClick={() => setShowScenarioModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Scenario Name
                </label>
                <input
                  type="text"
                  value={newScenarioName}
                  onChange={(e) => setNewScenarioName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="e.g., Conservative 2025, Bull Run, etc."
                  onKeyPress={(e) => e.key === 'Enter' && saveScenario()}
                />
              </div>
              
              <div className="text-sm text-gray-600 mb-4">
                This will save your current parameters, miners, and prices.
              </div>
              
              {Object.keys(savedScenarios).length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Existing Scenarios:</h4>
                  <div className="max-h-32 overflow-y-auto">
                    {Object.keys(savedScenarios).map(name => (
                      <div key={name} className="flex items-center justify-between py-1">
                        <span className="text-sm">{name}</span>
                        <button
                          onClick={() => deleteScenario(name)}
                          className="text-red-500 hover:text-red-700 p-1"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="flex gap-3">
                <button
                  onClick={() => setShowScenarioModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={saveScenario}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Save Scenario
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal for detailed calculations */}
      {selectedDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="px-6 py-4 border-b flex items-center justify-between">
              <h3 className="text-xl font-semibold">
                {selectedDetail.miner.fullName} at ${selectedDetail.rate}/kWh
              </h3>
              <button
                onClick={() => setSelectedDetail(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
              {selectedDetail.isTwoYear ? (
                <div>
                  {/* 2-Year Summary */}
                  <div className="mb-6 bg-purple-50 rounded-lg p-4">
                    <h4 className="font-semibold text-purple-900 mb-3">2-Year Summary</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <div className="text-sm text-gray-600">Total BTC Mined</div>
                        <div className="font-semibold">{selectedDetail.details.totalBtcMined.toFixed(4)}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Total Op. Profit</div>
                        <div className="font-semibold">${selectedDetail.details.operationalProfit.toLocaleString()}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">After-Tax Profit</div>
                        <div className="font-semibold">${selectedDetail.details.afterTaxProfit.toLocaleString()}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Annualized ROI</div>
                        <div className="font-semibold">{selectedDetail.details.annualizedRoi.toFixed(1)}%</div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Year 1 Details */}
                  <div className="mb-6">
                    <h4 className="font-semibold mb-3">Year 1 Monthly Breakdown</h4>
                    <div className="mb-3 bg-blue-50 rounded p-3">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                        <div>
                          <span className="text-gray-600">Total Revenue:</span>
                          <span className="font-semibold ml-1">${selectedDetail.details.year1Details.totalRevenue.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Electricity:</span>
                          <span className="font-semibold ml-1 text-red-600">-${selectedDetail.details.year1Details.totalElectricity.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Depreciation:</span>
                          <span className="font-semibold ml-1 text-green-600">-${selectedDetail.details.year1Details.depreciation.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Tax:</span>
                          <span className="font-semibold ml-1 text-red-600">-${selectedDetail.details.year1Details.totalTax.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left py-2">Month</th>
                            <th className="text-right py-2">BTC Price</th>
                            <th className="text-right py-2">Network (EH/s)</th>
                            <th className="text-right py-2">BTC Mined</th>
                            <th className="text-right py-2">Revenue</th>
                            <th className="text-right py-2">Electricity</th>
                            <th className="text-right py-2">Op. Profit</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedDetail.details.year1Details.monthlyData.map((month) => (
                            <tr key={month.month} className="border-b">
                              <td className="py-2">{month.month}</td>
                              <td className="text-right py-2">${month.btcPrice.toLocaleString()}</td>
                              <td className="text-right py-2">{month.networkHashrate.toFixed(0)}</td>
                              <td className="text-right py-2">{month.btcMinedNet.toFixed(5)}</td>
                              <td className="text-right py-2">${month.netRevenue.toLocaleString()}</td>
                              <td className="text-right py-2 text-red-600">-${month.electricityCost.toLocaleString()}</td>
                              <td className="text-right py-2 font-semibold">${month.operationalProfit.toLocaleString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                  
                  {/* Year 2 Details */}
                  <div>
                    <h4 className="font-semibold mb-3">Year 2 Monthly Breakdown</h4>
                    <div className="mb-3 bg-purple-50 rounded p-3">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                        <div>
                          <span className="text-gray-600">Total Revenue:</span>
                          <span className="font-semibold ml-1">${selectedDetail.details.year2Details.totalRevenue.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Electricity:</span>
                          <span className="font-semibold ml-1 text-red-600">-${selectedDetail.details.year2Details.totalElectricity.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Depreciation:</span>
                          <span className="font-semibold ml-1 text-green-600">-${selectedDetail.details.year2Details.depreciation.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Tax:</span>
                          <span className="font-semibold ml-1 text-red-600">-${selectedDetail.details.year2Details.totalTax.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left py-2">Month</th>
                            <th className="text-right py-2">BTC Price</th>
                            <th className="text-right py-2">Network (EH/s)</th>
                            <th className="text-right py-2">BTC Mined</th>
                            <th className="text-right py-2">Revenue</th>
                            <th className="text-right py-2">Electricity</th>
                            <th className="text-right py-2">Op. Profit</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedDetail.details.year2Details.monthlyData.map((month) => (
                            <tr key={month.month} className="border-b">
                              <td className="py-2">{month.month}</td>
                              <td className="text-right py-2">${month.btcPrice.toLocaleString()}</td>
                              <td className="text-right py-2">{month.networkHashrate.toFixed(0)}</td>
                              <td className="text-right py-2">{month.btcMinedNet.toFixed(5)}</td>
                              <td className="text-right py-2">${month.netRevenue.toLocaleString()}</td>
                              <td className="text-right py-2 text-red-600">-${month.electricityCost.toLocaleString()}</td>
                              <td className="text-right py-2 font-semibold">${month.operationalProfit.toLocaleString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ) : (
                <div>
                  {/* Year 1 Summary */}
                  <div className="mb-6 bg-blue-50 rounded-lg p-4">
                    <h4 className="font-semibold text-blue-900 mb-3">Year 1 Summary</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <div className="text-sm text-gray-600">Total BTC Mined</div>
                        <div className="font-semibold">{selectedDetail.details.totalBtcMined.toFixed(4)}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Op. Profit</div>
                        <div className="font-semibold">${selectedDetail.details.totalOperationalProfit.toLocaleString()}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">After-Tax Profit</div>
                        <div className="font-semibold">${selectedDetail.details.afterTaxProfit.toLocaleString()}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">ROI</div>
                        <div className="font-semibold">{selectedDetail.details.roi.toFixed(1)}%</div>
                      </div>
                    </div>
                    <div className="mt-3 pt-3 border-t grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                      <div>
                        <span className="text-gray-600">Depreciation:</span>
                        <span className="font-semibold ml-1 text-green-600">${selectedDetail.details.depreciation.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Total Tax:</span>
                        <span className="font-semibold ml-1 text-red-600">${selectedDetail.details.totalTax.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Equipment Cost:</span>
                        <span className="font-semibold ml-1">${selectedDetail.details.minerPrice.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Monthly Details */}
                  <h4 className="font-semibold mb-3">Monthly Breakdown</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2">Month</th>
                          <th className="text-right py-2">BTC Price</th>
                          <th className="text-right py-2">Network (EH/s)</th>
                          <th className="text-right py-2">BTC Mined</th>
                          <th className="text-right py-2">Revenue</th>
                          <th className="text-right py-2">Electricity</th>
                          <th className="text-right py-2">Op. Profit</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedDetail.details.monthlyData.map((month) => (
                          <tr key={month.month} className="border-b">
                            <td className="py-2">{month.month}</td>
                            <td className="text-right py-2">${month.btcPrice.toLocaleString()}</td>
                            <td className="text-right py-2">{month.networkHashrate.toFixed(0)}</td>
                            <td className="text-right py-2">{month.btcMinedNet.toFixed(5)}</td>
                            <td className="text-right py-2">${month.netRevenue.toLocaleString()}</td>
                            <td className="text-right py-2 text-red-600">-${month.electricityCost.toLocaleString()}</td>
                            <td className="text-right py-2 font-semibold">${month.operationalProfit.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Wrap the component with ErrorBoundary
const EnhancedMinerProfitMatrixWithErrorBoundary = () => (
  <ErrorBoundary>
    <EnhancedMinerProfitMatrix />
  </ErrorBoundary>
);

export default EnhancedMinerProfitMatrixWithErrorBoundary;