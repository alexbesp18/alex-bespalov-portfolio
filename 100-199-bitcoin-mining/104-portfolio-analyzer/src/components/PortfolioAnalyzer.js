import React, { useState, useMemo, useCallback } from 'react';
import {
  TrendingUp, Wallet, Download, Upload, BarChart3,
  Zap, Bitcoin, Cpu, Brain, AlertTriangle, Plus, Trash2
} from 'lucide-react';
import logger from '../utils/logger';
import {
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell
} from "recharts";

/**
 * Portfolio Analyzer Component
 * 
 * A comprehensive portfolio analysis tool for tracking and optimizing investments including:
 * - Bitcoin cold storage
 * - Growth stocks
 * - MSTR stock positions
 * - BTC mining operations
 * - Options positions (calls/puts)
 * - Debt management
 * - Withdrawal strategy planning
 * 
 * Features:
 * - Real-time portfolio valuation
 * - Mining profitability calculations
 * - Options valuation using Black-Scholes approximation
 * - Risk analysis and concentration metrics
 * - Withdrawal optimization recommendations
 * - Debt payoff strategies
 * 
 * @component
 * @returns {JSX.Element} The Portfolio Analyzer interface
 */
const PortfolioAnalyzer = () => {
  // Asset categories with metadata
  const ASSET_CATEGORIES = {
    btcCold: { name: 'BTC Cold Storage', color: '#F7931A', icon: Bitcoin, type: 'crypto', volatility: 'high' },
    growthStocks: { name: 'Growth Stocks', color: '#10B981', icon: TrendingUp, type: 'equity', volatility: 'high' },
    mstrStock: { name: 'MSTR Stock', color: '#8B5CF6', icon: BarChart3, type: 'equity', volatility: 'extreme' },
    btcMiners: { name: 'BTC Hosted Miners', color: '#6366F1', icon: Cpu, type: 'mining', volatility: 'high' }
  };

  // Default portfolio state
  const DEFAULT_PORTFOLIO = {
    btcCold: { quantity: 0.5, costBasis: 45000 },
    growthStocks: { value: 25000, costBasis: 20000 },
    mstrStock: { shares: 50, costBasis: 350 },
    btcMiners: { totalValue: 15000 }
  };

  // Default mining providers
  const DEFAULT_MINING_PROVIDERS = [
    { id: 1, name: 'Provider 1', hashrate: 150, power: 4500, electricityRate: 0.065, uptime: 98 },
    { id: 2, name: 'Provider 2', hashrate: 200, power: 6000, electricityRate: 0.070, uptime: 97 },
    { id: 3, name: 'Provider 3', hashrate: 100, power: 3200, electricityRate: 0.055, uptime: 99 },
    { id: 4, name: 'Provider 4', hashrate: 50, power: 1500, electricityRate: 0.080, uptime: 95 }
  ];

  // Default options
  const DEFAULT_OPTIONS = [
    { id: 1, underlying: 'IBIT', type: 'call', strike: 50, expiry: '2025-01-17', contracts: 5, costBasis: 2.5 },
    { id: 2, underlying: 'IBIT', type: 'call', strike: 55, expiry: '2025-04-18', contracts: 3, costBasis: 5.0 },
    { id: 3, underlying: 'IBIT', type: 'call', strike: 60, expiry: '2026-01-15', contracts: 2, costBasis: 8.0 },
    { id: 4, underlying: 'MSTR', type: 'call', strike: 400, expiry: '2025-01-17', contracts: 2, costBasis: 15 },
    { id: 5, underlying: 'MSTR', type: 'call', strike: 450, expiry: '2025-04-18', contracts: 2, costBasis: 30 },
    { id: 6, underlying: 'MSTR', type: 'call', strike: 500, expiry: '2026-01-15', contracts: 1, costBasis: 50 },
    { id: 7, underlying: 'NVDA', type: 'call', strike: 140, expiry: '2026-01-15', contracts: 3, costBasis: 12 },
    { id: 8, underlying: 'NVDA', type: 'call', strike: 160, expiry: '2027-01-15', contracts: 2, costBasis: 18 },
    { id: 9, underlying: 'IBIT', type: 'call', strike: 75, expiry: '2027-12-17', contracts: 5, costBasis: 15 },
    { id: 10, underlying: 'MSTR', type: 'call', strike: 600, expiry: '2027-01-15', contracts: 2, costBasis: 80 }
  ];

  // Extended timeframes for projections
  const PROJECTION_TIMEFRAMES = [
    { key: 'month3', label: '3 Months', months: 3 },
    { key: 'month6', label: '6 Months', months: 6 },
    { key: 'year1', label: '1 Year', months: 12 },
    { key: 'year2', label: '2 Years', months: 24 },
    { key: 'year3', label: '3 Years', months: 36 }
  ];

  // Default price projections with extended timeframes
  const DEFAULT_PROJECTIONS = {
    btc: {
      current: 100000,
      month3: 115000,
      month6: 135000,
      year1: 180000,
      year2: 250000,
      year3: 350000
    },
    mstr: {
      current: 400,
      month3: 500,
      month6: 650,
      year1: 900,
      year2: 1400,
      year3: 2000
    },
    nvda: {
      current: 135,
      month3: 145,
      month6: 160,
      year1: 185,
      year2: 220,
      year3: 280
    },
    ibit: {
      current: 48,
      month3: 55,
      month6: 65,
      year1: 86,
      year2: 120,
      year3: 168
    },
    miningParams: {
      networkHashrate: 900,
      monthlyDifficultyGrowth: 2.5,
      blockReward: 3.125,
      blocksPerDay: 144
    }
  };

  // Default debt info
  const DEFAULT_DEBT = {
    creditCards: [
      { name: 'Chase Sapphire', balance: 8500, apr: 24.99, minPayment: 250 },
      { name: 'Amex Gold', balance: 5200, apr: 22.99, minPayment: 150 },
      { name: 'Capital One', balance: 3800, apr: 26.99, minPayment: 120 }
    ],
    totalDebt: 17500,
    monthlyMinPayment: 520,
    targetPayoffMonths: 12
  };

  // State management - using in-memory state only (no localStorage)
  const [portfolio, setPortfolio] = useState(DEFAULT_PORTFOLIO);
  const [miningProviders, setMiningProviders] = useState(DEFAULT_MINING_PROVIDERS);
  const [options, setOptions] = useState(DEFAULT_OPTIONS);
  const [projections, setProjections] = useState(DEFAULT_PROJECTIONS);
  const [debt, setDebt] = useState(DEFAULT_DEBT);
  const [withdrawalStrategy, setWithdrawalStrategy] = useState({
    monthlyTarget: 2000,
    preserveCore: true,
    coreAssets: ['btcCold', 'btcMiners'],
    minCoreRetention: 0.7,
    riskTolerance: 'moderate',
    taxConsideration: true
  });

  const [activeTab, setActiveTab] = useState('overview');
  const [showAddOption, setShowAddOption] = useState(false);
  const [newOption, setNewOption] = useState({
    underlying: 'IBIT',
    type: 'call',
    strike: 50,
    expiry: '',
    contracts: 1,
    costBasis: 0
  });

  /**
   * Validates and clamps a number value within specified bounds
   * @param {string|number} value - The value to validate
   * @param {number} [min=0] - Minimum allowed value
   * @param {number} [max=Infinity] - Maximum allowed value
   * @returns {number} Validated number clamped between min and max
   * @example
   * validateNumber('123', 0, 100) // Returns 100
   * validateNumber('abc', 0, 100) // Returns 0 (min)
   */
  const validateNumber = (value, min = 0, max = Infinity) => {
    const num = parseFloat(value);
    if (isNaN(num)) return min;
    return Math.max(min, Math.min(max, num));
  };

  /**
   * Calculates the number of months until an option expiry date
   * @param {string} expiryDate - ISO date string (YYYY-MM-DD)
   * @returns {number} Number of months until expiry (0 if expired or invalid)
   * @example
   * getMonthsToExpiry('2025-12-31') // Returns ~12 if current date is Jan 2025
   */
  const getMonthsToExpiry = (expiryDate) => {
    try {
      const expiry = new Date(expiryDate);
      const now = new Date();
      if (isNaN(expiry.getTime())) return 0;
      return Math.max(0, (expiry - now) / (1000 * 60 * 60 * 24 * 30.42));
    } catch (error) {
      logger.warn('Date calculation error:', error);
      return 0;
    }
  };

  /**
   * Calculates mining profitability metrics for a given provider
   * 
   * Computes BTC mined, revenue, electricity costs, profit, and efficiency metrics
   * over a specified time period, accounting for network difficulty growth.
   * 
   * @param {Object} provider - Mining provider configuration
   * @param {number} provider.hashrate - Hashrate in TH/s
   * @param {number} provider.power - Power consumption in watts
   * @param {number} provider.electricityRate - Electricity cost per kWh
   * @param {number} [provider.uptime=98] - Uptime percentage
   * @param {number} btcPrice - Current BTC price in USD
   * @param {number} [months=12] - Number of months to project
   * @returns {Object} Mining metrics including:
   *   - totalBtcMined: Total BTC mined over period
   *   - totalRevenue: Total revenue in USD
   *   - totalElectricity: Total electricity costs
   *   - profit: Net profit (revenue - electricity)
   *   - profitMargin: Profit margin percentage
   *   - monthlyAvgProfit: Average monthly profit
   *   - efficiency: Power efficiency in J/TH
   *   - breakevenPrice: BTC price needed to break even
   */
  const calculateMiningMetrics = useCallback((provider, btcPrice, months = 12) => {
    try {
      const { hashrate, power, electricityRate, uptime = 98 } = provider;
      const { networkHashrate, monthlyDifficultyGrowth, blockReward, blocksPerDay } = projections.miningParams;
      
      // Validate inputs
      if (!hashrate || !power || !btcPrice || months <= 0) {
        return {
          totalBtcMined: 0,
          totalRevenue: 0,
          totalElectricity: 0,
          profit: 0,
          profitMargin: 0,
          monthlyAvgProfit: 0,
          efficiency: power && hashrate ? power / hashrate : 0,
          breakevenPrice: 0
        };
      }
      
      let totalBtcMined = 0;
      let totalRevenue = 0;
      let totalElectricity = 0;
      
      for (let month = 0; month < months; month++) {
        const growthFactor = Math.pow(1 + validateNumber(monthlyDifficultyGrowth, 0, 50) / 100, month);
        const currentNetworkHashrate = validateNumber(networkHashrate, 1) * growthFactor;
        
        const shareOfNetwork = (validateNumber(hashrate, 0) / (currentNetworkHashrate * 1000000)) * (validateNumber(uptime, 0, 100) / 100);
        
        const btcPerDay = shareOfNetwork * validateNumber(blocksPerDay, 0) * validateNumber(blockReward, 0);
        const btcPerMonth = btcPerDay * 30.42;
        
        const monthlyRevenue = btcPerMonth * validateNumber(btcPrice, 0);
        
        const powerKw = validateNumber(power, 0) / 1000;
        const monthlyElectricity = powerKw * 24 * 30.42 * validateNumber(electricityRate, 0);
        
        totalBtcMined += btcPerMonth;
        totalRevenue += monthlyRevenue;
        totalElectricity += monthlyElectricity;
      }
      
      const profit = totalRevenue - totalElectricity;
      const profitMargin = totalRevenue > 0 ? (profit / totalRevenue) * 100 : 0;
      
      return {
        totalBtcMined,
        totalRevenue,
        totalElectricity,
        profit,
        profitMargin,
        monthlyAvgProfit: profit / months,
        efficiency: validateNumber(power, 0) / validateNumber(hashrate, 1),
        breakevenPrice: totalBtcMined > 0 ? totalElectricity / totalBtcMined : 0
      };
    } catch (error) {
      logger.error('Mining calculation error:', error);
      return {
        totalBtcMined: 0,
        totalRevenue: 0,
        totalElectricity: 0,
        profit: 0,
        profitMargin: 0,
        monthlyAvgProfit: 0,
        efficiency: 0,
        breakevenPrice: 0
      };
    }
  }, [projections.miningParams]);

  // Calculate total mining value
  const miningTotalMetrics = useMemo(() => {
    try {
      const totalHashrate = miningProviders.reduce((sum, p) => sum + validateNumber(p.hashrate, 0), 0);
      const totalPower = miningProviders.reduce((sum, p) => sum + validateNumber(p.power, 0), 0);
      const weightedElectricityRate = totalHashrate > 0 
        ? miningProviders.reduce((sum, p) => sum + validateNumber(p.electricityRate, 0) * validateNumber(p.hashrate, 0), 0) / totalHashrate
        : 0;
      
      const combinedProvider = {
        hashrate: totalHashrate,
        power: totalPower,
        electricityRate: weightedElectricityRate,
        uptime: 97
      };
      
      return calculateMiningMetrics(combinedProvider, validateNumber(projections.btc.current, 0), 12);
    } catch (error) {
      logger.error('Total mining metrics error:', error);
      return {
        totalBtcMined: 0,
        totalRevenue: 0,
        totalElectricity: 0,
        profit: 0,
        profitMargin: 0,
        monthlyAvgProfit: 0,
        efficiency: 0,
        breakevenPrice: 0
      };
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [miningProviders, projections.btc.current, calculateMiningMetrics]);

  /**
   * Calculates option value using Black-Scholes approximation
   * 
   * Computes intrinsic value, time value, and projected value at expiry
   * for call or put options.
   * 
   * @param {Object} option - Option configuration
   * @param {number} option.strike - Strike price
   * @param {number} option.contracts - Number of contracts
   * @param {string} option.type - Option type ('call' or 'put')
   * @param {number} option.costBasis - Cost basis per contract
   * @param {number} currentPrice - Current underlying asset price
   * @param {number} projectedPrice - Projected price at expiry
   * @param {number} monthsToExpiry - Months until expiry
   * @returns {Object} Option valuation including:
   *   - currentValue: Current total option value
   *   - projectedValue: Projected value at expiry
   *   - intrinsicValue: Intrinsic value (max(0, S-K) for calls)
   *   - timeValue: Time value component
   *   - inTheMoney: Whether option is in the money
   *   - profitLoss: Current profit/loss vs cost basis
   */
  const calculateOptionValue = useCallback((option, currentPrice, projectedPrice, monthsToExpiry) => {
    try {
      const { strike, contracts, type } = option;
      
      // Validate inputs
      const validStrike = validateNumber(strike, 0);
      const validContracts = Math.max(1, parseInt(contracts) || 1);
      const validCurrentPrice = validateNumber(currentPrice, 0);
      const validProjectedPrice = validateNumber(projectedPrice, 0);
      const validMonthsToExpiry = validateNumber(monthsToExpiry, 0);
      
      // Intrinsic value
      const intrinsicValue = type === 'call' 
        ? Math.max(0, validCurrentPrice - validStrike)
        : Math.max(0, validStrike - validCurrentPrice);
      
      // Time value (simplified Black-Scholes approximation)
      const annualizedTime = validMonthsToExpiry / 12;
      const volatility = 0.8; // High volatility assumption
      const timeValue = annualizedTime > 0 && validCurrentPrice > 0
        ? validCurrentPrice * volatility * Math.sqrt(annualizedTime) * 0.2
        : 0;
      
      const optionPrice = Math.max(intrinsicValue, intrinsicValue + timeValue);
      const totalValue = optionPrice * validContracts * 100;
      
      // Projected value at expiry
      const projectedIntrinsicValue = type === 'call'
        ? Math.max(0, validProjectedPrice - validStrike)
        : Math.max(0, validStrike - validProjectedPrice);
      const projectedValue = projectedIntrinsicValue * validContracts * 100;
      
      const costBasisTotal = validateNumber(option.costBasis, 0) * validContracts * 100;
      
      return {
        currentValue: totalValue,
        projectedValue,
        intrinsicValue,
        timeValue,
        inTheMoney: intrinsicValue > 0,
        profitLoss: totalValue - costBasisTotal
      };
    } catch (error) {
      logger.error('Option calculation error:', error);
      return {
        currentValue: 0,
        projectedValue: 0,
        intrinsicValue: 0,
        timeValue: 0,
        inTheMoney: false,
        profitLoss: 0
      };
    }
  }, []);

  // Calculate current values including options
  const currentValues = useMemo(() => {
    try {
      const values = {};
      
      // Core assets with validation
      values.btcCold = validateNumber(portfolio.btcCold.quantity, 0) * validateNumber(projections.btc.current, 0);
      values.growthStocks = validateNumber(portfolio.growthStocks.value, 0);
      values.mstrStock = validateNumber(portfolio.mstrStock.shares, 0) * validateNumber(projections.mstr.current, 0);
      values.btcMiners = Math.max(0, miningTotalMetrics.profit * 2); // Simple 2x multiple on annual profit
      
      // Options by category
      const optionsByCategory = {
        ibitShort: [],
        ibitMed: [],
        ibitLong: [],
        mstrShort: [],
        mstrMed: [],
        mstrLong: [],
        nvdaLong: []
      };
      
      // Categorize options safely
      options.forEach(option => {
        try {
          const monthsToExpiry = getMonthsToExpiry(option.expiry);
          
          let category = '';
          if (option.underlying === 'IBIT') {
            if (monthsToExpiry <= 6) category = 'ibitShort';
            else if (monthsToExpiry <= 12) category = 'ibitMed';
            else category = 'ibitLong';
          } else if (option.underlying === 'MSTR') {
            if (monthsToExpiry <= 6) category = 'mstrShort';
            else if (monthsToExpiry <= 12) category = 'mstrMed';
            else category = 'mstrLong';
          } else if (option.underlying === 'NVDA') {
            category = 'nvdaLong';
          }
          
          if (category && optionsByCategory[category]) {
            const underlyingPrice = validateNumber(projections[option.underlying.toLowerCase()]?.current, 0);
            const calc = calculateOptionValue(option, underlyingPrice, underlyingPrice, monthsToExpiry);
            optionsByCategory[category].push(calc.currentValue);
          }
        } catch (error) {
          logger.warn('Option categorization error:', error);
        }
      });
      
      // Sum option values by category
      Object.keys(optionsByCategory).forEach(cat => {
        values[cat] = optionsByCategory[cat].reduce((sum, val) => sum + validateNumber(val, 0), 0);
      });
      
      values.total = Object.values(values).reduce((sum, val) => sum + validateNumber(val, 0), 0);
      
      return values;
    } catch (error) {
      logger.error('Current values calculation error:', error);
      return { total: 0 };
    }
  }, [portfolio, projections, options, calculateOptionValue, miningTotalMetrics.profit]);

  // Calculate allocation percentages
  const allocation = useMemo(() => {
    const total = Math.max(1, currentValues.total); // Prevent division by zero
    const percentages = {};
    
    Object.keys(currentValues).forEach(key => {
      if (key !== 'total') {
        percentages[key] = (validateNumber(currentValues[key], 0) / total) * 100;
      }
    });
    
    return percentages;
  }, [currentValues]);

  // Extended chart categories for display
  const EXTENDED_CATEGORIES = {
    ...ASSET_CATEGORIES,
    ibitShort: { name: 'IBIT Short Options', color: '#EF4444', icon: Zap, type: 'options', volatility: 'extreme' },
    ibitMed: { name: 'IBIT Med Options', color: '#F59E0B', icon: Zap, type: 'options', volatility: 'extreme' },
    ibitLong: { name: 'IBIT Long Options', color: '#3B82F6', icon: Zap, type: 'options', volatility: 'high' },
    mstrShort: { name: 'MSTR Short Options', color: '#DC2626', icon: Zap, type: 'options', volatility: 'extreme' },
    mstrMed: { name: 'MSTR Med Options', color: '#D97706', icon: Zap, type: 'options', volatility: 'extreme' },
    mstrLong: { name: 'MSTR Long Options', color: '#2563EB', icon: Zap, type: 'options', volatility: 'extreme' },
    nvdaLong: { name: 'NVDA Long Options', color: '#76B900', icon: Brain, type: 'options', volatility: 'high' }
  };

  // Risk metrics
  const riskMetrics = useMemo(() => {
    const metrics = {
      concentration: {},
      volatility: 'High',
      optionsExposure: 0,
      cryptoExposure: 0
    };
    
    // Concentration risk
    Object.keys(allocation).forEach(asset => {
      const assetAllocation = validateNumber(allocation[asset], 0);
      if (assetAllocation > 25) {
        metrics.concentration[asset] = 'High';
      } else if (assetAllocation > 15) {
        metrics.concentration[asset] = 'Medium';
      } else if (assetAllocation > 0) {
        metrics.concentration[asset] = 'Low';
      }
    });
    
    // Options exposure
    const optionsAssets = Object.keys(EXTENDED_CATEGORIES).filter(k => 
      EXTENDED_CATEGORIES[k].type === 'options'
    );
    metrics.optionsExposure = optionsAssets.reduce((sum, asset) => 
      sum + validateNumber(allocation[asset], 0), 0
    );
    
    // Crypto exposure
    const cryptoAssets = ['btcCold', 'btcMiners', 'mstrStock', 'ibitShort', 'ibitMed', 'ibitLong', 'mstrShort', 'mstrMed', 'mstrLong'];
    metrics.cryptoExposure = cryptoAssets.reduce((sum, asset) => 
      sum + validateNumber(allocation[asset], 0), 0
    );
    
    return metrics;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allocation]);

  // Chart data
  const allocationChartData = useMemo(() => {
    return Object.keys(EXTENDED_CATEGORIES)
      .map(key => ({
        name: EXTENDED_CATEGORIES[key].name,
        value: Math.max(0, currentValues[key] || 0),
        percentage: Math.max(0, allocation[key] || 0)
      }))
      .filter(item => item.value > 0)
      .sort((a, b) => b.value - a.value);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentValues, allocation]);

  /**
   * Updates a specific field of an asset in the portfolio
   * @param {string} assetKey - Asset identifier (e.g., 'btcCold', 'mstrStock')
   * @param {string} field - Field name to update (e.g., 'quantity', 'shares', 'value')
   * @param {string|number} value - New value (will be validated)
   */
  const handleAssetUpdate = (assetKey, field, value) => {
    const numValue = validateNumber(value, 0);
    setPortfolio(prev => ({
      ...prev,
      [assetKey]: {
        ...prev[assetKey],
        [field]: numValue
      }
    }));
  };

  const handleAddMiningProvider = () => {
    const newProvider = {
      id: Date.now(),
      name: `Provider ${miningProviders.length + 1}`,
      hashrate: 100,
      power: 3000,
      electricityRate: 0.07,
      uptime: 98
    };
    setMiningProviders(prev => [...prev, newProvider]);
  };

  const handleUpdateMiningProvider = (id, field, value) => {
    let validatedValue;
    if (field === 'name') {
      validatedValue = String(value || '');
    } else if (field === 'uptime') {
      validatedValue = validateNumber(value, 0, 100);
    } else {
      validatedValue = validateNumber(value, 0);
    }
    
    setMiningProviders(prev => prev.map(provider => 
      provider.id === id ? { ...provider, [field]: validatedValue } : provider
    ));
  };

  const handleDeleteMiningProvider = (id) => {
    if (miningProviders.length > 1) {
      setMiningProviders(prev => prev.filter(p => p.id !== id));
    }
  };

  const handleAddOption = () => {
    if (!newOption.expiry || !newOption.strike || !newOption.contracts) {
      alert('Please fill all required fields');
      return;
    }
    
    const option = {
      ...newOption,
      id: Date.now(),
      strike: validateNumber(newOption.strike, 0),
      contracts: Math.max(1, parseInt(newOption.contracts) || 1),
      costBasis: validateNumber(newOption.costBasis, 0)
    };
    
    setOptions(prev => [...prev, option]);
    setNewOption({
      underlying: 'IBIT',
      type: 'call',
      strike: 50,
      expiry: '',
      contracts: 1,
      costBasis: 0
    });
    setShowAddOption(false);
  };

  const handleDeleteOption = (id) => {
    setOptions(prev => prev.filter(o => o.id !== id));
  };

  /**
   * Exports all portfolio data to a JSON file
   * Includes portfolio, mining providers, options, projections, debt, and withdrawal strategy
   * @returns {void}
   */
  const exportData = () => {
    try {
      const data = {
        portfolio,
        miningProviders,
        options,
        projections,
        debt,
        withdrawalStrategy,
        exportDate: new Date().toISOString()
      };
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `portfolio-analysis-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      alert('Export failed: ' + error.message);
    }
  };

  /**
   * Imports portfolio data from a JSON file
   * Validates and merges imported data with defaults
   * @param {Event} event - File input change event
   * @returns {void}
   */
  const importData = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        if (data.portfolio) setPortfolio({ ...DEFAULT_PORTFOLIO, ...data.portfolio });
        if (data.miningProviders && Array.isArray(data.miningProviders)) setMiningProviders(data.miningProviders);
        if (data.options && Array.isArray(data.options)) setOptions(data.options);
        if (data.projections) setProjections({ ...DEFAULT_PROJECTIONS, ...data.projections });
        if (data.debt) setDebt({ ...DEFAULT_DEBT, ...data.debt });
        if (data.withdrawalStrategy) setWithdrawalStrategy(data.withdrawalStrategy);
        alert('Data imported successfully!');
      } catch (error) {
        alert('Error importing data: ' + error.message);
      }
    };
    reader.readAsText(file);
    event.target.value = '';
  };

  const COLORS = Object.values(EXTENDED_CATEGORIES).map(cat => cat.color);

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Wallet className="w-8 h-8 text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-900">Portfolio Analyzer & Withdrawal Optimizer</h1>
            </div>
            <div className="flex gap-2">
              <button
                onClick={exportData}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
              <label className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 cursor-pointer">
                <Upload className="w-4 h-4" />
                Import
                <input type="file" accept=".json" onChange={importData} className="hidden" />
              </label>
            </div>
          </div>
          
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-4">
              <div className="text-sm text-blue-600">Total Portfolio Value</div>
              <div className="text-2xl font-bold text-blue-900">${currentValues.total.toLocaleString()}</div>
            </div>
            <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4">
              <div className="text-sm text-green-600">Options Value</div>
              <div className="text-2xl font-bold text-green-900">
                ${Object.keys(currentValues)
                  .filter(k => k.includes('ibit') || k.includes('mstr') || k.includes('nvda'))
                  .reduce((sum, k) => sum + (currentValues[k] || 0), 0)
                  .toLocaleString()}
              </div>
            </div>
            <div className="bg-gradient-to-r from-red-50 to-red-100 rounded-lg p-4">
              <div className="text-sm text-red-600">Total Debt</div>
              <div className="text-2xl font-bold text-red-900">${debt.totalDebt.toLocaleString()}</div>
            </div>
            <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-4">
              <div className="text-sm text-purple-600">Net Worth</div>
              <div className="text-2xl font-bold text-purple-900">${(currentValues.total - debt.totalDebt).toLocaleString()}</div>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white rounded-lg shadow-lg p-2 mb-6 flex gap-2 overflow-x-auto">
          {['overview', 'assets', 'options', 'mining', 'projections', 'withdrawals', 'debt'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg capitalize whitespace-nowrap ${
                activeTab === tab 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Allocation Pie Chart */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold mb-4">Current Allocation</h2>
              {allocationChartData.length > 0 ? (
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsPieChart>
                      <Pie
                        data={allocationChartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({name, percentage}) => percentage > 2 ? `${percentage.toFixed(1)}%` : ''}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {allocationChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-80 flex items-center justify-center text-gray-500">
                  No allocation data available
                </div>
              )}
              <div className="mt-4 grid grid-cols-1 gap-2 text-sm max-h-40 overflow-y-auto">
                {allocationChartData.filter(d => d.percentage > 0).map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded flex-shrink-0" 
                      style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                    />
                    <span className="truncate">{item.name}: {item.percentage.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Risk Metrics */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-500" />
                Risk Analysis
              </h2>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium">Options Exposure</span>
                    <span className={`text-sm font-bold ${
                      riskMetrics.optionsExposure > 50 ? 'text-red-600' : 
                      riskMetrics.optionsExposure > 30 ? 'text-yellow-600' : 'text-green-600'
                    }`}>
                      {riskMetrics.optionsExposure.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        riskMetrics.optionsExposure > 50 ? 'bg-red-600' : 
                        riskMetrics.optionsExposure > 30 ? 'bg-yellow-600' : 'bg-green-600'
                      }`}
                      style={{ width: `${Math.min(100, riskMetrics.optionsExposure)}%` }}
                    />
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium">Crypto/Crypto-Adjacent Exposure</span>
                    <span className={`text-sm font-bold ${
                      riskMetrics.cryptoExposure > 70 ? 'text-red-600' : 
                      riskMetrics.cryptoExposure > 50 ? 'text-yellow-600' : 'text-green-600'
                    }`}>
                      {riskMetrics.cryptoExposure.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        riskMetrics.cryptoExposure > 70 ? 'bg-red-600' : 
                        riskMetrics.cryptoExposure > 50 ? 'bg-yellow-600' : 'bg-green-600'
                      }`}
                      style={{ width: `${Math.min(100, riskMetrics.cryptoExposure)}%` }}
                    />
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <h3 className="font-medium mb-2">Top Concentration Risks</h3>
                  <div className="space-y-1 text-sm">
                    {Object.entries(riskMetrics.concentration)
                      .filter(([_, risk]) => risk === 'High' || risk === 'Medium')
                      .slice(0, 5)
                      .map(([asset, risk]) => (
                        <div key={asset} className="flex items-center justify-between">
                          <span className="text-gray-600">{EXTENDED_CATEGORIES[asset]?.name || asset}:</span>
                          <span className={`font-medium ${
                            risk === 'High' ? 'text-red-600' : 'text-yellow-600'
                          }`}>{risk} ({(allocation[asset] || 0).toFixed(1)}%)</span>
                        </div>
                      ))}
                    {Object.keys(riskMetrics.concentration).length === 0 && (
                      <div className="text-gray-500">No major concentration risks detected</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Assets Tab */}
        {activeTab === 'assets' && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-bold mb-4">Core Asset Details</h2>
            <div className="space-y-4">
              {/* BTC Cold Storage */}
              <div className="border rounded-lg p-4">
                <h3 className="font-medium mb-3 flex items-center gap-2">
                  <Bitcoin className="w-5 h-5 text-orange-500" />
                  BTC Cold Storage
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm text-gray-600">Quantity (BTC)</label>
                    <input
                      type="number"
                      step="0.00001"
                      value={portfolio.btcCold.quantity}
                      onChange={(e) => handleAssetUpdate('btcCold', 'quantity', e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-gray-600">Cost Basis (per BTC)</label>
                    <input
                      type="number"
                      value={portfolio.btcCold.costBasis}
                      onChange={(e) => handleAssetUpdate('btcCold', 'costBasis', e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-gray-600">Current Value</label>
                    <div className="px-3 py-2 bg-gray-100 rounded-lg font-medium">
                      ${currentValues.btcCold.toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>

              {/* Growth Stocks */}
              <div className="border rounded-lg p-4">
                <h3 className="font-medium mb-3 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-green-500" />
                  Growth Stocks Portfolio
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm text-gray-600">Current Value</label>
                    <input
                      type="number"
                      value={portfolio.growthStocks.value}
                      onChange={(e) => handleAssetUpdate('growthStocks', 'value', e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-gray-600">Cost Basis</label>
                    <input
                      type="number"
                      value={portfolio.growthStocks.costBasis}
                      onChange={(e) => handleAssetUpdate('growthStocks', 'costBasis', e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-gray-600">Gain/Loss</label>
                    <div className={`px-3 py-2 bg-gray-100 rounded-lg font-medium ${
                      portfolio.growthStocks.value - portfolio.growthStocks.costBasis >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      ${(portfolio.growthStocks.value - portfolio.growthStocks.costBasis).toLocaleString()}
                      {portfolio.growthStocks.costBasis > 0 && (
                        <span> ({((portfolio.growthStocks.value - portfolio.growthStocks.costBasis) / portfolio.growthStocks.costBasis * 100).toFixed(1)}%)</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* MSTR Stock */}
              <div className="border rounded-lg p-4">
                <h3 className="font-medium mb-3 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-purple-500" />
                  MSTR Stock
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="text-sm text-gray-600">Shares</label>
                    <input
                      type="number"
                      value={portfolio.mstrStock.shares}
                      onChange={(e) => handleAssetUpdate('mstrStock', 'shares', e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-gray-600">Cost Basis (per share)</label>
                    <input
                      type="number"
                      value={portfolio.mstrStock.costBasis}
                      onChange={(e) => handleAssetUpdate('mstrStock', 'costBasis', e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-gray-600">Current Price</label>
                    <div className="px-3 py-2 bg-gray-100 rounded-lg font-medium">
                      ${projections.mstr.current}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm text-gray-600">Current Value</label>
                    <div className="px-3 py-2 bg-gray-100 rounded-lg font-medium">
                      ${currentValues.mstrStock.toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Options Tab */}
        {activeTab === 'options' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold">Options Portfolio</h2>
                <button
                  onClick={() => setShowAddOption(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add Option
                </button>
              </div>

              {/* Add Option Modal */}
              {showAddOption && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                  <div className="bg-white rounded-lg p-6 w-full max-w-md">
                    <h3 className="text-lg font-bold mb-4">Add New Option</h3>
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium">Underlying</label>
                        <select
                          value={newOption.underlying}
                          onChange={(e) => setNewOption({...newOption, underlying: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg"
                        >
                          <option value="IBIT">IBIT</option>
                          <option value="MSTR">MSTR</option>
                          <option value="NVDA">NVDA</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-sm font-medium">Type</label>
                        <select
                          value={newOption.type}
                          onChange={(e) => setNewOption({...newOption, type: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg"
                        >
                          <option value="call">Call</option>
                          <option value="put">Put</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-sm font-medium">Strike Price</label>
                        <input
                          type="number"
                          value={newOption.strike}
                          onChange={(e) => setNewOption({...newOption, strike: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Expiration Date</label>
                        <input
                          type="date"
                          value={newOption.expiry}
                          onChange={(e) => setNewOption({...newOption, expiry: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Number of Contracts</label>
                        <input
                          type="number"
                          value={newOption.contracts}
                          onChange={(e) => setNewOption({...newOption, contracts: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Cost Basis (per contract)</label>
                        <input
                          type="number"
                          step="0.01"
                          value={newOption.costBasis}
                          onChange={(e) => setNewOption({...newOption, costBasis: e.target.value})}
                          className="w-full px-3 py-2 border rounded-lg"
                        />
                      </div>
                    </div>
                    <div className="flex gap-2 mt-6">
                      <button
                        onClick={handleAddOption}
                        className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                      >
                        Add Option
                      </button>
                      <button
                        onClick={() => setShowAddOption(false)}
                        className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Options List */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left">Underlying</th>
                      <th className="px-4 py-2 text-left">Type</th>
                      <th className="px-4 py-2 text-right">Strike</th>
                      <th className="px-4 py-2 text-right">Expiry</th>
                      <th className="px-4 py-2 text-right">Contracts</th>
                      <th className="px-4 py-2 text-right">Cost Basis</th>
                      <th className="px-4 py-2 text-right">Current Value</th>
                      <th className="px-4 py-2 text-right">P/L</th>
                      <th className="px-4 py-2 text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {options.map(option => {
                      const monthsToExpiry = getMonthsToExpiry(option.expiry);
                      const underlyingPrice = validateNumber(projections[option.underlying.toLowerCase()]?.current, 0);
                      const calc = calculateOptionValue(option, underlyingPrice, underlyingPrice, monthsToExpiry);
                      
                      return (
                        <tr key={option.id} className="border-t">
                          <td className="px-4 py-3 font-medium">{option.underlying}</td>
                          <td className="px-4 py-3 capitalize">{option.type}</td>
                          <td className="px-4 py-3 text-right">${option.strike}</td>
                          <td className="px-4 py-3 text-right">{option.expiry}</td>
                          <td className="px-4 py-3 text-right">{option.contracts}</td>
                          <td className="px-4 py-3 text-right">${option.costBasis}</td>
                          <td className="px-4 py-3 text-right font-medium">${calc.currentValue.toLocaleString()}</td>
                          <td className={`px-4 py-3 text-right font-medium ${calc.profitLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            ${calc.profitLoss.toLocaleString()}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <button
                              onClick={() => handleDeleteOption(option.id)}
                              className="text-red-500 hover:text-red-700"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Mining Tab */}
        {activeTab === 'mining' && (
          <div className="space-y-6">
            {/* Mining Summary */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold mb-4">Mining Operations Summary</h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-orange-50 rounded-lg p-4">
                  <div className="text-sm text-orange-600">Total Hashrate</div>
                  <div className="text-2xl font-bold text-orange-900">
                    {miningProviders.reduce((sum, p) => sum + validateNumber(p.hashrate, 0), 0)} TH/s
                  </div>
                </div>
                <div className="bg-red-50 rounded-lg p-4">
                  <div className="text-sm text-red-600">Total Power</div>
                  <div className="text-2xl font-bold text-red-900">
                    {(miningProviders.reduce((sum, p) => sum + validateNumber(p.power, 0), 0) / 1000).toFixed(1)} kW
                  </div>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="text-sm text-green-600">Monthly Profit</div>
                  <div className="text-2xl font-bold text-green-900">
                    ${miningTotalMetrics.monthlyAvgProfit.toLocaleString()}
                  </div>
                </div>
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="text-sm text-blue-600">Annual BTC</div>
                  <div className="text-2xl font-bold text-blue-900">
                    {miningTotalMetrics.totalBtcMined.toFixed(4)} BTC
                  </div>
                </div>
              </div>
            </div>

            {/* Mining Providers */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold">Mining Providers</h2>
                <button
                  onClick={handleAddMiningProvider}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add Provider
                </button>
              </div>

              <div className="space-y-4">
                {miningProviders.map(provider => {
                  const metrics = calculateMiningMetrics(provider, validateNumber(projections.btc.current, 0), 12);
                  
                  return (
                    <div key={provider.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <input
                          type="text"
                          value={provider.name}
                          onChange={(e) => handleUpdateMiningProvider(provider.id, 'name', e.target.value)}
                          className="font-medium text-lg bg-transparent border-b border-transparent hover:border-gray-300 focus:border-blue-500 outline-none"
                        />
                        {miningProviders.length > 1 && (
                          <button
                            onClick={() => handleDeleteMiningProvider(provider.id)}
                            className="text-red-500 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-3">
                        <div>
                          <label className="text-xs text-gray-600">Hashrate (TH/s)</label>
                          <input
                            type="number"
                            value={provider.hashrate}
                            onChange={(e) => handleUpdateMiningProvider(provider.id, 'hashrate', e.target.value)}
                            className="w-full px-2 py-1 border rounded text-sm"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-gray-600">Power (W)</label>
                          <input
                            type="number"
                            value={provider.power}
                            onChange={(e) => handleUpdateMiningProvider(provider.id, 'power', e.target.value)}
                            className="w-full px-2 py-1 border rounded text-sm"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-gray-600">$/kWh</label>
                          <input
                            type="number"
                            step="0.001"
                            value={provider.electricityRate}
                            onChange={(e) => handleUpdateMiningProvider(provider.id, 'electricityRate', e.target.value)}
                            className="w-full px-2 py-1 border rounded text-sm"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-gray-600">Uptime %</label>
                          <input
                            type="number"
                            value={provider.uptime}
                            onChange={(e) => handleUpdateMiningProvider(provider.id, 'uptime', e.target.value)}
                            className="w-full px-2 py-1 border rounded text-sm"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-gray-600">Efficiency</label>
                          <div className="px-2 py-1 bg-gray-100 rounded text-sm font-medium">
                            {metrics.efficiency.toFixed(1)} J/TH
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                        <div>
                          <span className="text-gray-600">Annual BTC:</span>
                          <span className="font-medium ml-1">{metrics.totalBtcMined.toFixed(4)}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Revenue:</span>
                          <span className="font-medium ml-1">${metrics.totalRevenue.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Profit:</span>
                          <span className={`font-medium ml-1 ${metrics.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            ${metrics.profit.toLocaleString()}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">Breakeven:</span>
                          <span className="font-medium ml-1">${metrics.breakevenPrice.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Mining Parameters */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold mb-4">Mining Network Parameters</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium">Current Network Hashrate (EH/s)</label>
                  <input
                    type="number"
                    value={projections.miningParams.networkHashrate}
                    onChange={(e) => setProjections({
                      ...projections,
                      miningParams: {
                        ...projections.miningParams,
                        networkHashrate: validateNumber(e.target.value, 1)
                      }
                    })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Monthly Difficulty Growth (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={projections.miningParams.monthlyDifficultyGrowth}
                    onChange={(e) => setProjections({
                      ...projections,
                      miningParams: {
                        ...projections.miningParams,
                        monthlyDifficultyGrowth: validateNumber(e.target.value, 0, 50)
                      }
                    })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Block Reward</label>
                  <div className="px-3 py-2 bg-gray-100 rounded-lg">
                    {projections.miningParams.blockReward} BTC
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Projections Tab */}
        {activeTab === 'projections' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold mb-4">Price Projections</h2>
              <div className="space-y-6">
                {['btc', 'mstr', 'nvda', 'ibit'].map(asset => (
                  <div key={asset} className="border rounded-lg p-4">
                    <h3 className="font-medium mb-3 capitalize">
                      {asset === 'ibit' ? 'IBIT ETF' : asset.toUpperCase()} Price Projections
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                      <div>
                        <label className="text-xs text-gray-600">Current</label>
                        <input
                          type="number"
                          value={projections[asset].current}
                          onChange={(e) => setProjections({
                            ...projections,
                            [asset]: { ...projections[asset], current: validateNumber(e.target.value, 0) }
                          })}
                          className="w-full px-2 py-1 border rounded text-sm"
                        />
                      </div>
                      {PROJECTION_TIMEFRAMES.map(tf => (
                        <div key={tf.key}>
                          <label className="text-xs text-gray-600">{tf.label}</label>
                          <input
                            type="number"
                            value={projections[asset][tf.key]}
                            onChange={(e) => setProjections({
                              ...projections,
                              [asset]: { ...projections[asset], [tf.key]: validateNumber(e.target.value, 0) }
                            })}
                            className="w-full px-2 py-1 border rounded text-sm"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Options Projection Matrix */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold mb-4">Options Value Projections</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left">Option</th>
                      <th className="px-4 py-2 text-right">Current</th>
                      {PROJECTION_TIMEFRAMES.map(tf => (
                        <th key={tf.key} className="px-4 py-2 text-right">{tf.label}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {options.map(option => {
                      const expiryDate = new Date(option.expiry);
                      const currentUnderlyingPrice = validateNumber(projections[option.underlying.toLowerCase()]?.current, 0);
                      
                      return (
                        <tr key={option.id} className="border-t">
                          <td className="px-4 py-3">
                            <div className="font-medium">{option.underlying} ${option.strike} {option.type}</div>
                            <div className="text-xs text-gray-500">Exp: {option.expiry}</div>
                          </td>
                          <td className="px-4 py-3 text-right">
                            ${calculateOptionValue(
                              option, 
                              currentUnderlyingPrice, 
                              currentUnderlyingPrice, 
                              getMonthsToExpiry(option.expiry)
                            ).currentValue.toLocaleString()}
                          </td>
                          {PROJECTION_TIMEFRAMES.map(tf => {
                            const projectionDate = new Date();
                            projectionDate.setMonth(projectionDate.getMonth() + tf.months);
                            const monthsToExpiry = (expiryDate - projectionDate) / (1000 * 60 * 60 * 24 * 30.42);
                            
                            if (monthsToExpiry < 0) {
                              // Option expired
                              const finalPrice = validateNumber(projections[option.underlying.toLowerCase()]?.[tf.key], 0);
                              const finalValue = option.type === 'call'
                                ? Math.max(0, finalPrice - option.strike) * option.contracts * 100
                                : Math.max(0, option.strike - finalPrice) * option.contracts * 100;
                              
                              return (
                                <td key={tf.key} className="px-4 py-3 text-right">
                                  <div className={finalValue > 0 ? 'text-green-600' : 'text-gray-400'}>
                                    ${finalValue.toLocaleString()}
                                  </div>
                                  <div className="text-xs text-gray-500">Expired</div>
                                </td>
                              );
                            } else {
                              const projectedPrice = validateNumber(projections[option.underlying.toLowerCase()]?.[tf.key], 0);
                              const calc = calculateOptionValue(option, projectedPrice, projectedPrice, Math.max(0, monthsToExpiry));
                              
                              return (
                                <td key={tf.key} className="px-4 py-3 text-right">
                                  ${calc.currentValue.toLocaleString()}
                                </td>
                              );
                            }
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Withdrawals Tab */}
        {activeTab === 'withdrawals' && (
          <div className="space-y-6">
            {/* Withdrawal Settings */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold mb-4">Withdrawal Strategy Settings</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Monthly Withdrawal Target</label>
                  <input
                    type="number"
                    value={withdrawalStrategy.monthlyTarget}
                    onChange={(e) => setWithdrawalStrategy({
                      ...withdrawalStrategy,
                      monthlyTarget: validateNumber(e.target.value, 0)
                    })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Risk Tolerance</label>
                  <select
                    value={withdrawalStrategy.riskTolerance}
                    onChange={(e) => setWithdrawalStrategy({
                      ...withdrawalStrategy,
                      riskTolerance: e.target.value
                    })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="conservative">Conservative</option>
                    <option value="moderate">Moderate</option>
                    <option value="aggressive">Aggressive</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">
                    <input
                      type="checkbox"
                      checked={withdrawalStrategy.preserveCore}
                      onChange={(e) => setWithdrawalStrategy({
                        ...withdrawalStrategy,
                        preserveCore: e.target.checked
                      })}
                      className="mr-2"
                    />
                    Preserve Core Assets
                  </label>
                  <p className="text-sm text-gray-600">Keep at least {(withdrawalStrategy.minCoreRetention * 100).toFixed(0)}% of BTC and miners</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">
                    <input
                      type="checkbox"
                      checked={withdrawalStrategy.taxConsideration}
                      onChange={(e) => setWithdrawalStrategy({
                        ...withdrawalStrategy,
                        taxConsideration: e.target.checked
                      })}
                      className="mr-2"
                    />
                    Consider Tax Implications
                  </label>
                  <p className="text-sm text-gray-600">Prioritize long-term holdings for lower tax rates</p>
                </div>
              </div>
            </div>

            {/* Withdrawal Recommendations */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold mb-4">Smart Withdrawal Recommendations</h2>
              
              {/* Priority Order */}
              <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                <h3 className="font-medium mb-2">Withdrawal Priority Order</h3>
                <ol className="text-sm space-y-1 list-decimal list-inside">
                  <li>Short-term options near expiry (&lt; 6 months)</li>
                  <li>Medium-term options (6-12 months)</li>
                  <li>Options with significant gains</li>
                  <li>MSTR stock (partial positions)</li>
                  <li>Growth stocks</li>
                  <li>Long-term options (if needed)</li>
                  <li>BTC/Miners (only if absolutely necessary)</li>
                </ol>
              </div>

              {/* Monthly Plan */}
              <div className="space-y-4">
                <h3 className="font-medium">12-Month Withdrawal Plan</h3>
                {(() => {
                  const monthlyTarget = withdrawalStrategy.monthlyTarget;
                  const recommendations = [];
                  
                  // Get options sorted by expiry
                  const sortedOptions = [...options].sort((a, b) => 
                    new Date(a.expiry) - new Date(b.expiry)
                  );
                  
                  for (let month = 1; month <= 12; month++) {
                    const monthDate = new Date();
                    monthDate.setMonth(monthDate.getMonth() + month - 1);
                    
                    const monthPlan = {
                      month,
                      withdrawals: [],
                      total: 0
                    };
                    
                    // Check expiring options
                    sortedOptions.forEach(option => {
                      const expiryDate = new Date(option.expiry);
                      const monthsToExpiry = (expiryDate - monthDate) / (1000 * 60 * 60 * 24 * 30.42);
                      
                      if (monthsToExpiry <= 1 && monthsToExpiry > 0 && monthPlan.total < monthlyTarget) {
                        const underlyingPrice = validateNumber(projections[option.underlying.toLowerCase()]?.current, 0);
                        const calc = calculateOptionValue(option, underlyingPrice, underlyingPrice, monthsToExpiry);
                        
                        if (calc.currentValue > 100) {
                          monthPlan.withdrawals.push({
                            asset: `${option.underlying} ${option.strike} ${option.type} (Exp: ${option.expiry})`,
                            amount: Math.min(calc.currentValue, monthlyTarget - monthPlan.total),
                            type: 'option'
                          });
                          monthPlan.total += Math.min(calc.currentValue, monthlyTarget - monthPlan.total);
                        }
                      }
                    });
                    
                    // Fill remaining with other assets if needed
                    if (monthPlan.total < monthlyTarget) {
                      const remaining = monthlyTarget - monthPlan.total;
                      
                      // Priority: MSTR stock partial
                      if (currentValues.mstrStock > remaining * 2) {
                        monthPlan.withdrawals.push({
                          asset: 'MSTR Stock (Partial)',
                          amount: remaining,
                          type: 'stock'
                        });
                        monthPlan.total += remaining;
                      }
                    }
                    
                    recommendations.push(monthPlan);
                  }
                  
                  return recommendations.map((month, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex justify-between items-center mb-2">
                        <h3 className="font-medium">Month {month.month}</h3>
                        <span className="font-bold text-lg">${month.total.toLocaleString()}</span>
                      </div>
                      {month.withdrawals.length > 0 ? (
                        <div className="space-y-2">
                          {month.withdrawals.map((withdrawal, idx) => (
                            <div key={idx} className="flex justify-between text-sm">
                              <span className="text-gray-600">{withdrawal.asset}</span>
                              <span className="font-medium">${withdrawal.amount.toLocaleString()}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">Consider selling partial stock positions or longer-term options</p>
                      )}
                    </div>
                  ));
                })()}
              </div>
            </div>

            {/* Withdrawal Impact Analysis */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold mb-4">Withdrawal Impact Analysis</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium mb-3">Portfolio After 12 Months of Withdrawals</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Current Portfolio Value:</span>
                      <span className="font-medium">${currentValues.total.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Withdrawals (12mo):</span>
                      <span className="font-medium text-red-600">-${(withdrawalStrategy.monthlyTarget * 12).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Projected Growth:</span>
                      <span className="font-medium text-green-600">+${Math.max(0, (currentValues.total * 0.3) - (withdrawalStrategy.monthlyTarget * 12)).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between pt-2 border-t font-bold">
                      <span>Projected Portfolio Value:</span>
                      <span>${Math.max(0, currentValues.total * 1.3 - withdrawalStrategy.monthlyTarget * 12).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium mb-3">Core Assets Protection</h3>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm">BTC Cold Storage</span>
                        <span className="text-sm font-medium text-green-600">Protected</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-green-600 h-2 rounded-full" style={{ width: '100%' }} />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm">Mining Operations</span>
                        <span className="text-sm font-medium text-green-600">Protected</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-green-600 h-2 rounded-full" style={{ width: '100%' }} />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Debt Tab */}
        {activeTab === 'debt' && (
          <div className="space-y-6">
            {/* Debt Overview */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold mb-4">Debt Overview</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-red-50 rounded-lg p-4">
                  <div className="text-sm text-red-600">Total Debt</div>
                  <div className="text-2xl font-bold text-red-900">${debt.totalDebt.toLocaleString()}</div>
                </div>
                <div className="bg-orange-50 rounded-lg p-4">
                  <div className="text-sm text-orange-600">Monthly Minimum</div>
                  <div className="text-2xl font-bold text-orange-900">${debt.monthlyMinPayment}</div>
                </div>
                <div className="bg-yellow-50 rounded-lg p-4">
                  <div className="text-sm text-yellow-600">Target Payoff</div>
                  <div className="text-2xl font-bold text-yellow-900">{debt.targetPayoffMonths} months</div>
                </div>
              </div>
              
              <h3 className="font-medium mb-3">Credit Card Details</h3>
              <div className="space-y-3">
                {debt.creditCards.map((card, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="font-medium">{card.name}</h4>
                        <p className="text-sm text-gray-600">APR: {card.apr}%</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-lg">${card.balance.toLocaleString()}</p>
                        <p className="text-sm text-gray-600">Min: ${card.minPayment}/mo</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Payoff Strategy */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold mb-4">Debt Payoff Strategy</h2>
              <div className="space-y-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <h3 className="font-medium mb-2">Recommended Monthly Payment</h3>
                  <p className="text-2xl font-bold text-blue-900">
                    ${Math.ceil(debt.totalDebt / Math.max(1, debt.targetPayoffMonths)).toLocaleString()}
                  </p>
                  <p className="text-sm text-blue-600 mt-1">
                    To pay off in {debt.targetPayoffMonths} months (vs ${debt.monthlyMinPayment} minimum)
                  </p>
                </div>
                
                <div className="bg-green-50 rounded-lg p-4">
                  <h3 className="font-medium mb-2">Interest Savings</h3>
                  <p className="text-lg font-bold text-green-900">
                    ${Math.max(0, (debt.totalDebt * 0.25 * 3) - (debt.totalDebt * 0.25 * (debt.targetPayoffMonths / 12))).toLocaleString()}
                  </p>
                  <p className="text-sm text-green-600">By paying off in {debt.targetPayoffMonths} months vs 36 months</p>
                </div>

                {/* Avalanche vs Snowball */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="border rounded-lg p-4">
                    <h3 className="font-medium mb-2">Avalanche Method</h3>
                    <p className="text-sm text-gray-600 mb-2">Pay highest APR first</p>
                    <ol className="text-sm space-y-1 list-decimal list-inside">
                      {[...debt.creditCards].sort((a, b) => b.apr - a.apr).map((card, idx) => (
                        <li key={idx}>{card.name} ({card.apr}%)</li>
                      ))}
                    </ol>
                    <p className="text-xs text-green-600 mt-2">Saves the most on interest</p>
                  </div>
                  
                  <div className="border rounded-lg p-4">
                    <h3 className="font-medium mb-2">Snowball Method</h3>
                    <p className="text-sm text-gray-600 mb-2">Pay smallest balance first</p>
                    <ol className="text-sm space-y-1 list-decimal list-inside">
                      {[...debt.creditCards].sort((a, b) => a.balance - b.balance).map((card, idx) => (
                        <li key={idx}>{card.name} (${card.balance.toLocaleString()})</li>
                      ))}
                    </ol>
                    <p className="text-xs text-blue-600 mt-2">Psychological wins</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Debt vs Investment Analysis */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold mb-4">Debt Payoff vs Investment Growth</h2>
              <div className="bg-yellow-50 rounded-lg p-4 mb-4">
                <p className="text-sm">
                  <strong>Key Insight:</strong> Your highest APR is {debt.creditCards.length > 0 ? Math.max(...debt.creditCards.map(c => c.apr)) : 0}%. 
                  Compare this to expected portfolio returns when deciding between aggressive debt payoff vs investing.
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border rounded-lg p-4">
                  <h3 className="font-medium mb-2">If You Pay Off Debt in 12 Months</h3>
                  <ul className="text-sm space-y-1">
                    <li>• Monthly payment: ${Math.ceil(debt.totalDebt / 12).toLocaleString()}</li>
                    <li>• Total interest paid: ~${(debt.totalDebt * 0.25 * 1).toLocaleString()}</li>
                    <li>• Free cash flow after: ${Math.ceil(debt.totalDebt / 12).toLocaleString()}/mo</li>
                    <li className="text-green-600 font-medium">• Guaranteed {debt.creditCards.length > 0 ? Math.max(...debt.creditCards.map(c => c.apr)) : 0}% return</li>
                  </ul>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h3 className="font-medium mb-2">If You Invest Instead</h3>
                  <ul className="text-sm space-y-1">
                    <li>• Keep paying minimums: ${debt.monthlyMinPayment}/mo</li>
                    <li>• Invest difference: ${Math.max(0, Math.ceil(debt.totalDebt / 12) - debt.monthlyMinPayment).toLocaleString()}/mo</li>
                    <li>• Need >{debt.creditCards.length > 0 ? Math.max(...debt.creditCards.map(c => c.apr)) : 0}% returns to break even</li>
                    <li className="text-yellow-600 font-medium">• Higher risk, potentially higher reward</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PortfolioAnalyzer;