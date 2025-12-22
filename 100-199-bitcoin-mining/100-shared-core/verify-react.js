#!/usr/bin/env node
/**
 * Verify React hooks can be imported (syntax only - no React runtime)
 */

console.log('🔍 Verifying React hooks syntax...\n');

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

test('useLocalStorage hook exports', () => {
  const mod = require('./dist/hooks/useLocalStorage');
  if (typeof mod.useLocalStorage !== 'function') throw new Error('useLocalStorage not a function');
});

test('useMiningCalculations hook exports', () => {
  const mod = require('./dist/hooks/useMiningCalculations');
  if (typeof mod.useMiningCalculations !== 'function') throw new Error('useMiningCalculations not a function');
});

test('useScenarios hook exports', () => {
  const mod = require('./dist/hooks/useScenarios');
  if (typeof mod.useScenarios !== 'function') throw new Error('useScenarios not a function');
});

console.log('\n' + '='.repeat(40));
console.log(`Results: ${passed} passed, ${failed} failed`);

if (failed === 0) {
  console.log('\n✨ React hooks verified!\n');
}

process.exit(failed > 0 ? 1 : 0);

