"""
Tests using real cached market data to verify actual results.

Uses cached Twelve Data responses from 007-ticker-analysis to test
end-to-end processing without hitting the API.
"""

import pytest
import json
import pandas as pd
from pathlib import Path

from shared_core.data import (
    process_ohlcv_data,
    add_standard_indicators,
    calculate_matrix,
    calculate_bullish_score,
    calculate_bullish_score_detailed,
)
from shared_core.divergence import detect_combined_divergence
from shared_core.scoring import score_rsi, score_stochastic, DivergenceType
from shared_core.triggers import evaluate_ticker, WATCHLIST_SIGNALS, PORTFOLIO_SIGNALS


# Path to real cached data
CACHE_DIR = Path(__file__).parent.parent.parent / "007-ticker-analysis" / "data" / "twelve_data"


def get_cached_tickers():
    """Get list of available cached tickers."""
    if not CACHE_DIR.exists():
        return []
    return sorted(set(f.stem.split("_")[0] for f in CACHE_DIR.glob("*.json")))


def load_cached_data(ticker: str):
    """Load most recent cached data for a ticker as a DataFrame."""
    files = sorted(CACHE_DIR.glob(f"{ticker}_*.json"), reverse=True)
    if not files:
        return None
    with open(files[0]) as f:
        data = json.load(f)
    
    # Data is in pandas to_dict() format, convert back to DataFrame
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.set_index('datetime').sort_index()
    
    # Ensure numeric types
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


# Skip if no cached data available
CACHED_TICKERS = get_cached_tickers()
SKIP_NO_CACHE = pytest.mark.skipif(
    len(CACHED_TICKERS) == 0,
    reason="No cached data available in 007-ticker-analysis"
)


@SKIP_NO_CACHE
class TestRealDataProcessing:
    """Test processing with real cached market data."""
    
    @pytest.mark.parametrize("ticker", CACHED_TICKERS[:10] if CACHED_TICKERS else ["NVDA"])
    def test_process_real_ticker(self, ticker):
        """Process real ticker data end-to-end."""
        raw_df = load_cached_data(ticker)
        if raw_df is None:
            pytest.skip(f"No data for {ticker}")
        
        assert len(raw_df) >= 200, f"{ticker} has insufficient data: {len(raw_df)} rows"
        
        # Add indicators
        df = add_standard_indicators(raw_df.copy())
        
        # Verify all expected columns
        expected_cols = ['open', 'high', 'low', 'close', 'volume', 
                        'SMA_20', 'SMA_50', 'SMA_200', 'RSI', 
                        'MACD', 'MACD_SIGNAL', 'MACD_HIST',
                        'BB_UPPER', 'BB_MIDDLE', 'BB_LOWER',
                        'STOCH_K', 'STOCH_D', 'ATR']
        for col in expected_cols:
            assert col in df.columns, f"{ticker} missing column: {col}"
    
    @pytest.mark.parametrize("ticker", CACHED_TICKERS[:10] if CACHED_TICKERS else ["NVDA"])
    def test_calculate_bullish_score_real(self, ticker):
        """Calculate bullish score for real tickers."""
        raw_df = load_cached_data(ticker)
        if raw_df is None:
            pytest.skip(f"No data for {ticker}")
        
        df = add_standard_indicators(raw_df.copy())
        score, breakdown = calculate_bullish_score(df)
        
        # Score must be bounded
        assert 0 <= score <= 10, f"{ticker} score out of bounds: {score}"
        
        # Breakdown must have expected components
        expected_components = ['trend', 'ma_stack', 'macd', 'rsi', 'obv', 'adx']
        for comp in expected_components:
            assert comp in breakdown, f"{ticker} missing breakdown: {comp}"
            assert 1 <= breakdown[comp] <= 10, f"{ticker} {comp} out of bounds"
        
        print(f"{ticker}: Score={score:.1f}, RSI={breakdown.get('rsi', 'N/A')}")
    
    @pytest.mark.parametrize("ticker", CACHED_TICKERS[:10] if CACHED_TICKERS else ["NVDA"])
    def test_calculate_matrix_real(self, ticker):
        """Calculate flag matrix for real tickers."""
        raw_df = load_cached_data(ticker)
        if raw_df is None:
            pytest.skip(f"No data for {ticker}")
        
        df = add_standard_indicators(raw_df.copy())
        matrix = calculate_matrix(df)
        
        # Must be a dict with expected keys
        assert isinstance(matrix, dict)
        assert '_price' in matrix
        assert '_rsi' in matrix
        
        # Price should be reasonable
        price = matrix.get('_price', 0)
        assert 0.01 < price < 100000, f"{ticker} price unreasonable: {price}"
        
        # RSI should be bounded
        rsi = matrix.get('_rsi', 50)
        assert 0 <= rsi <= 100, f"{ticker} RSI out of bounds: {rsi}"


@SKIP_NO_CACHE
class TestRealDivergenceDetection:
    """Test divergence detection with real data."""
    
    @pytest.mark.parametrize("ticker", CACHED_TICKERS[:20] if CACHED_TICKERS else ["NVDA"])
    def test_detect_divergence_real(self, ticker):
        """Detect divergences in real tickers."""
        raw_df = load_cached_data(ticker)
        if raw_df is None:
            pytest.skip(f"No data for {ticker}")
        
        df = add_standard_indicators(raw_df.copy())
        
        # Should not crash on real data
        result = detect_combined_divergence(df, lookback=14)
        
        # Result should have expected structure
        assert hasattr(result, 'type')
        assert hasattr(result, 'strength')
        
        if result.type != DivergenceType.NONE:
            print(f"{ticker}: {result.type.value} divergence, strength={result.strength}")


@SKIP_NO_CACHE
class TestRealTriggerEvaluation:
    """Test trigger evaluation with real data."""
    
    @pytest.mark.parametrize("ticker", CACHED_TICKERS[:10] if CACHED_TICKERS else ["NVDA"])
    def test_evaluate_triggers_real(self, ticker):
        """Evaluate triggers for real tickers."""
        raw_df = load_cached_data(ticker)
        if raw_df is None:
            pytest.skip(f"No data for {ticker}")
        
        df = add_standard_indicators(raw_df.copy())
        
        # Get matrix and score
        matrix = calculate_matrix(df)
        score, _ = calculate_bullish_score(df)
        matrix['score'] = score
        
        # Evaluate watchlist triggers
        results = evaluate_ticker(
            ticker=ticker,
            flags=matrix,
            list_type='watchlist',
            cooldowns={},
            actioned={},
        )
        
        assert isinstance(results, list)
        
        for r in results:
            assert r.ticker == ticker
            assert r.action in ['BUY', 'SELL', 'ALERT']
            print(f"{ticker}: {r.signal} -> {r.action}")


@SKIP_NO_CACHE
class TestKnownTickerExpectations:
    """Test specific expectations for well-known tickers."""
    
    def test_nvda_has_valid_indicators(self):
        """NVDA should have all indicators calculated."""
        raw_df = load_cached_data("NVDA")
        if raw_df is None:
            pytest.skip("NVDA data not available")
        
        df = add_standard_indicators(raw_df.copy())
        assert len(df) >= 200
        
        # NVDA should have meaningful price (adjust range as needed)
        last_close = df['close'].iloc[-1]
        assert 50 < last_close < 500, f"NVDA price unexpected: {last_close}"
        
        # Indicators should be calculated
        last_row = df.iloc[-1]
        assert 0 < last_row['RSI'] < 100
        assert last_row['SMA_200'] > 0
        
        print(f"NVDA: Price=${last_close:.2f}, RSI={last_row['RSI']:.1f}")
    
    def test_aapl_has_valid_indicators(self):
        """AAPL should have all indicators calculated."""
        raw_df = load_cached_data("AAPL")
        if raw_df is None:
            pytest.skip("AAPL data not available")
        
        df = add_standard_indicators(raw_df.copy())
        
        # AAPL should have meaningful price  
        last_close = df['close'].iloc[-1]
        assert 100 < last_close < 400, f"AAPL price unexpected: {last_close}"
        
        print(f"AAPL: Price=${last_close:.2f}")
    
    def test_tsla_has_valid_indicators(self):
        """TSLA should have all indicators calculated."""
        raw_df = load_cached_data("TSLA")
        if raw_df is None:
            pytest.skip("TSLA data not available")
        
        df = add_standard_indicators(raw_df.copy())
        
        # TSLA should have meaningful price
        last_close = df['close'].iloc[-1]
        assert 100 < last_close < 1000, f"TSLA price unexpected: {last_close}"
        
        print(f"TSLA: Price=${last_close:.2f}")


@SKIP_NO_CACHE
class TestBatchProcessing:
    """Test processing many tickers to ensure robustness."""
    
    def test_process_all_cached_tickers(self):
        """Process all cached tickers without crashes."""
        success = 0
        failed = []
        
        for ticker in CACHED_TICKERS:
            try:
                raw_df = load_cached_data(ticker)
                if raw_df is None or len(raw_df) < 50:
                    continue
                
                df = add_standard_indicators(raw_df.copy())
                score, _ = calculate_bullish_score(df)
                matrix = calculate_matrix(df)
                
                if 0 <= score <= 10:
                    success += 1
                else:
                    failed.append((ticker, f"Score out of bounds: {score}"))
            except Exception as e:
                failed.append((ticker, str(e)))
        
        print(f"\nProcessed {success}/{len(CACHED_TICKERS)} tickers successfully")
        
        # Allow some failures due to data quality issues
        failure_rate = len(failed) / max(len(CACHED_TICKERS), 1)
        assert failure_rate < 0.1, f"Too many failures ({len(failed)}): {failed[:5]}"
    
    def test_collect_signal_statistics(self):
        """Collect statistics on signals across all tickers."""
        total_buy = 0
        total_sell = 0
        scores = []
        ticker_signals = []
        
        for ticker in CACHED_TICKERS[:50]:  # First 50 tickers
            try:
                raw_df = load_cached_data(ticker)
                if raw_df is None or len(raw_df) < 50:
                    continue
                
                df = add_standard_indicators(raw_df.copy())
                score, _ = calculate_bullish_score(df)
                scores.append((ticker, score))
                
                matrix = calculate_matrix(df)
                matrix['score'] = score
                
                results = evaluate_ticker(
                    ticker=ticker,
                    flags=matrix,
                    list_type='watchlist',
                    cooldowns={},
                    actioned={},
                )
                
                for r in results:
                    ticker_signals.append((ticker, r.signal, r.action))
                    if r.action == 'BUY':
                        total_buy += 1
                    elif r.action == 'SELL':
                        total_sell += 1
            except Exception:
                continue
        
        if scores:
            scores_only = [s[1] for s in scores]
            avg_score = sum(scores_only) / len(scores_only)
            
            # Sort by score
            top_5 = sorted(scores, key=lambda x: x[1], reverse=True)[:5]
            bottom_5 = sorted(scores, key=lambda x: x[1])[:5]
            
            print(f"\n📊 Signal Statistics (n={len(scores)}):")
            print(f"  Average Score: {avg_score:.1f}")
            print(f"  Score Range: {min(scores_only):.1f} - {max(scores_only):.1f}")
            print(f"\n  Top 5 Bullish: {', '.join([f'{t}({s:.1f})' for t, s in top_5])}")
            print(f"  Bottom 5: {', '.join([f'{t}({s:.1f})' for t, s in bottom_5])}")
            print(f"\n  Buy Signals: {total_buy}")
            print(f"  Sell Signals: {total_sell}")
            
            if ticker_signals:
                print(f"\n  Sample Signals:")
                for t, sig, act in ticker_signals[:5]:
                    print(f"    {t}: {sig} -> {act}")

