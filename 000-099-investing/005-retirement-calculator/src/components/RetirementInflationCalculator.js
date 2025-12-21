/**
 * Retirement Inflation Calculator Component
 * 
 * A comprehensive retirement planning tool that models the impact of inflation
 * on retirement savings, calculates required investment returns, and helps
 * plan contribution strategies.
 * 
 * @module components/RetirementInflationCalculator
 */

import React, { useState, useMemo, useCallback } from 'react';
import PropTypes from 'prop-types';
import { Calculator, TrendingUp, DollarSign, Calendar, AlertCircle, Info } from 'lucide-react';

import {
  calculateTotalFunding,
  calculateFutureValueWithReturn,
  calculateFutureValuesByAge,
  calculateRequiredReturnsTable,
  calculateProjectedOutcomes,
} from '../utils/calculations';
import { formatCurrency, formatPercent } from '../utils/formatters';
import {
  INFLATION_RATES,
  DEFAULT_VALUES,
  INPUT_CONSTRAINTS,
  DISPLAY_CONFIG,
  RETURN_THRESHOLDS,
} from '../config/constants';

/**
 * Main retirement calculator component
 * 
 * @returns {JSX.Element} The rendered calculator
 */
const RetirementInflationCalculator = () => {
  // ============================================
  // State Management
  // ============================================
  
  const [currentAge, setCurrentAge] = useState(DEFAULT_VALUES.currentAge);
  const [retirementAge, setRetirementAge] = useState(DEFAULT_VALUES.retirementAge);
  const [endAge, setEndAge] = useState(DEFAULT_VALUES.endAge);
  const [desiredIncome, setDesiredIncome] = useState(DEFAULT_VALUES.desiredIncome);
  const [inflationScenario, setInflationScenario] = useState(DEFAULT_VALUES.inflationScenario);
  const [customInflation, setCustomInflation] = useState(DEFAULT_VALUES.customInflation);
  const [initialInvestment, setInitialInvestment] = useState(DEFAULT_VALUES.initialInvestment);
  const [annualContribution, setAnnualContribution] = useState(DEFAULT_VALUES.annualContribution);
  const [expectedReturn, setExpectedReturn] = useState(DEFAULT_VALUES.expectedReturn);

  // ============================================
  // Derived Values (Memoized)
  // ============================================

  /**
   * Current inflation rates including custom rate
   */
  const inflationRates = useMemo(() => ({
    ...INFLATION_RATES,
    custom: customInflation,
  }), [customInflation]);

  /**
   * Years until retirement
   */
  const yearsToRetirement = useMemo(
    () => retirementAge - currentAge,
    [retirementAge, currentAge]
  );

  /**
   * Total funding needed under each inflation scenario
   */
  const totalFunding = useMemo(() => ({
    best: calculateTotalFunding(desiredIncome, currentAge, retirementAge, endAge, inflationRates.best),
    base: calculateTotalFunding(desiredIncome, currentAge, retirementAge, endAge, inflationRates.base),
    worst: calculateTotalFunding(desiredIncome, currentAge, retirementAge, endAge, inflationRates.worst),
    custom: calculateTotalFunding(desiredIncome, currentAge, retirementAge, endAge, inflationRates.custom),
  }), [desiredIncome, currentAge, retirementAge, endAge, inflationRates]);

  /**
   * Future income requirements at various ages
   */
  const futureValues = useMemo(
    () => calculateFutureValuesByAge(currentAge, retirementAge, endAge, desiredIncome, inflationRates),
    [currentAge, retirementAge, endAge, desiredIncome, inflationRates]
  );

  /**
   * Required returns for various investment amounts
   */
  const requiredReturns = useMemo(
    () => calculateRequiredReturnsTable(
      DISPLAY_CONFIG.requiredReturnsAmounts,
      annualContribution,
      totalFunding,
      yearsToRetirement
    ),
    [annualContribution, totalFunding, yearsToRetirement]
  );

  /**
   * Investment amounts for projected outcomes table
   * Includes user's specific amount if not already in the default list
   */
  const projectedOutcomesAmounts = useMemo(() => {
    let amounts = [...DISPLAY_CONFIG.projectedOutcomesAmounts];
    
    if (initialInvestment > 0 && !amounts.includes(initialInvestment)) {
      amounts.push(initialInvestment);
      amounts.sort((a, b) => a - b);
    }
    
    // Keep only max configured amounts
    if (amounts.length > DISPLAY_CONFIG.maxProjectedOutcomes) {
      const step = Math.floor(amounts.length / 5);
      const newAmounts = [];
      for (let i = 0; i < amounts.length; i += step) {
        newAmounts.push(amounts[i]);
      }
      // Always include the user's amount
      if (initialInvestment > 0 && !newAmounts.includes(initialInvestment)) {
        newAmounts.push(initialInvestment);
        newAmounts.sort((a, b) => a - b);
      }
      amounts = newAmounts.slice(0, DISPLAY_CONFIG.maxProjectedOutcomes);
    }
    
    return amounts;
  }, [initialInvestment]);

  /**
   * Projected outcomes for various investment amounts
   */
  const projectedOutcomes = useMemo(
    () => calculateProjectedOutcomes(
      projectedOutcomesAmounts,
      annualContribution,
      expectedReturn,
      yearsToRetirement,
      totalFunding
    ),
    [projectedOutcomesAmounts, annualContribution, expectedReturn, yearsToRetirement, totalFunding]
  );

  /**
   * User's specific projected outcome based on their inputs
   */
  const userSpecificOutcome = useMemo(() => {
    const projectedValue = calculateFutureValueWithReturn(
      initialInvestment,
      annualContribution,
      expectedReturn,
      yearsToRetirement
    );

    return {
      projectedValue,
      baseCaseMet: projectedValue >= totalFunding.base,
      worstCaseMet: projectedValue >= totalFunding.worst,
      customMet: projectedValue >= totalFunding.custom,
      baseCaseGap: totalFunding.base - projectedValue,
      worstCaseGap: totalFunding.worst - projectedValue,
      customGap: totalFunding.custom - projectedValue,
    };
  }, [initialInvestment, annualContribution, expectedReturn, yearsToRetirement, totalFunding]);

  // ============================================
  // Event Handlers
  // ============================================

  const handleIntegerInput = useCallback((setter) => (e) => {
    setter(parseInt(e.target.value) || 0);
  }, []);

  const handleFloatInput = useCallback((setter) => (e) => {
    setter(parseFloat(e.target.value) || 0);
  }, []);

  // ============================================
  // Render
  // ============================================

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* Header */}
      <header className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center justify-center gap-2">
          <Calculator className="w-8 h-8 text-blue-600" aria-hidden="true" />
          Retirement Inflation Calculator
        </h1>
        <p className="text-gray-600">Plan for inflation's impact on your retirement purchasing power</p>
      </header>

      {/* Input Section */}
      <section className="bg-white rounded-lg shadow-lg p-6 space-y-6" aria-labelledby="input-section-title">
        <h2 id="input-section-title" className="text-xl font-semibold text-gray-800 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-blue-600" aria-hidden="true" />
          Your Information
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <InputField
            label="Current Age"
            value={currentAge}
            onChange={handleIntegerInput(setCurrentAge)}
            min={INPUT_CONSTRAINTS.minAge}
            max={INPUT_CONSTRAINTS.maxAge}
          />

          <InputField
            label="Retirement Age"
            value={retirementAge}
            onChange={handleIntegerInput(setRetirementAge)}
            min={currentAge + 1}
            max={INPUT_CONSTRAINTS.maxAge}
          />

          <InputField
            label="Life Expectancy"
            value={endAge}
            onChange={handleIntegerInput(setEndAge)}
            min={retirementAge + 1}
            max={INPUT_CONSTRAINTS.maxLifeExpectancy}
          />

          <InputField
            label="Desired Annual Income (Today's $)"
            value={desiredIncome}
            onChange={handleIntegerInput(setDesiredIncome)}
            min={0}
            step={INPUT_CONSTRAINTS.investmentStep}
          />

          <InputField
            label="Initial Investment Amount"
            value={initialInvestment}
            onChange={handleIntegerInput(setInitialInvestment)}
            min={0}
            step={INPUT_CONSTRAINTS.investmentStep}
            hint="Lump sum available to invest now"
          />

          <InputField
            label="Annual Contribution Until Retirement"
            value={annualContribution}
            onChange={handleIntegerInput(setAnnualContribution)}
            min={0}
            step={INPUT_CONSTRAINTS.contributionStep}
            placeholder="0"
            hint="Annual savings in addition to initial investment"
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Inflation Scenario
            </label>
            <select
              value={inflationScenario}
              onChange={(e) => setInflationScenario(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              aria-label="Select inflation scenario"
            >
              <option value="best">Best Case ({formatPercent(INFLATION_RATES.best)})</option>
              <option value="base">Base Case ({formatPercent(INFLATION_RATES.base)})</option>
              <option value="worst">Worst Case ({formatPercent(INFLATION_RATES.worst)})</option>
              <option value="custom">Custom</option>
            </select>
          </div>

          {inflationScenario === 'custom' && (
            <InputField
              label="Custom Inflation Rate (%)"
              value={customInflation}
              onChange={handleFloatInput(setCustomInflation)}
              min={INPUT_CONSTRAINTS.minInflation}
              max={INPUT_CONSTRAINTS.maxInflation}
              step={0.1}
              type="number"
            />
          )}
        </div>
      </section>

      {/* Projected Outcomes Section */}
      <section className="bg-white rounded-lg shadow-lg p-6" aria-labelledby="projected-outcomes-title">
        <h2 id="projected-outcomes-title" className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-600" aria-hidden="true" />
          Projected Outcomes Analysis
        </h2>
        
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Expected Annual Return (%)
          </label>
          <div className="flex items-center gap-4">
            <input
              type="number"
              value={expectedReturn}
              onChange={handleFloatInput(setExpectedReturn)}
              className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              min={INPUT_CONSTRAINTS.minReturn}
              max={INPUT_CONSTRAINTS.maxReturn}
              step={0.5}
              aria-label="Expected annual return percentage"
            />
            <span className="text-sm text-gray-600">
              (S&P 500 historical average: ~{formatPercent(DEFAULT_VALUES.expectedReturn)})
            </span>
          </div>
        </div>

        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            This section shows what portfolio value you'll achieve with your expected return rate, 
            and whether it meets your retirement funding goals under different inflation scenarios.
          </p>
        </div>

        {/* User's Specific Outcome */}
        <UserOutcomeCard
          outcome={userSpecificOutcome}
          initialInvestment={initialInvestment}
          annualContribution={annualContribution}
          expectedReturn={expectedReturn}
          showCustom={inflationScenario === 'custom'}
        />
        
        {/* Projected Outcomes Table */}
        <ProjectedOutcomesTable
          outcomes={projectedOutcomes}
          initialInvestment={initialInvestment}
          showCustom={inflationScenario === 'custom'}
        />
        
        {annualContribution > 0 && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-600">
              * Additional contributions shown are on top of your current {formatCurrency(annualContribution)} annual contribution
            </p>
          </div>
        )}
      </section>

      {/* Key Findings */}
      <KeyFindings
        futureValues={futureValues}
        totalFunding={totalFunding}
        inflationScenario={inflationScenario}
        retirementAge={retirementAge}
        endAge={endAge}
        currentAge={currentAge}
        annualContribution={annualContribution}
      />

      {/* Future Value Table */}
      <FutureIncomeTable
        futureValues={futureValues}
        inflationScenario={inflationScenario}
        customInflation={customInflation}
      />

      {/* Required Returns Table */}
      <RequiredReturnsTable
        requiredReturns={requiredReturns}
        inflationRates={inflationRates}
        inflationScenario={inflationScenario}
        customInflation={customInflation}
        annualContribution={annualContribution}
      />

      {/* Planning Recommendations */}
      <PlanningRecommendations />
    </div>
  );
};

// ============================================
// Sub-Components
// ============================================

/**
 * Reusable input field component
 */
const InputField = ({ label, value, onChange, min, max, step, hint, placeholder, type = 'number' }) => (
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-2">
      {label}
    </label>
    <input
      type={type}
      value={value}
      onChange={onChange}
      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      min={min}
      max={max}
      step={step}
      placeholder={placeholder}
      aria-label={label}
    />
    {hint && <p className="text-xs text-gray-500 mt-1">{hint}</p>}
  </div>
);

InputField.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  onChange: PropTypes.func.isRequired,
  min: PropTypes.number,
  max: PropTypes.number,
  step: PropTypes.number,
  hint: PropTypes.string,
  placeholder: PropTypes.string,
  type: PropTypes.string,
};

InputField.defaultProps = {
  min: 0,
  max: Infinity,
  step: 1,
  hint: null,
  placeholder: '',
  type: 'number',
};

/**
 * User's specific outcome card
 */
const UserOutcomeCard = ({ outcome, initialInvestment, annualContribution, expectedReturn, showCustom }) => {
  if (!outcome) return null;

  return (
    <div className="mb-6 p-4 bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 rounded-lg">
      <h3 className="font-semibold text-gray-800 mb-2">Your Projected Outcome</h3>
      <p className="text-sm text-gray-700 mb-3">
        With {formatCurrency(initialInvestment)} initial investment
        {annualContribution > 0 && ` and ${formatCurrency(annualContribution)} annual contributions`} 
        at {formatPercent(expectedReturn)} return:
      </p>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="col-span-2 md:col-span-1">
          <p className="text-xs text-gray-600">Projected Value</p>
          <p className="text-xl font-bold text-gray-900">{formatCurrency(outcome.projectedValue)}</p>
        </div>
        <OutcomeStatus label="Base Case" met={outcome.baseCaseMet} gap={outcome.baseCaseGap} />
        <OutcomeStatus label="Worst Case" met={outcome.worstCaseMet} gap={outcome.worstCaseGap} />
        {showCustom && (
          <OutcomeStatus label="Custom" met={outcome.customMet} gap={outcome.customGap} />
        )}
      </div>
    </div>
  );
};

UserOutcomeCard.propTypes = {
  outcome: PropTypes.shape({
    projectedValue: PropTypes.number.isRequired,
    baseCaseMet: PropTypes.bool.isRequired,
    worstCaseMet: PropTypes.bool.isRequired,
    customMet: PropTypes.bool.isRequired,
    baseCaseGap: PropTypes.number.isRequired,
    worstCaseGap: PropTypes.number.isRequired,
    customGap: PropTypes.number.isRequired,
  }),
  initialInvestment: PropTypes.number.isRequired,
  annualContribution: PropTypes.number.isRequired,
  expectedReturn: PropTypes.number.isRequired,
  showCustom: PropTypes.bool.isRequired,
};

/**
 * Outcome status indicator
 */
const OutcomeStatus = ({ label, met, gap }) => (
  <div>
    <p className="text-xs text-gray-600">{label}</p>
    <p className={`text-lg font-semibold ${met ? 'text-green-600' : 'text-red-600'}`}>
      {met ? '✓ Met' : '✗ Short'}
    </p>
    {!met && (
      <p className="text-xs text-gray-600">{formatCurrency(Math.abs(gap))}</p>
    )}
  </div>
);

OutcomeStatus.propTypes = {
  label: PropTypes.string.isRequired,
  met: PropTypes.bool.isRequired,
  gap: PropTypes.number.isRequired,
};

/**
 * Projected outcomes table
 */
const ProjectedOutcomesTable = ({ outcomes, initialInvestment, showCustom }) => (
  <div className="overflow-x-auto">
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-200">
          <th className="px-4 py-3 text-left text-gray-700">Initial Investment</th>
          <th className="px-4 py-3 text-right text-gray-700">Projected Value</th>
          <th className="px-4 py-3 text-center text-gray-700">Base Case</th>
          <th className="px-4 py-3 text-center text-gray-700">Worst Case</th>
          {showCustom && (
            <th className="px-4 py-3 text-center text-gray-700">Custom</th>
          )}
        </tr>
      </thead>
      <tbody>
        {outcomes.map((row, index) => (
          <tr 
            key={index} 
            className={`border-b border-gray-100 hover:bg-gray-50 ${row.investment === initialInvestment ? 'bg-blue-50' : ''}`}
          >
            <td className="px-4 py-3 font-medium">
              {formatCurrency(row.investment)}
              {row.investment === initialInvestment && (
                <span className="ml-1 text-blue-600 text-xs" aria-label="Your amount">★</span>
              )}
            </td>
            <td className="px-4 py-3 text-right font-medium">{formatCurrency(row.projectedValue)}</td>
            <OutcomeCell met={row.baseCaseMet} gap={row.baseCaseGap} additional={row.additionalForBase} />
            <OutcomeCell met={row.worstCaseMet} gap={row.worstCaseGap} additional={row.additionalForWorst} />
            {showCustom && (
              <OutcomeCell met={row.customMet} gap={row.customGap} additional={row.additionalForCustom} />
            )}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

ProjectedOutcomesTable.propTypes = {
  outcomes: PropTypes.arrayOf(PropTypes.shape({
    investment: PropTypes.number.isRequired,
    projectedValue: PropTypes.number.isRequired,
    baseCaseMet: PropTypes.bool.isRequired,
    baseCaseGap: PropTypes.number.isRequired,
    additionalForBase: PropTypes.number.isRequired,
    worstCaseMet: PropTypes.bool.isRequired,
    worstCaseGap: PropTypes.number.isRequired,
    additionalForWorst: PropTypes.number.isRequired,
    customMet: PropTypes.bool.isRequired,
    customGap: PropTypes.number.isRequired,
    additionalForCustom: PropTypes.number.isRequired,
  })).isRequired,
  initialInvestment: PropTypes.number.isRequired,
  showCustom: PropTypes.bool.isRequired,
};

/**
 * Outcome cell in table
 */
const OutcomeCell = ({ met, gap, additional }) => (
  <td className="px-4 py-3">
    <div className="space-y-1">
      <div className={`text-center font-medium ${met ? 'text-green-600' : 'text-red-600'}`}>
        {met ? '✓ Met' : '✗ Short'}
      </div>
      {!met && (
        <>
          <div className="text-xs text-gray-600 text-center">
            Gap: {formatCurrency(gap)}
          </div>
          <div className="text-xs text-gray-600 text-center">
            Need +{formatCurrency(additional)}/yr
          </div>
        </>
      )}
    </div>
  </td>
);

OutcomeCell.propTypes = {
  met: PropTypes.bool.isRequired,
  gap: PropTypes.number.isRequired,
  additional: PropTypes.number.isRequired,
};

/**
 * Key findings section
 */
const KeyFindings = ({ futureValues, totalFunding, inflationScenario, retirementAge, endAge, currentAge, annualContribution }) => (
  <section className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg shadow-lg p-6" aria-labelledby="key-findings-title">
    <h2 id="key-findings-title" className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
      <AlertCircle className="w-5 h-5 text-blue-600" aria-hidden="true" />
      Key Findings
    </h2>
    
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="bg-white rounded-lg p-4">
        <p className="text-sm text-gray-600 mb-1">Income Needed at {retirementAge}</p>
        <p className="text-2xl font-bold text-gray-900">
          {formatCurrency(futureValues.length > 0 ? (futureValues[0]?.[inflationScenario] || 0) : 0)}
        </p>
      </div>
      
      <div className="bg-white rounded-lg p-4">
        <p className="text-sm text-gray-600 mb-1">Income Needed at {endAge}</p>
        <p className="text-2xl font-bold text-gray-900">
          {formatCurrency(futureValues.length > 0 ? (futureValues[futureValues.length - 1]?.[inflationScenario] || 0) : 0)}
        </p>
      </div>
      
      <div className="bg-white rounded-lg p-4">
        <p className="text-sm text-gray-600 mb-1">Total Retirement Funding</p>
        <p className="text-2xl font-bold text-gray-900">
          {formatCurrency(totalFunding[inflationScenario] || 0)}
        </p>
      </div>
    </div>
    
    {annualContribution > 0 && (
      <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>Impact of Annual Contributions:</strong> Adding {formatCurrency(annualContribution)} annually for {retirementAge - currentAge} years 
          totals {formatCurrency(annualContribution * (retirementAge - currentAge))} in additional savings, 
          significantly reducing the required investment returns needed to reach your retirement goals.
        </p>
      </div>
    )}
  </section>
);

KeyFindings.propTypes = {
  futureValues: PropTypes.arrayOf(PropTypes.shape({
    age: PropTypes.number.isRequired,
    years: PropTypes.number.isRequired,
    best: PropTypes.number.isRequired,
    base: PropTypes.number.isRequired,
    worst: PropTypes.number.isRequired,
    custom: PropTypes.number.isRequired,
  })).isRequired,
  totalFunding: PropTypes.shape({
    best: PropTypes.number.isRequired,
    base: PropTypes.number.isRequired,
    worst: PropTypes.number.isRequired,
    custom: PropTypes.number.isRequired,
  }).isRequired,
  inflationScenario: PropTypes.oneOf(['best', 'base', 'worst', 'custom']).isRequired,
  retirementAge: PropTypes.number.isRequired,
  endAge: PropTypes.number.isRequired,
  currentAge: PropTypes.number.isRequired,
  annualContribution: PropTypes.number.isRequired,
};

/**
 * Future income requirements table
 */
const FutureIncomeTable = ({ futureValues, inflationScenario, customInflation }) => (
  <section className="bg-white rounded-lg shadow-lg p-6" aria-labelledby="future-income-title">
    <h2 id="future-income-title" className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
      <TrendingUp className="w-5 h-5 text-blue-600" aria-hidden="true" />
      Future Income Requirements
    </h2>
    
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="px-4 py-3 text-left text-gray-700">Age</th>
            <th className="px-4 py-3 text-left text-gray-700">Years from Now</th>
            <th className="px-4 py-3 text-right text-gray-700">Best Case ({formatPercent(INFLATION_RATES.best)})</th>
            <th className="px-4 py-3 text-right text-gray-700">Base Case ({formatPercent(INFLATION_RATES.base)})</th>
            <th className="px-4 py-3 text-right text-gray-700">Worst Case ({formatPercent(INFLATION_RATES.worst)})</th>
            {inflationScenario === 'custom' && (
              <th className="px-4 py-3 text-right text-gray-700">Custom ({formatPercent(customInflation)})</th>
            )}
          </tr>
        </thead>
        <tbody>
          {futureValues.map((row, index) => (
            <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="px-4 py-3 font-medium">{row.age}</td>
              <td className="px-4 py-3">{row.years}</td>
              <td className="px-4 py-3 text-right">{formatCurrency(row.best)}</td>
              <td className="px-4 py-3 text-right">{formatCurrency(row.base)}</td>
              <td className="px-4 py-3 text-right">{formatCurrency(row.worst)}</td>
              {inflationScenario === 'custom' && (
                <td className="px-4 py-3 text-right font-medium">{formatCurrency(row.custom)}</td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </section>
);

FutureIncomeTable.propTypes = {
  futureValues: PropTypes.arrayOf(PropTypes.shape({
    age: PropTypes.number.isRequired,
    years: PropTypes.number.isRequired,
    best: PropTypes.number.isRequired,
    base: PropTypes.number.isRequired,
    worst: PropTypes.number.isRequired,
    custom: PropTypes.number.isRequired,
  })).isRequired,
  inflationScenario: PropTypes.oneOf(['best', 'base', 'worst', 'custom']).isRequired,
  customInflation: PropTypes.number.isRequired,
};

/**
 * Required annual returns table
 */
const RequiredReturnsTable = ({ requiredReturns, inflationRates, inflationScenario, customInflation, annualContribution }) => (
  <section className="bg-white rounded-lg shadow-lg p-6" aria-labelledby="required-returns-title">
    <h2 id="required-returns-title" className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
      <DollarSign className="w-5 h-5 text-blue-600" aria-hidden="true" />
      Required Annual Returns
    </h2>
    
    <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
      <Info className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <div className="text-sm text-amber-800">
        <p>These returns assume a single lump-sum investment{annualContribution > 0 && ` plus ${formatCurrency(annualContribution)} annual contributions`}.</p>
        <p className="mt-1">Historical S&P 500 average is ~{formatPercent(DEFAULT_VALUES.expectedReturn)} annually. Returns above {RETURN_THRESHOLDS.unrealistic}% are extremely difficult to achieve consistently.</p>
      </div>
    </div>
    
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="px-4 py-3 text-left text-gray-700">Initial Investment</th>
            <th className="px-4 py-3 text-center text-gray-700" colSpan="2">Base Case ({formatPercent(inflationRates.base)})</th>
            <th className="px-4 py-3 text-center text-gray-700" colSpan="2">Worst Case ({formatPercent(inflationRates.worst)})</th>
            {inflationScenario === 'custom' && (
              <th className="px-4 py-3 text-center text-gray-700" colSpan="2">Custom ({formatPercent(customInflation)})</th>
            )}
          </tr>
          <tr className="border-b border-gray-200 text-xs">
            <th className="px-4 py-2"></th>
            <th className="px-4 py-2 text-right text-gray-600">Lump Sum Only</th>
            <th className="px-4 py-2 text-right text-gray-600">With Contributions</th>
            <th className="px-4 py-2 text-right text-gray-600">Lump Sum Only</th>
            <th className="px-4 py-2 text-right text-gray-600">With Contributions</th>
            {inflationScenario === 'custom' && (
              <>
                <th className="px-4 py-2 text-right text-gray-600">Lump Sum Only</th>
                <th className="px-4 py-2 text-right text-gray-600">With Contributions</th>
              </>
            )}
          </tr>
        </thead>
        <tbody>
          {requiredReturns.map((row, index) => (
            <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="px-4 py-3 font-medium">{formatCurrency(row.investment)}</td>
              <ReturnCell value={row.baseReturn} threshold={RETURN_THRESHOLDS.unrealistic} />
              <ReturnCell value={row.baseReturnWithContrib} threshold={RETURN_THRESHOLDS.unrealistic} isWithContrib />
              <ReturnCell value={row.worstReturn} threshold={RETURN_THRESHOLDS.veryUnrealistic} />
              <ReturnCell value={row.worstReturnWithContrib} threshold={RETURN_THRESHOLDS.veryUnrealistic} isWithContrib />
              {inflationScenario === 'custom' && (
                <>
                  <ReturnCell value={row.customReturn} threshold={RETURN_THRESHOLDS.unrealistic} />
                  <ReturnCell value={row.customReturnWithContrib} threshold={RETURN_THRESHOLDS.unrealistic} isWithContrib />
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </section>
);

RequiredReturnsTable.propTypes = {
  requiredReturns: PropTypes.arrayOf(PropTypes.shape({
    investment: PropTypes.number.isRequired,
    baseReturn: PropTypes.number.isRequired,
    baseReturnWithContrib: PropTypes.number.isRequired,
    worstReturn: PropTypes.number.isRequired,
    worstReturnWithContrib: PropTypes.number.isRequired,
    customReturn: PropTypes.number.isRequired,
    customReturnWithContrib: PropTypes.number.isRequired,
  })).isRequired,
  inflationRates: PropTypes.shape({
    best: PropTypes.number.isRequired,
    base: PropTypes.number.isRequired,
    worst: PropTypes.number.isRequired,
    custom: PropTypes.number.isRequired,
  }).isRequired,
  inflationScenario: PropTypes.oneOf(['best', 'base', 'worst', 'custom']).isRequired,
  customInflation: PropTypes.number.isRequired,
  annualContribution: PropTypes.number.isRequired,
};

/**
 * Return rate cell with conditional formatting
 */
const ReturnCell = ({ value, threshold, isWithContrib = false }) => {
  const isUnrealistic = value > threshold;
  const colorClass = isUnrealistic 
    ? 'text-red-600 font-medium' 
    : (isWithContrib ? 'text-green-600 font-medium' : '');

  return (
    <td className={`px-4 py-3 text-right ${colorClass}`}>
      {formatPercent(value)}
    </td>
  );
};

ReturnCell.propTypes = {
  value: PropTypes.number.isRequired,
  threshold: PropTypes.number.isRequired,
  isWithContrib: PropTypes.bool,
};

ReturnCell.defaultProps = {
  isWithContrib: false,
};

/**
 * Planning recommendations section
 */
const PlanningRecommendations = () => (
  <section className="bg-gray-50 rounded-lg p-6" aria-labelledby="recommendations-title">
    <h3 id="recommendations-title" className="text-lg font-semibold text-gray-800 mb-3">Planning Recommendations</h3>
    <ul className="space-y-2 text-sm text-gray-700">
      <li className="flex items-start gap-2">
        <span className="text-blue-600 mt-1" aria-hidden="true">•</span>
        <span>Use the Projected Outcomes section to test if realistic return expectations meet your goals</span>
      </li>
      <li className="flex items-start gap-2">
        <span className="text-blue-600 mt-1" aria-hidden="true">•</span>
        <span>Consider multiple inflation scenarios when planning - the gap between best and worst cases is substantial</span>
      </li>
      <li className="flex items-start gap-2">
        <span className="text-blue-600 mt-1" aria-hidden="true">•</span>
        <span>Required returns above {RETURN_THRESHOLDS.unrealistic}% are extremely difficult to achieve consistently - consider regular contributions</span>
      </li>
      <li className="flex items-start gap-2">
        <span className="text-blue-600 mt-1" aria-hidden="true">•</span>
        <span>Annual contributions dramatically reduce required returns - even modest monthly savings make a big difference</span>
      </li>
      <li className="flex items-start gap-2">
        <span className="text-blue-600 mt-1" aria-hidden="true">•</span>
        <span>Include inflation-hedged assets like TIPS, real estate, and international diversification in your portfolio</span>
      </li>
      <li className="flex items-start gap-2">
        <span className="text-blue-600 mt-1" aria-hidden="true">•</span>
        <span>Maintain flexibility with potential part-time income during early retirement years</span>
      </li>
    </ul>
  </section>
);

export default RetirementInflationCalculator;
