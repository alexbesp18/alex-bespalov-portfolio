#!/usr/bin/env node
/**
 * Quick verification script for shared-core
 * Tests that all modules load and key functions work
 */

console.log('🔍 Verifying @btc-mining/shared-core...\n');

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✅ ${name}`);
    passed++;
  } catch (e) {
    console.log(`  ❌ ${name}: ${e.message}`);
    failed++;
  }
}

// Test Constants
console.log('📦 Constants:');
test('bitcoin constants', () => {
  const { BLOCK_REWARD, BLOCKS_PER_DAY } = require('./dist/constants/bitcoin');
  if (BLOCK_REWARD !== 3.125) throw new Error('BLOCK_REWARD wrong');
  if (BLOCKS_PER_DAY !== 144) throw new Error('BLOCKS_PER_DAY wrong');
});

test('tax constants', () => {
  const { MACRS_RATES } = require('./dist/constants/tax');
  if (!Array.isArray(MACRS_RATES)) throw new Error('MACRS_RATES not array');
  if (MACRS_RATES[0] !== 0.20) throw new Error('MACRS_RATES[0] wrong');
});

test('electricity constants', () => {
  const { ELECTRICITY_RATES } = require('./dist/constants/electricity');
  if (!Array.isArray(ELECTRICITY_RATES)) throw new Error('ELECTRICITY_RATES not array');
});

test('defaults', () => {
  const { DEFAULT_PARAMS } = require('./dist/constants/defaults');
  if (!DEFAULT_PARAMS.btcPriceStart) throw new Error('DEFAULT_PARAMS missing btcPriceStart');
});

// Test Calculations
console.log('\n📊 Calculations:');
test('mining calculations', () => {
  const { calculateDailyBtcMined, calculateMonthlyProfit } = require('./dist/calculations/mining');
  const daily = calculateDailyBtcMined(500, 1000);
  if (typeof daily !== 'number' || daily <= 0) throw new Error('calculateDailyBtcMined failed');
});

test('projections', () => {
  const { calculateYearlyProfit } = require('./dist/calculations/projections');
  if (typeof calculateYearlyProfit !== 'function') throw new Error('calculateYearlyProfit not a function');
});

test('risk calculations', () => {
  const { calculateIRR, getCellColor } = require('./dist/calculations/risk');
  if (typeof calculateIRR !== 'function') throw new Error('calculateIRR not a function');
  const color = getCellColor(100, 'roi');
  if (typeof color !== 'string') throw new Error('getCellColor failed');
});

// Test Data
console.log('\n💾 Data:');
test('miner database', () => {
  const { MINER_DATABASE, getMinerById } = require('./dist/data/miners');
  if (!Array.isArray(MINER_DATABASE)) throw new Error('MINER_DATABASE not array');
  if (MINER_DATABASE.length < 20) throw new Error('MINER_DATABASE too small');
});

test('scenarios', () => {
  const { PRESET_SCENARIOS } = require('./dist/data/scenarios');
  if (!PRESET_SCENARIOS.current) throw new Error('Missing current scenario');
});

// Test Formatters
console.log('\n🎨 Formatters:');
test('currency formatter', () => {
  const { formatCurrency } = require('./dist/formatters/currency');
  const result = formatCurrency(1234);
  if (!result.includes('1,234')) throw new Error('formatCurrency failed');
});

test('number formatter', () => {
  const { formatPercentage } = require('./dist/formatters/numbers');
  const result = formatPercentage(45.6);
  if (result !== '45.6%') throw new Error('formatPercentage failed');
});

// Test Validation
console.log('\n✔️ Validation:');
test('number validation', () => {
  const { validateNumber, clamp } = require('./dist/validation/numbers');
  if (validateNumber(-10, 0, 100) !== 0) throw new Error('validateNumber failed');
  if (clamp(150, 0, 100) !== 100) throw new Error('clamp failed');
});

test('miner validation', () => {
  const { validateMiner } = require('./dist/validation/miners');
  const result = validateMiner({ hashrate: 500, power: 5500 });
  if (!result.isValid) throw new Error('validateMiner failed for valid miner');
});

// Test Storage
console.log('\n💿 Storage:');
test('storage utilities', () => {
  const { safeJSONParse, safeJSONStringify } = require('./dist/storage/localStorage');
  if (safeJSONParse('{"a":1}').a !== 1) throw new Error('safeJSONParse failed');
  if (safeJSONStringify({a:1}) !== '{"a":1}') throw new Error('safeJSONStringify failed');
});

test('compression', () => {
  const { compressString, decompressString } = require('./dist/storage/compression');
  const original = 'test string test string test string';
  const compressed = compressString(original);
  const decompressed = decompressString(compressed);
  if (decompressed !== original) throw new Error('compression roundtrip failed');
});

// Test Export
console.log('\n📤 Export:');
test('csv utilities', () => {
  const { arrayToCSV, parseCSV } = require('./dist/export/csv');
  const csv = arrayToCSV([{a: 1, b: 2}]);
  if (!csv.includes('a') || !csv.includes('1')) throw new Error('arrayToCSV failed');
});

// Test main index exports
console.log('\n📚 Main Index:');
test('main index exports', () => {
  const core = require('./dist/index');
  if (!core.BLOCK_REWARD) throw new Error('BLOCK_REWARD not exported');
  if (!core.formatCurrency) throw new Error('formatCurrency not exported');
  if (!core.calculateDailyBtcMined) throw new Error('calculateDailyBtcMined not exported');
  if (!core.MINER_DATABASE) throw new Error('MINER_DATABASE not exported');
});

// Summary
console.log('\n' + '='.repeat(40));
console.log(`Results: ${passed} passed, ${failed} failed`);
console.log('='.repeat(40));

if (failed > 0) {
  process.exit(1);
} else {
  console.log('\n✨ All verifications passed!\n');
  process.exit(0);
}

