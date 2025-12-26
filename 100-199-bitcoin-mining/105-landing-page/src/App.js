import React, { useState } from 'react';
import { Calculator, TrendingUp, DollarSign, ArrowRight, Shield, Clock, BarChart3, Building2, Coffee, Copy, Check, Grid3x3, LineChart } from 'lucide-react';

function App() {
  const [copied, setCopied] = useState(false);
  const btcAddress = 'bc1q7fcyqpenn624vky3dvda5nd6h48e2xjslz3037';

  const copyToClipboard = () => {
    navigator.clipboard.writeText(btcAddress);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  const calculators = [
    {
      title: "Bitcoin Mining Profitability Calculator",
      description: "All-in-one matrix comparison tool with 20+ miners, multiple electricity rates, 2-year projections, and Acquisition Mode to find maximum purchase prices for target profits.",
      url: "https://bitcoin-mining-calculator.vercel.app",
      icon: <Grid3x3 className="w-6 h-6" />,
      features: ["Matrix comparison", "Acquisition mode", "2-year projections", "Tax optimization"]
    },
    {
      title: "BTC Loan Calculator",
      description: "Advanced Bitcoin-backed loan calculations with real-time LTV monitoring, liquidation analysis, and scenario planning",
      url: "https://btc-loan-calculator.vercel.app",
      icon: <DollarSign className="w-6 h-6" />,
      features: ["LTV monitoring", "Liquidation price alerts", "Price shock scenarios", "Future projections"]
    },
    {
      title: "Miner Price Tracker",
      description: "Track historical miner hardware prices with daily/intraday data, upload Excel/CSV files, and analyze price trends over time.",
      url: "https://miner-price-tracker.vercel.app",
      icon: <LineChart className="w-6 h-6" />,
      features: ["Price history tracking", "Excel/CSV upload", "Rollback functionality", "Efficiency database"]
    },
    {
      title: "Portfolio Analyzer",
      description: "Comprehensive investment portfolio analysis across BTC, stocks, mining operations, and options with multi-company hosting management.",
      url: "https://portfolio-analyzer.vercel.app",
      icon: <Building2 className="w-6 h-6" />,
      features: ["Multi-asset tracking", "Mining operations", "Options valuation", "Debt management"]
    },
    {
      title: "Retirement Inflation Calculator",
      description: "Plan for inflation's impact on retirement with advanced projections, multiple scenarios, and contribution analysis",
      url: "https://retirement-calculator-sand.vercel.app/",
      icon: <TrendingUp className="w-6 h-6" />,
      features: ["Inflation scenarios", "Required returns", "Contribution planning", "Future value analysis"]
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Calculator className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Mine and Hodl BTC Calculators</h1>
            </div>
            <div className="text-sm text-gray-600">
              Professional Bitcoin Tools
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center">
          <h2 className="text-4xl font-bold text-gray-900 sm:text-5xl">
            Mine and Hodl BTC Calculators
          </h2>
          <p className="mt-6 text-xl text-gray-600 max-w-3xl mx-auto">
            Advanced calculation tools for Bitcoin mining, lending, and investment decisions. 
            Built for professionals who need accurate financial modeling. 7 powerful calculators to optimize your Bitcoin operations and retirement planning.
          </p>
          
          {/* Trust Indicators */}
          <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-2xl mx-auto">
            <div className="flex items-center justify-center space-x-2 text-gray-600">
              <Shield className="w-5 h-5 text-green-500" />
              <span>Data Stays Local</span>
            </div>
            <div className="flex items-center justify-center space-x-2 text-gray-600">
              <Clock className="w-5 h-5 text-blue-500" />
              <span>Real-time Calculations</span>
            </div>
            <div className="flex items-center justify-center space-x-2 text-gray-600">
              <Calculator className="w-5 h-5 text-purple-500" />
              <span>Tax Optimized</span>
            </div>
          </div>
        </div>
      </section>

      {/* Calculators Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {calculators.map((calc, index) => (
            <div key={index} className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 overflow-hidden">
              <div className="p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                    {calc.icon}
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900">
                    {calc.title}
                  </h3>
                </div>
                
                <p className="text-gray-600 mb-6">
                  {calc.description}
                </p>
                
                <a 
                  href={calc.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors duration-200"
                >
                  Open Calculator
                  <ArrowRight className="w-4 h-4 ml-2" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Custom Calculator CTA */}
      <section className="bg-gradient-to-r from-purple-50 to-blue-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Want a custom calculator?
            </h3>
            <p className="text-lg text-gray-600 mb-6">
              Need a specific Bitcoin calculation tool for your business or personal use? 
              I can build custom calculators tailored to your exact needs.
            </p>
            <a 
              href="mailto:user@example.com"
              className="inline-flex items-center justify-center px-8 py-3 bg-purple-600 text-white font-semibold rounded-lg hover:bg-purple-700 transition-colors duration-200"
            >
              Let me know
              <ArrowRight className="w-4 h-4 ml-2" />
            </a>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900">
              Why Choose Our Calculators?
            </h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <BarChart3 className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Professional Grade</h3>
              <p className="text-gray-600">Built with real-world mining and lending experience. Every calculation accounts for fees, taxes, and market conditions.</p>
            </div>
            
            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <Shield className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Privacy First</h3>
              <p className="text-gray-600">All calculations run locally in your browser. Your financial data never leaves your device.</p>
            </div>
            
            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mb-4">
                <TrendingUp className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Save & Export</h3>
              <p className="text-gray-600">Export your calculations, save scenarios, and import data for seamless workflow integration.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <Calculator className="w-6 h-6" />
              <span className="text-xl font-bold">Mine and Hodl BTC Calculators</span>
            </div>
            <p className="text-gray-400">
              Professional Bitcoin calculation tools for mining, lending, and investment analysis
            </p>
            <div className="mt-6 space-y-3">
              <a 
                href="https://strike.me/mineandhodl" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center px-6 py-2 bg-orange-500 text-white font-medium rounded-lg hover:bg-orange-600 transition-colors duration-200"
              >
                <Coffee className="w-4 h-4 mr-2" />
                Buy me a coffee
              </a>
              <div className="text-sm text-gray-400">
                <div className="flex items-center justify-center space-x-2">
                  <span>BTC:</span>
                  <button
                    onClick={copyToClipboard}
                    className="bg-gray-800 px-2 py-1 rounded text-xs hover:bg-gray-700 transition-colors duration-200 flex items-center space-x-1"
                  >
                    <code>{btcAddress}</code>
                    {copied ? (
                      <Check className="w-3 h-3 text-green-400" />
                    ) : (
                      <Copy className="w-3 h-3" />
                    )}
                  </button>
                </div>
              </div>
            </div>
            <div className="mt-8 text-sm text-gray-500">
              © 2025 Mine and Hodl BTC Calculators. All calculations are estimates. Always verify with your own analysis.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
