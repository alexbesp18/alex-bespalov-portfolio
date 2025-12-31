/**
 * Shared PropTypes definitions
 */

import PropTypes from 'prop-types';

/**
 * Miner object shape
 */
export const MinerShape = PropTypes.shape({
  id: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  fullName: PropTypes.string.isRequired,
  hashrate: PropTypes.number.isRequired,
  power: PropTypes.number.isRequired,
  efficiency: PropTypes.number.isRequired,
  defaultPrice: PropTypes.number.isRequired,
  manufacturer: PropTypes.string.isRequired,
  coolingType: PropTypes.string.isRequired,
  releaseYear: PropTypes.number.isRequired,
  series: PropTypes.string.isRequired
});

/**
 * Parameters object shape
 */
export const ParamsShape = PropTypes.shape({
  btcPriceStart: PropTypes.number.isRequired,
  btcPriceEnd: PropTypes.number.isRequired,
  networkHashrateStart: PropTypes.number.isRequired,
  networkHashrateEnd: PropTypes.number.isRequired,
  poolFee: PropTypes.number.isRequired,
  taxRate: PropTypes.number.isRequired,
  stateRate: PropTypes.number.isRequired,
  useBonusDepreciation: PropTypes.bool.isRequired,
  annualBtcPriceIncrease: PropTypes.number,
  annualDifficultyIncrease: PropTypes.number,
  useAnnualIncreases: PropTypes.bool
});

/**
 * Monthly data shape
 */
export const MonthlyDataShape = PropTypes.shape({
  month: PropTypes.number.isRequired,
  btcPrice: PropTypes.number.isRequired,
  networkHashrate: PropTypes.number.isRequired,
  btcMined: PropTypes.number.isRequired,
  btcMinedNet: PropTypes.number.isRequired,
  grossRevenue: PropTypes.number.isRequired,
  poolFees: PropTypes.number.isRequired,
  netRevenue: PropTypes.number.isRequired,
  electricityCost: PropTypes.number.isRequired,
  operationalProfit: PropTypes.number.isRequired
});

/**
 * Yearly profit details shape
 */
export const YearlyProfitShape = PropTypes.shape({
  monthlyData: PropTypes.arrayOf(MonthlyDataShape).isRequired,
  totalBtcMined: PropTypes.number.isRequired,
  totalRevenue: PropTypes.number.isRequired,
  totalElectricity: PropTypes.number.isRequired,
  totalPoolFees: PropTypes.number.isRequired,
  totalOperationalProfit: PropTypes.number.isRequired,
  depreciation: PropTypes.number.isRequired,
  taxableIncome: PropTypes.number.isRequired,
  federalTax: PropTypes.number.isRequired,
  stateTax: PropTypes.number.isRequired,
  totalTax: PropTypes.number.isRequired,
  afterTaxProfit: PropTypes.number.isRequired,
  netProfit: PropTypes.number.isRequired,
  roi: PropTypes.number.isRequired,
  minerPrice: PropTypes.number.isRequired,
  year: PropTypes.number.isRequired
});
