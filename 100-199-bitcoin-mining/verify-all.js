#!/usr/bin/env node
/**
 * Quick verification of all projects' shared-core linkage
 */

const fs = require('fs');
const path = require('path');

const projects = [
  '101-mining-profitability-calculator',
  '102-btc-loan-calculator',
  '103-miner-price-tracker',
  '104-portfolio-analyzer',
  '105-landing-page'
  // Note: 106-miner-price-scraper is Python-based, not Node.js
];

console.log('🔍 Verifying shared-core linkage in all projects...\n');

let passed = 0;
let failed = 0;

for (const project of projects) {
  const projectPath = path.join(__dirname, project);
  const pkgPath = path.join(projectPath, 'package.json');
  const nodeModulesLink = path.join(projectPath, 'node_modules', '@btc-mining', 'shared-core');
  
  // Check package.json has dependency
  try {
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
    const hasDep = pkg.dependencies && pkg.dependencies['@btc-mining/shared-core'];
    
    if (!hasDep) {
      console.log(`❌ ${project}: Missing @btc-mining/shared-core dependency`);
      failed++;
      continue;
    }
    
    // Check if node_modules link exists
    const linkExists = fs.existsSync(nodeModulesLink);
    
    if (!linkExists) {
      console.log(`⚠️  ${project}: Dependency declared but not installed (run npm install)`);
      failed++;
      continue;
    }
    
    // Try to require the shared-core from the project
    // Note: We only test constants module because hooks require React
    try {
      const constants = require(path.join(nodeModulesLink, 'dist', 'constants', 'index.js'));
      const data = require(path.join(nodeModulesLink, 'dist', 'data', 'index.js'));
      const formatters = require(path.join(nodeModulesLink, 'dist', 'formatters', 'index.js'));

      // Quick sanity check on non-React exports
      if (constants.BLOCK_REWARD && formatters.formatCurrency && data.MINER_DATABASE) {
        console.log(`✅ ${project}: Linked and working`);
        passed++;
      } else {
        console.log(`❌ ${project}: Linked but exports missing`);
        failed++;
      }
    } catch (e) {
      console.log(`❌ ${project}: Link broken - ${e.message}`);
      failed++;
    }
    
  } catch (e) {
    console.log(`❌ ${project}: Error - ${e.message}`);
    failed++;
  }
}

console.log('\n' + '='.repeat(50));
console.log(`Results: ${passed} passed, ${failed} failed out of ${projects.length} projects`);
console.log('='.repeat(50));

if (failed > 0) {
  console.log('\n⚠️  To fix failed projects, run:');
  console.log('   cd <project> && npm install --legacy-peer-deps\n');
  process.exit(1);
} else {
  console.log('\n✨ All projects verified!\n');
  process.exit(0);
}

