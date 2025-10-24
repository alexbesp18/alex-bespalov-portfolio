# AI-Powered Technical Stock Analyzer

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> Multi-agent AI system for technical stock analysis using Claude, GPT-4, and Gemini

## 🎯 Overview

**Problem:** Traditional stock analysis is expensive, uses outdated methods, and lacks AI insights.

**Solution:** A 3-agent AI system that analyzes stocks using multiple AI models for consensus-based recommendations.

**Impact:**
- **90% API cost reduction** - 1 credit per stock vs 7+ previously
- **Multi-model consensus** - Reduces AI bias and hallucination
- **Automated analysis** - Processes watchlists in minutes
- **Actionable insights** - Clear recommendations with confidence scores

## ✨ Features

- 🤖 **3-Agent AI System** - Claude 4, GPT-4, and Gemini analyze independently
- 📊 **20+ Technical Indicators** - RSI, MACD, Bollinger Bands, ATR, ADX, Stochastic
- ⚡ **Optimized API** - Single call per stock with client-side calculations
- 📈 **Google Sheets Integration** - Automated formatting and results
- 🎯 **Consensus Decisions** - AI arbitrator resolves disagreements
- 💰 **Support/Resistance** - Automated key level identification

## 🛠️ Tech Stack

**Core:**
- Python 3.9+, Pandas, NumPy

**AI Models:**
- Anthropic Claude Sonnet 4.5
- OpenAI GPT-4 Turbo
- Google Gemini 2.0

**APIs:**
- Twelve Data API (market data)
- Google Sheets API (output)

## 🏗️ Architecture

```
Twelve Data API (1 call)
         ↓
Technical Calculator
(Client-Side Indicators)
         ↓
┌────────────────────┐
│ 3 AI Agents        │
│ Claude | GPT | Gem │
└───────┬────────────┘
        ↓
Claude Arbitrator
(Consensus)
        ↓
Google Sheets
(Formatted Results)
```

## 🚀 Setup

### Prerequisites
```bash
Python 3.9+
API Keys: Anthropic, OpenAI, Google AI, Twelve Data
Google Cloud Service Account
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp config.json.example config.json
# Edit config.json with your API keys

# Run
python technical_analyzer.py
```

## 📊 Technical Indicators

- **Trend:** SMA (20/50/200), EMA, MACD, ADX
- **Momentum:** RSI, Stochastic, MACD Histogram
- **Volatility:** Bollinger Bands, ATR
- **Support/Resistance:** Key levels, pivot points
- **Volume:** VWAP, volume trends

## 💡 Innovation

### Cost Optimization
- **Before:** 7+ API calls per stock ($0.07+)
- **After:** 1 API call per stock ($0.01)
- **Savings:** 90%

### Multi-Agent Consensus
- Reduces hallucination
- Catches conflicting signals
- More robust recommendations

## 📝 License

MIT License

## 🤝 Contact

**Alex Bespalov**  
📧 [Your Email]  
💼 [LinkedIn](https://linkedin.com/in/yourprofile)  
🌐 [GitHub](https://github.com/alexbesp18)

---

⭐ Star this repo if you find it useful!
