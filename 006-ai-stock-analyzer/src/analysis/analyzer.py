"""
Multi-agent technical analysis orchestrator.

Coordinates data fetching, parallel AI analysis, and result arbitration
to produce comprehensive technical analysis of stocks.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from src.config import Settings
from src.fetcher.twelve_data import TwelveDataFetcher
from src.llm.client import LLMClient
from src.sheets.writer import SheetsWriter

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """
    Multi-agent technical analysis system.
    
    Orchestrates:
    1. Data fetching from Twelve Data (1 credit per stock)
    2. Parallel analysis across multiple AI models
    3. Result comparison and arbitration
    4. Output to Google Sheets with formatting
    
    Attributes:
        settings: Application settings
        data_fetcher: Twelve Data API client
        llm_client: Unified LLM client
        sheets_writer: Google Sheets output
        reports_dir: Path for markdown reports
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize analyzer with settings.
        
        Args:
            settings: Application configuration
        """
        self.settings = settings
        
        # Initialize data fetcher
        api_key = settings.api_keys.get_twelve_data_key()
        if not api_key:
            raise ValueError("Twelve Data API key not found in config")
        self.data_fetcher = TwelveDataFetcher(api_key)
        
        # Initialize LLM client
        self.llm_client = LLMClient(settings)
        
        # Initialize sheets writer
        self.sheets_writer = SheetsWriter(settings.google_sheet_url)
        
        # Create reports directory
        self.reports_dir = Path('stock_reports')
        self.reports_dir.mkdir(exist_ok=True)
        
        # Stats tracking
        self.stats = {
            'successful': 0,
            'failed': 0,
            'total_cost': 0.0,
            'full_agreement': 0,
            'partial_agreement': 0,
            'major_disagreement': 0
        }
    
    def analyze_ticker(self, ticker: str) -> Dict:
        """
        Run complete analysis for a single ticker.
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            
        Returns:
            Complete analysis result dictionary
        """
        logger.info(f"\n{'='*70}\nANALYZING: {ticker}\n{'='*70}")
        
        # Step 1: Fetch market data (ONLY 1 CREDIT!)
        market_data = self.data_fetcher.get_complete_analysis_data(ticker)
        if not market_data:
            logger.error(f"Failed to fetch market data for {ticker}")
            return {'success': False, 'error': 'Market data fetch failed', 'ticker': ticker}
        
        market_data['current_price'] = market_data['quote']['price']
        
        logger.info("Running agent analyses in parallel")
        
        # Step 2: Run all agents in parallel
        results = self._run_parallel_analysis(ticker, market_data)
        
        # Add full market data to each result
        full_results = [{**market_data, **r} for r in results]
        
        # Step 3: Check results
        valid = [r for r in full_results if r.get('success')]
        if not valid:
            logger.error("ALL AGENTS FAILED")
            return {'success': False, 'error': 'All agents failed', 'ticker': ticker}
        
        if len(valid) == 1:
            logger.warning("Only 1 agent succeeded, using its results")
            final = valid[0]
            final.update({
                'total_cost': final.get('cost', 0),
                'ticker': ticker,
                'agreement_level': 'SINGLE_AGENT',
                'discrepancies': {}
            })
            return final
        
        # Step 4: Compare and arbitrate
        agreement, discrepancies = self._compare_analyses(valid)
        self._update_agreement_stats(agreement)
        
        aligned = self._arbitrate_results(ticker, valid, agreement, discrepancies)
        aligned['total_cost'] = sum(r.get('cost', 0) for r in valid) + aligned.get('cost', 0)
        
        # Create report
        self._create_report(ticker, valid, aligned, agreement, discrepancies)
        
        logger.info(
            f"\n{'='*66}\n"
            f"Cost: ${aligned['total_cost']:.4f} | Agreement: {agreement}\n"
            f"Technical Score: {aligned.get('technical_score', 'N/A')}/10\n"
            f"Price: ${aligned.get('current_price', 0):.2f} | "
            f"Entry: ${aligned.get('optimal_entry', 0):.2f}\n"
            f"{'='*66}"
        )
        
        return aligned
    
    def _run_parallel_analysis(self, ticker: str, market_data: Dict) -> List[Dict]:
        """Run analysis with all enabled agents in parallel."""
        global_config = self.settings.global_settings
        
        def safe_analyze(func, name):
            try:
                return func(ticker, market_data)
            except Exception as e:
                logger.error(f"{name} failed: {e}")
                return {'success': False, 'model': name, 'error': str(e), 'cost': 0.0}
        
        if global_config.use_concurrent:
            with ThreadPoolExecutor(max_workers=global_config.max_workers) as executor:
                futures = [
                    executor.submit(safe_analyze, self.llm_client.analyze_with_gemini, 'gemini'),
                    executor.submit(safe_analyze, self.llm_client.analyze_with_grok, 'grok'),
                    executor.submit(safe_analyze, self.llm_client.analyze_with_gpt, 'gpt')
                ]
                return [f.result() for f in futures]
        else:
            return [
                safe_analyze(self.llm_client.analyze_with_gemini, 'gemini'),
                safe_analyze(self.llm_client.analyze_with_grok, 'grok'),
                safe_analyze(self.llm_client.analyze_with_gpt, 'gpt')
            ]
    
    def _compare_analyses(self, results: List[Dict]) -> Tuple[str, Dict]:
        """Compare agent results and determine agreement level."""
        if len(results) < 2:
            return 'INSUFFICIENT_DATA', {}
        
        tech_scores = [r['technical_score'] for r in results]
        tech_variance = np.var(tech_scores)
        
        discrepancies = {}
        if tech_variance > 4.0:
            discrepancies['technical_score'] = f"High variance: {tech_scores}"
        
        if tech_variance < 1.0:
            return 'FULL_AGREEMENT', discrepancies
        elif tech_variance < 2.5:
            return 'PARTIAL_AGREEMENT', discrepancies
        else:
            return 'MAJOR_DISAGREEMENT', discrepancies
    
    def _update_agreement_stats(self, agreement: str) -> None:
        """Update agreement statistics."""
        if agreement == 'FULL_AGREEMENT':
            self.stats['full_agreement'] += 1
        elif agreement == 'PARTIAL_AGREEMENT':
            self.stats['partial_agreement'] += 1
        else:
            self.stats['major_disagreement'] += 1
    
    def _arbitrate_results(
        self, ticker: str, results: List[Dict],
        agreement: str, discrepancies: Dict
    ) -> Dict:
        """Arbitrate between agent results."""
        base_result = results[0]
        
        def avg(key):
            values = [r[key] for r in results if key in r]
            return round(sum(values) / len(values), 2) if values else None
        
        if agreement == 'FULL_AGREEMENT':
            logger.info("Full agreement - averaging results")
            final = {
                'technical_score': avg('technical_score'),
                'optimal_entry': avg('optimal_entry'),
                'closest_support': avg('closest_support'),
                'key_support': avg('key_support'),
                'closest_resistance': avg('closest_resistance'),
                'strongest_resistance': avg('strongest_resistance'),
                'cost': 0,
                'reasoning': "Full agreement between models."
            }
        elif self.llm_client.claude_client:
            logger.info(f"Claude arbitrating ({agreement})")
            try:
                final = self.llm_client.arbitrate_with_claude(ticker, results, discrepancies)
            except Exception as e:
                logger.error(f"Arbitration failed: {e}, using average")
                final = self._average_results(results)
        else:
            logger.warning("Claude disabled, using average for arbitration")
            final = self._average_results(results)
        
        # Merge with base data
        complete = {**base_result, **final}
        complete.update({
            'ticker': ticker,
            'agreement_level': agreement,
            'discrepancies': discrepancies,
            'success': True
        })
        
        return complete
    
    def _average_results(self, results: List[Dict]) -> Dict:
        """Average numeric results across agents."""
        def avg(key):
            values = [r[key] for r in results if key in r]
            return round(sum(values) / len(values), 2) if values else None
        
        return {
            'technical_score': avg('technical_score'),
            'optimal_entry': avg('optimal_entry'),
            'closest_support': avg('closest_support'),
            'key_support': avg('key_support'),
            'closest_resistance': avg('closest_resistance'),
            'strongest_resistance': avg('strongest_resistance'),
            'cost': 0,
            'reasoning': "Averaged results across models."
        }
    
    def _create_report(
        self, ticker: str, results: List[Dict],
        final: Dict, agreement: str, discrepancies: Dict
    ) -> str:
        """Create markdown report for the analysis."""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = self.reports_dir / f"{ticker}_{timestamp}.md"
        
        disc_section = "\n## ✅ All Models Aligned\n" if not discrepancies else \
                      "\n## ⚠️ Discrepancies\n" + "\n".join(f"- {k}: {v}" for k, v in discrepancies.items())
        
        models_section = ""
        for r in results:
            if r.get('success'):
                models_section += f"\n### {r['model'].upper()}\n"
                models_section += f"Technical Score: {r.get('technical_score', 'N/A')}/10\n"
                if 'reasoning' in r:
                    models_section += f"Reasoning: {r['reasoning']}\n"
        
        content = f"""# Technical Analysis: {ticker}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Data Source**: Twelve Data API (Optimized 1-Credit Method)
**Agreement**: {agreement}

## 📊 Final Results
Price: ${final.get('current_price', 0):.2f} | Technical Score: {final.get('technical_score', 'N/A')}/10
Optimal Entry: ${final.get('optimal_entry', 0):.2f}
Support: ${final.get('closest_support', 0):.2f} / ${final.get('key_support', 0):.2f}
Resistance: ${final.get('closest_resistance', 0):.2f} / ${final.get('strongest_resistance', 0):.2f}
Moving Averages: ${final.get('ma_20', 0):.2f} / ${final.get('ma_50', 0):.2f} / ${final.get('ma_200', 0):.2f}
RSI: {final.get('rsi', 0):.1f}

{disc_section}

## 🤖 Models
{models_section}

## 💰 Cost
Total: ${final.get('total_cost', 0):.4f}
Twelve Data: 1 credit per stock (90% savings!)

---
*Pure Technical Analysis - All indicators calculated client-side from single time_series call*
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Report: {filename.name}")
        return str(filename)
    
    def process_tickers(self, tickers: List[str] = None, start_row: int = 2) -> None:
        """
        Process tickers from list or Google Sheet.
        
        Args:
            tickers: Optional list of tickers. If None, reads from sheet.
            start_row: Starting row for sheet data
        """
        if tickers:
            self._process_ticker_list(tickers)
        elif self.sheets_writer.is_connected:
            self._process_from_sheet(start_row)
        else:
            logger.error("No tickers provided and Google Sheets not connected")
    
    def _process_ticker_list(self, tickers: List[str]) -> None:
        """Process a list of tickers."""
        logger.info(f"\n{'='*70}\nProcessing {len(tickers)} tickers\n{'='*70}")
        
        for idx, ticker in enumerate(tickers):
            logger.info(f"\n[{idx+1}/{len(tickers)}] {ticker}")
            result = self.analyze_ticker(ticker)
            
            if result.get('success'):
                self.stats['successful'] += 1
                self.stats['total_cost'] += result.get('total_cost', 0)
            else:
                self.stats['failed'] += 1
            
            if idx < len(tickers) - 1:
                time.sleep(2)
        
        self._print_summary(len(tickers))
    
    def _process_from_sheet(self, start_row: int) -> None:
        """Process tickers from Google Sheet."""
        logger.info(f"\n{'='*70}\nLOADING TICKERS FROM SHEET\n{'='*70}")
        
        all_values = self.sheets_writer.sheet.get_all_values()
        
        # Check/setup headers
        if not all_values or len(all_values[0]) < 22 or all_values[0][0] != 'Ticker':
            logger.info("Setting up headers")
            self.sheets_writer.setup_headers()
            all_values = self.sheets_writer.sheet.get_all_values()
        
        tickers = [
            {'symbol': row[0].strip().upper(), 'row_num': idx}
            for idx, row in enumerate(all_values[start_row-1:], start=start_row)
            if row and row[0].strip()
        ]
        
        if not tickers:
            logger.warning("No tickers found in Column A")
            return
        
        logger.info(f"Found {len(tickers)} ticker(s)")
        
        for idx, t in enumerate(tickers):
            logger.info(f"\n[{idx+1}/{len(tickers)}] {t['symbol']}")
            result = self.analyze_ticker(t['symbol'])
            
            if result.get('success'):
                self.sheets_writer.write_result(t['row_num'], result)
                self.stats['successful'] += 1
                self.stats['total_cost'] += result.get('total_cost', 0)
            else:
                self.stats['failed'] += 1
                try:
                    self.sheets_writer.sheet.update(
                        values=[[f"ERROR: {result.get('error', 'Unknown')}"]],
                        range_name=f"N{t['row_num']}"
                    )
                except Exception:
                    pass
            
            if idx < len(tickers) - 1:
                time.sleep(2)
        
        self._print_summary(len(tickers))
    
    def _print_summary(self, total: int) -> None:
        """Print final summary."""
        logger.info(f"""
{'='*70}
COMPLETE
{'='*70}
Processed: {total} | Success: {self.stats['successful']} | Failed: {self.stats['failed']}

🤝 Agreement:
  Full: {self.stats['full_agreement']}
  Partial: {self.stats['partial_agreement']}
  Major: {self.stats['major_disagreement']}

💰 Total cost: ${self.stats['total_cost']:.4f}
{'   Avg/ticker: $' + f"{self.stats['total_cost']/self.stats['successful']:.4f}" if self.stats['successful'] > 0 else ''}

💡 Twelve Data Savings: ~90% (1 credit vs 7+ per stock)
{'✅ Results in Google Sheet' if self.sheets_writer.is_connected else '⚠️ Google Sheets not configured'}
📁 Reports in: {self.reports_dir.absolute()}
{'='*70}
""")
