"""
Backtest Engine — Core backtesting logic for reversal signals.

Scans historical data, detects signals, and calculates forward returns.
"""

import pandas as pd
import numpy as np
from datetime import date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .models import (
    SignalEvent, SignalType, ConvictionLevel,
    BacktestResult, HorizonMetrics, HORIZON_DAYS
)
from ..divergence.divergence import detect_combined_divergence
from ..scoring.models import DivergenceType


@dataclass
class ScoringConfig:
    """Configuration for signal scoring thresholds."""
    # Score thresholds for conviction levels
    high_score_min: float = 8.0
    medium_score_min: float = 7.0
    low_score_min: float = 6.0

    # Volume requirements
    high_volume_min: float = 1.2
    medium_volume_min: float = 1.0

    # ADX requirements
    high_adx_max: float = 35.0


class BacktestEngine:
    """
    Engine for backtesting reversal and oversold signals.

    Workflow:
    1. Load historical data for tickers
    2. Calculate indicators for each date (rolling window)
    3. Detect signals based on scoring logic
    4. Calculate forward returns at each horizon
    5. Aggregate metrics
    """

    def __init__(
        self,
        scoring_config: Optional[ScoringConfig] = None,
        verbose: bool = False
    ):
        self.config = scoring_config or ScoringConfig()
        self.verbose = verbose

    def run_backtest(
        self,
        ticker_data: Dict[str, pd.DataFrame],
        signal_type: SignalType = SignalType.UPSIDE_REVERSAL,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        conviction_filter: Optional[ConvictionLevel] = None,
    ) -> BacktestResult:
        """
        Run backtest on provided ticker data.

        Args:
            ticker_data: Dict mapping ticker symbols to DataFrames with OHLCV + indicators
            signal_type: Type of signal to detect
            start_date: Start of backtest period (default: earliest available)
            end_date: End of backtest period (default: 6 months ago for forward data)
            conviction_filter: Only include signals at this conviction level or higher

        Returns:
            BacktestResult with all signals and metrics
        """
        all_signals: List[SignalEvent] = []

        for ticker, df in ticker_data.items():
            if df is None or len(df) < 250:  # Need ~1 year minimum
                if self.verbose:
                    print(f"  Skipping {ticker}: insufficient data ({len(df) if df is not None else 0} rows)")
                continue

            signals = self._scan_ticker(
                ticker, df, signal_type, start_date, end_date
            )

            # Filter by conviction if specified
            if conviction_filter:
                conviction_order = [ConvictionLevel.HIGH, ConvictionLevel.MEDIUM, ConvictionLevel.LOW]
                min_idx = conviction_order.index(conviction_filter)
                signals = [s for s in signals if conviction_order.index(s.conviction) <= min_idx]

            all_signals.extend(signals)

            if self.verbose:
                print(f"  {ticker}: {len(signals)} signals detected")

        # Determine actual date range
        if all_signals:
            actual_start = min(s.signal_date for s in all_signals)
            actual_end = max(s.signal_date for s in all_signals)
        else:
            actual_start = start_date or date.today()
            actual_end = end_date or date.today()

        # Calculate aggregate metrics
        result = BacktestResult(
            tickers=list(ticker_data.keys()),
            start_date=actual_start,
            end_date=actual_end,
            signal_type=signal_type,
            conviction_filter=conviction_filter,
            signals=all_signals,
        )

        # Calculate metrics for each horizon
        result.metrics_2w = self._calculate_horizon_metrics(all_signals, '2w')
        result.metrics_2m = self._calculate_horizon_metrics(all_signals, '2m')
        result.metrics_6m = self._calculate_horizon_metrics(all_signals, '6m')

        # Calculate metrics by conviction level
        for conv in [ConvictionLevel.HIGH, ConvictionLevel.MEDIUM, ConvictionLevel.LOW]:
            conv_signals = [s for s in all_signals if s.conviction == conv]
            if conv_signals:
                result.metrics_by_conviction[conv] = {
                    '2w': self._calculate_horizon_metrics(conv_signals, '2w'),
                    '2m': self._calculate_horizon_metrics(conv_signals, '2m'),
                    '6m': self._calculate_horizon_metrics(conv_signals, '6m'),
                }

        return result

    def _scan_ticker(
        self,
        ticker: str,
        df: pd.DataFrame,
        signal_type: SignalType,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> List[SignalEvent]:
        """
        Scan a single ticker's data for signals.

        For each date, we calculate the score using only data available
        up to that date (no look-ahead bias).
        """
        signals = []

        # Ensure datetime index
        if 'datetime' in df.columns:
            df = df.set_index('datetime')
        df.index = pd.to_datetime(df.index)

        # Determine scan range
        # Need at least 200 days of history for indicators
        min_history = 200
        # Need at least 6 months of forward data for returns
        max_forward = HORIZON_DAYS['6m']

        scan_start_idx = min_history
        scan_end_idx = len(df) - max_forward

        if scan_end_idx <= scan_start_idx:
            return signals

        # Apply date filters
        for i in range(scan_start_idx, scan_end_idx):
            current_date = df.index[i].date()

            if start_date and current_date < start_date:
                continue
            if end_date and current_date > end_date:
                continue

            # Get data up to this point (no look-ahead)
            historical_df = df.iloc[:i+1].copy()

            # Calculate score for this date
            score_result = self._calculate_score(historical_df, signal_type)

            if score_result is None:
                continue

            final_score, conviction, volume_ratio, adx_value = score_result

            # Only record if meets minimum threshold
            if final_score < self.config.low_score_min:
                continue

            # Get price at signal
            price_at_signal = float(df.iloc[i]['close'])

            # Calculate forward returns
            forward_returns = self._calculate_forward_returns(
                df, i, price_at_signal
            )

            signal = SignalEvent(
                ticker=ticker,
                signal_date=current_date,
                signal_type=signal_type,
                conviction=conviction,
                score=final_score,
                volume_ratio=volume_ratio,
                adx_value=adx_value,
                price_at_signal=price_at_signal,
                **forward_returns
            )

            signals.append(signal)

        return signals

    def _calculate_score(
        self,
        df: pd.DataFrame,
        signal_type: SignalType,
    ) -> Optional[Tuple[float, ConvictionLevel, float, float]]:
        """
        Calculate signal score for the current date.

        Returns: (final_score, conviction, volume_ratio, adx_value) or None
        """
        if len(df) < 50:
            return None

        current = df.iloc[-1]
        prev = df.iloc[-2]

        # Get required values
        rsi = current.get('RSI')
        macd = current.get('MACD')
        macd_signal = current.get('MACD_SIGNAL') or current.get('MACD_Signal')
        macd_hist = current.get('MACD_HIST') or current.get('MACD_Hist')
        prev_macd = prev.get('MACD')
        prev_macd_signal = prev.get('MACD_SIGNAL') or prev.get('MACD_Signal')
        prev_macd_hist = prev.get('MACD_HIST') or prev.get('MACD_Hist')
        sma50 = current.get('SMA_50')
        prev_sma50 = prev.get('SMA_50')
        sma200 = current.get('SMA_200')
        prev_sma200 = prev.get('SMA_200')
        adx = current.get('ADX', 25)
        close = current['close']
        prev_close = prev['close']

        # Volume ratio (with NaN handling)
        if 'volume' in df.columns:
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
            if pd.isna(current_volume) or pd.isna(avg_volume) or avg_volume == 0:
                volume_ratio = 1.0
            else:
                volume_ratio = current_volume / avg_volume
        else:
            volume_ratio = 1.0

        # Score components based on signal type
        if signal_type == SignalType.UPSIDE_REVERSAL:
            components = self._score_upside_components(
                df, rsi, macd, macd_signal, macd_hist,
                prev_macd, prev_macd_signal, prev_macd_hist,
                close, sma50, prev_close, prev_sma50,
                sma200, prev_sma200, volume_ratio
            )
        else:
            components = self._score_downside_components(
                df, rsi, macd, macd_signal, macd_hist,
                prev_macd, prev_macd_signal, prev_macd_hist,
                close, sma50, prev_close, prev_sma50,
                sma200, prev_sma200, volume_ratio
            )

        # Calculate raw score
        weights = {
            'rsi': 0.15,
            'macd_crossover': 0.15,
            'macd_hist': 0.10,
            'price_sma50': 0.15,
            'price_sma200': 0.20,
            'volume': 0.15,
            'divergence': 0.10,
        }

        raw_score = sum(components.get(k, 1.0) * weights[k] for k in weights)

        # Apply multipliers
        volume_mult = self._get_volume_multiplier(volume_ratio)
        adx_mult = self._get_adx_multiplier(adx if not pd.isna(adx) else 25)

        final_score = min(10.0, raw_score * volume_mult * adx_mult)

        # Determine conviction
        conviction = self._classify_conviction(final_score, volume_ratio, adx if not pd.isna(adx) else 25)

        return (round(final_score, 2), conviction, round(volume_ratio, 2), round(adx if not pd.isna(adx) else 25, 1))

    def _score_upside_components(
        self, df: pd.DataFrame, rsi, macd, macd_signal, macd_hist,
        prev_macd, prev_macd_signal, prev_macd_hist,
        close, sma50, prev_close, prev_sma50,
        sma200, prev_sma200, volume_ratio
    ) -> Dict[str, float]:
        """Score components for upside reversal."""
        components = {}

        # RSI (tightened)
        if pd.isna(rsi):
            components['rsi'] = 1.0
        elif rsi < 25:
            components['rsi'] = 10.0
        elif rsi < 30:
            components['rsi'] = 7.0
        elif rsi < 35:
            components['rsi'] = 4.0
        else:
            components['rsi'] = 1.0

        # MACD Crossover
        if pd.isna(macd) or pd.isna(macd_signal):
            components['macd_crossover'] = 1.0
        elif not pd.isna(prev_macd) and not pd.isna(prev_macd_signal):
            if prev_macd < prev_macd_signal and macd > macd_signal:
                components['macd_crossover'] = 10.0
            elif macd > macd_signal:
                components['macd_crossover'] = 6.0
            else:
                components['macd_crossover'] = 1.0
        elif macd > macd_signal:
            components['macd_crossover'] = 6.0
        else:
            components['macd_crossover'] = 1.0

        # MACD Histogram
        if pd.isna(macd_hist):
            components['macd_hist'] = 1.0
        elif not pd.isna(prev_macd_hist) and prev_macd_hist < 0 and macd_hist > 0:
            components['macd_hist'] = 10.0
        elif macd_hist > 0:
            components['macd_hist'] = 6.0
        elif not pd.isna(prev_macd_hist) and macd_hist > prev_macd_hist:
            components['macd_hist'] = 5.0
        else:
            components['macd_hist'] = 1.0

        # Price vs SMA50
        if pd.isna(sma50) or sma50 == 0:
            components['price_sma50'] = 1.0
        else:
            pct_diff = ((close - sma50) / sma50) * 100
            crossed_above = (
                not pd.isna(prev_close) and not pd.isna(prev_sma50)
                and prev_close < prev_sma50 and close > sma50
            )
            if crossed_above:
                components['price_sma50'] = 10.0
            elif close > sma50:
                components['price_sma50'] = 7.0
            elif pct_diff >= -3:
                components['price_sma50'] = 4.0
            else:
                components['price_sma50'] = 1.0

        # Price vs SMA200
        if pd.isna(sma200) or sma200 == 0:
            components['price_sma200'] = 1.0
        else:
            pct_diff = ((close - sma200) / sma200) * 100
            crossed_above = (
                not pd.isna(prev_close) and not pd.isna(prev_sma200)
                and prev_close < prev_sma200 and close > sma200
            )
            if crossed_above:
                components['price_sma200'] = 10.0
            elif close > sma200:
                components['price_sma200'] = 7.0
            elif pct_diff >= -5:
                components['price_sma200'] = 4.0
            else:
                components['price_sma200'] = 1.0

        # Volume
        if volume_ratio >= 2.0:
            components['volume'] = 10.0
        elif volume_ratio >= 1.5:
            components['volume'] = 7.0
        elif volume_ratio >= 1.2:
            components['volume'] = 5.0
        elif volume_ratio >= 1.0:
            components['volume'] = 3.0
        else:
            components['volume'] = 1.0

        # Divergence detection (using combined RSI + OBV)
        try:
            divergence = detect_combined_divergence(df, lookback=20)
            if divergence.type == DivergenceType.BULLISH:
                # Bullish divergence is good for upside reversal
                components['divergence'] = min(10.0, 7.0 + (divergence.strength / 10.0))
            else:
                components['divergence'] = 1.0
        except Exception:
            components['divergence'] = 1.0

        return components

    def _score_downside_components(
        self, df: pd.DataFrame, rsi, macd, macd_signal, macd_hist,
        prev_macd, prev_macd_signal, prev_macd_hist,
        close, sma50, prev_close, prev_sma50,
        sma200, prev_sma200, volume_ratio
    ) -> Dict[str, float]:
        """Score components for downside reversal."""
        components = {}

        # RSI (overbought)
        if pd.isna(rsi):
            components['rsi'] = 1.0
        elif rsi > 75:
            components['rsi'] = 10.0
        elif rsi > 70:
            components['rsi'] = 7.0
        elif rsi > 65:
            components['rsi'] = 4.0
        else:
            components['rsi'] = 1.0

        # MACD Crossover (bearish)
        if pd.isna(macd) or pd.isna(macd_signal):
            components['macd_crossover'] = 1.0
        elif not pd.isna(prev_macd) and not pd.isna(prev_macd_signal):
            if prev_macd > prev_macd_signal and macd < macd_signal:
                components['macd_crossover'] = 10.0
            elif macd < macd_signal:
                components['macd_crossover'] = 6.0
            else:
                components['macd_crossover'] = 1.0
        elif macd < macd_signal:
            components['macd_crossover'] = 6.0
        else:
            components['macd_crossover'] = 1.0

        # MACD Histogram (bearish)
        if pd.isna(macd_hist):
            components['macd_hist'] = 1.0
        elif not pd.isna(prev_macd_hist) and prev_macd_hist > 0 and macd_hist < 0:
            components['macd_hist'] = 10.0
        elif macd_hist < 0:
            components['macd_hist'] = 6.0
        else:
            components['macd_hist'] = 1.0

        # Price vs SMA50 (extended above)
        if pd.isna(sma50) or sma50 == 0:
            components['price_sma50'] = 1.0
        else:
            pct_diff = ((close - sma50) / sma50) * 100
            crossed_below = (
                not pd.isna(prev_close) and not pd.isna(prev_sma50)
                and prev_close > prev_sma50 and close < sma50
            )
            if crossed_below:
                components['price_sma50'] = 10.0
            elif pct_diff > 15:
                components['price_sma50'] = 7.0
            elif pct_diff > 5:
                components['price_sma50'] = 4.0
            else:
                components['price_sma50'] = 1.0

        # Price vs SMA200 (extended above)
        if pd.isna(sma200) or sma200 == 0:
            components['price_sma200'] = 1.0
        else:
            pct_diff = ((close - sma200) / sma200) * 100
            crossed_below = (
                not pd.isna(prev_close) and not pd.isna(prev_sma200)
                and prev_close > prev_sma200 and close < sma200
            )
            if crossed_below:
                components['price_sma200'] = 10.0
            elif pct_diff > 20:
                components['price_sma200'] = 7.0
            elif pct_diff > 10:
                components['price_sma200'] = 4.0
            else:
                components['price_sma200'] = 1.0

        # Volume
        if volume_ratio >= 2.0:
            components['volume'] = 10.0
        elif volume_ratio >= 1.5:
            components['volume'] = 7.0
        elif volume_ratio >= 1.2:
            components['volume'] = 5.0
        elif volume_ratio >= 1.0:
            components['volume'] = 3.0
        else:
            components['volume'] = 1.0

        # Divergence detection (using combined RSI + OBV)
        try:
            divergence = detect_combined_divergence(df, lookback=20)
            if divergence.type == DivergenceType.BEARISH:
                # Bearish divergence is good for downside reversal
                components['divergence'] = min(10.0, 7.0 + (divergence.strength / 10.0))
            else:
                components['divergence'] = 1.0
        except Exception:
            components['divergence'] = 1.0

        return components

    def _get_volume_multiplier(self, volume_ratio: float) -> float:
        """Harsh volume gate."""
        if volume_ratio >= 2.0:
            return 1.2
        elif volume_ratio >= 1.5:
            return 1.1
        elif volume_ratio >= 1.0:
            return 1.0
        elif volume_ratio >= 0.8:
            return 0.7
        else:
            return 0.5

    def _get_adx_multiplier(self, adx: float) -> float:
        """Harsh ADX penalty."""
        if adx < 20:
            return 1.15
        elif adx <= 30:
            return 1.0
        elif adx <= 40:
            return 0.7
        else:
            return 0.5

    def _classify_conviction(
        self, final_score: float, volume_ratio: float, adx: float
    ) -> ConvictionLevel:
        """Classify conviction level."""
        if final_score >= 8.0 and volume_ratio >= 1.2 and adx < 35:
            return ConvictionLevel.HIGH
        elif final_score >= 7.0 and volume_ratio >= 1.0:
            return ConvictionLevel.MEDIUM
        elif final_score >= 6.0:
            return ConvictionLevel.LOW
        return ConvictionLevel.NONE

    def _calculate_forward_returns(
        self,
        df: pd.DataFrame,
        signal_idx: int,
        price_at_signal: float,
    ) -> Dict[str, Optional[float]]:
        """
        Calculate forward returns at each horizon.

        Returns dict with return_2w, return_2m, return_6m, and max gain/loss.
        """
        result = {}

        for horizon, days in HORIZON_DAYS.items():
            end_idx = signal_idx + days

            if end_idx >= len(df):
                result[f'return_{horizon}'] = None
                result[f'max_gain_{horizon}'] = None
                result[f'max_loss_{horizon}'] = None
                continue

            # Get forward price window
            forward_window = df.iloc[signal_idx:end_idx + 1]
            end_price = float(forward_window.iloc[-1]['close'])

            # Calculate return
            pct_return = ((end_price - price_at_signal) / price_at_signal) * 100
            result[f'return_{horizon}'] = round(pct_return, 2)

            # Calculate max gain and loss within window
            high_prices = forward_window['high'].values
            low_prices = forward_window['low'].values

            max_price = float(high_prices.max())
            min_price = float(low_prices.min())

            max_gain = ((max_price - price_at_signal) / price_at_signal) * 100
            max_loss = ((min_price - price_at_signal) / price_at_signal) * 100

            result[f'max_gain_{horizon}'] = round(max_gain, 2)
            result[f'max_loss_{horizon}'] = round(max_loss, 2)

        return result

    def _calculate_horizon_metrics(
        self,
        signals: List[SignalEvent],
        horizon: str,
    ) -> HorizonMetrics:
        """Calculate aggregate metrics for a specific horizon."""
        return_attr = f'return_{horizon}'
        max_gain_attr = f'max_gain_{horizon}'
        max_loss_attr = f'max_loss_{horizon}'

        # Filter signals with valid return data
        valid_signals = [
            s for s in signals
            if getattr(s, return_attr) is not None
        ]

        if not valid_signals:
            return HorizonMetrics(
                horizon=horizon,
                total_signals=len(signals),
                signals_with_data=0,
                winners=0,
                losers=0,
                win_rate=0.0,
                avg_return=0.0,
                median_return=0.0,
                best_return=0.0,
                worst_return=0.0,
                avg_max_gain=0.0,
                avg_max_loss=0.0,
                expectancy=0.0,
            )

        returns = [getattr(s, return_attr) for s in valid_signals]
        max_gains = [getattr(s, max_gain_attr) or 0 for s in valid_signals]
        max_losses = [getattr(s, max_loss_attr) or 0 for s in valid_signals]

        winners = [r for r in returns if r > 0]
        losers = [r for r in returns if r <= 0]

        win_count = len(winners)
        loss_count = len(losers)
        total = len(returns)

        win_rate = (win_count / total * 100) if total > 0 else 0

        avg_win = np.mean(winners) if winners else 0
        avg_loss = abs(np.mean(losers)) if losers else 0

        # Expectancy = (Win% × Avg Win) - (Loss% × Avg Loss)
        expectancy = (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * avg_loss)

        return HorizonMetrics(
            horizon=horizon,
            total_signals=len(signals),
            signals_with_data=len(valid_signals),
            winners=win_count,
            losers=loss_count,
            win_rate=round(win_rate, 1),
            avg_return=round(np.mean(returns), 2),
            median_return=round(np.median(returns), 2),
            best_return=round(max(returns), 2),
            worst_return=round(min(returns), 2),
            avg_max_gain=round(np.mean(max_gains), 2),
            avg_max_loss=round(np.mean(max_losses), 2),
            expectancy=round(expectancy, 2),
        )
