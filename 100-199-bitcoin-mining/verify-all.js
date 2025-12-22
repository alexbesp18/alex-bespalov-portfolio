#!/usr/bin/env node
/**
 * Quick verification of all projects' shared-core linkage
 */

const fs = require('fs');
const path = require('path');

const projects = [
  '101-bitcoin-mining-calculator',
  '102-bitcoin-mining-electricity-calculator', 
  '103-btc-loan-calculator',
  '104-miner-price-tracker',
  '105-miner-acquisition-calculator',
  '106-hosted-mining-portfolio',
  '107-crypto-calculators-landing',
  '109-portfolio-analyzer'
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
    try {
      const sharedCore = require(path.join(nodeModulesLink, 'dist', 'index.js'));
      
      // Quick sanity check
      if (sharedCore.BLOCK_REWARD && sharedCore.formatCurrency && sharedCore.MINER_DATABASE) {
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

