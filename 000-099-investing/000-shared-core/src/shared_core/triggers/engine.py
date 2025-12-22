"""
Config-driven trigger evaluation engine.

Evaluates triggers defined in JSON config against market data.
"""

import logging
import pandas as pd
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TriggerEngine:
    """
    Config-driven trigger evaluation engine.
    
    Evaluates triggers defined in watchlist.json against market data.
    Supports various trigger types: score-based, price-based, MA crosses, etc.
    
    Attributes:
        default_triggers: List of default triggers applied to all tickers
    """

    def __init__(self, default_triggers: Optional[List[Dict]] = None):
        """
        Initialize with optional default triggers.
        
        Args:
            default_triggers: Default triggers that apply to all tickers
        """
        self.default_triggers = default_triggers or []

    def evaluate(
        self,
        symbol: str,
        df: pd.DataFrame,
        score: float,
        ticker_triggers: Optional[List[Dict]] = None,
        matrix: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate triggers for a single symbol.
        
        Args:
            symbol: Ticker symbol
            df: DataFrame with OHLCV and indicators
            score: Bullish score (0-10)
            ticker_triggers: Custom triggers for this ticker (overrides defaults)
            matrix: Optional matrix flags for conditional triggers
            
        Returns:
            List of triggered dicts with: symbol, action, type, message, trigger_key
        """
        if df is None or len(df) < 2:
            return []

        triggers_to_eval = ticker_triggers if ticker_triggers else self.default_triggers
        if not triggers_to_eval:
            return []

        results = []
        curr = df.iloc[-1]
        prev = df.iloc[-2]

        for trigger in triggers_to_eval:
            evaluated = self._evaluate_trigger(symbol, trigger, curr, prev, df, score, matrix=matrix)
            if evaluated:
                results.append(evaluated)

        return results

    def _trigger_key(self, symbol: str, trigger: Dict[str, Any]) -> str:
        """Generate stable identifier for dedupe/suppression."""
        t_type = trigger.get("type", "unknown")
        action = trigger.get("action", "WATCH")

        parts: List[str] = [symbol, t_type, action]

        if t_type in ("score_above", "score_below", "price_above", "price_below"):
            parts.append(str(trigger.get("value")))
        elif t_type in ("price_crosses_above_ma", "price_crosses_below_ma", "price_above_ma", "price_below_ma"):
            parts.append(str(trigger.get("ma")))
        elif t_type == "ma_cross":
            parts.extend([str(trigger.get("fast")), str(trigger.get("slow")), str(trigger.get("direction", "bullish"))])
        elif t_type in ("stoch_oversold", "stoch_overbought", "rsi_oversold", "rsi_overbought"):
            parts.append(str(trigger.get("threshold")))
        elif t_type == "volume_spike":
            parts.append(str(trigger.get("multiplier")))
        elif t_type == "price_within_pct_of_ma":
            parts.extend([str(trigger.get("ma")), str(trigger.get("pct"))])

        # Sanitize for file/email safety
        safe = []
        for p in parts:
            p = (p or "").strip().replace(" ", "").replace("/", "_").replace(":", "_").replace("__", "_")
            if p:
                safe.append(p)
        return "_".join(safe)

    def _evaluate_trigger(
        self,
        symbol: str,
        trigger: Dict,
        curr: pd.Series,
        prev: pd.Series,
        df: pd.DataFrame,
        score: float,
        matrix: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Evaluate a single trigger configuration."""
        t_type = trigger.get('type')
        action = trigger.get('action', 'WATCH')
        note = trigger.get('note', '')
        cooldown_days = int(trigger.get("cooldown_days", 0) or 0)

        # Optional matrix gate
        requires_matrix = trigger.get("requires_matrix") or {}
        if requires_matrix:
            if not matrix:
                return None
            for k, expected in requires_matrix.items():
                if matrix.get(k) != expected:
                    return None

        triggered = False
        detail = ""

        try:
            if t_type == 'score_above':
                value = trigger['value']
                if score >= value:
                    triggered = True
                    detail = f"Score {score} >= {value}"

            elif t_type == 'score_below':
                value = trigger['value']
                if score <= value:
                    triggered = True
                    detail = f"Score {score} <= {value}"

            elif t_type == 'price_above':
                value = trigger['value']
                if curr['close'] > value:
                    triggered = True
                    detail = f"Price ${round(curr['close'], 2)} > ${value}"

            elif t_type == 'price_below':
                value = trigger['value']
                if curr['close'] < value:
                    triggered = True
                    detail = f"Price ${round(curr['close'], 2)} < ${value}"

            elif t_type == 'price_crosses_above_ma':
                ma = trigger['ma']
                if ma in curr.index and ma in prev.index:
                    if prev['close'] <= prev[ma] and curr['close'] > curr[ma]:
                        triggered = True
                        detail = f"Price crossed above {ma}"

            elif t_type == 'price_crosses_below_ma':
                ma = trigger['ma']
                if ma in curr.index and ma in prev.index:
                    if prev['close'] >= prev[ma] and curr['close'] < curr[ma]:
                        triggered = True
                        detail = f"Price crossed below {ma}"

            elif t_type == 'price_above_ma':
                ma = trigger['ma']
                if ma in curr.index:
                    if curr['close'] > curr[ma]:
                        triggered = True
                        detail = f"Price > {ma}"

            elif t_type == 'price_below_ma':
                ma = trigger['ma']
                if ma in curr.index:
                    if curr['close'] < curr[ma]:
                        triggered = True
                        detail = f"Price < {ma}"

            elif t_type == 'ma_cross':
                fast = trigger['fast']
                slow = trigger['slow']
                direction = trigger.get('direction', 'bullish')

                if all(col in curr.index for col in [fast, slow]):
                    if direction == 'bullish':
                        if prev[fast] <= prev[slow] and curr[fast] > curr[slow]:
                            triggered = True
                            detail = f"Golden Cross ({fast} > {slow})"
                    else:
                        if prev[fast] >= prev[slow] and curr[fast] < curr[slow]:
                            triggered = True
                            detail = f"Death Cross ({fast} < {slow})"

            elif t_type == 'stoch_oversold':
                threshold = trigger.get('threshold', 20)
                if 'STOCH_K' in curr.index:
                    if curr['STOCH_K'] < threshold and score >= 5:
                        triggered = True
                        detail = f"Stoch_K {round(curr['STOCH_K'], 1)} < {threshold}"

            elif t_type == 'stoch_overbought':
                threshold = trigger.get('threshold', 80)
                if 'STOCH_K' in curr.index:
                    if curr['STOCH_K'] > threshold:
                        triggered = True
                        detail = f"Stoch_K {round(curr['STOCH_K'], 1)} > {threshold}"

            elif t_type == 'rsi_oversold':
                threshold = trigger.get('threshold', 30)
                if 'RSI' in curr.index:
                    if curr['RSI'] < threshold:
                        triggered = True
                        detail = f"RSI {round(curr['RSI'], 1)} < {threshold}"

            elif t_type == 'rsi_overbought':
                threshold = trigger.get('threshold', 70)
                if 'RSI' in curr.index:
                    if curr['RSI'] > threshold:
                        triggered = True
                        detail = f"RSI {round(curr['RSI'], 1)} > {threshold}"

            elif t_type == 'volume_spike':
                multiplier = trigger.get('multiplier', 2.0)
                vol_ma = df['volume'].rolling(50).mean().iloc[-1]
                if vol_ma > 0:
                    vol_ratio = curr['volume'] / vol_ma
                    if vol_ratio >= multiplier:
                        triggered = True
                        detail = f"Volume {round(vol_ratio, 1)}x avg"

            elif t_type == 'price_within_pct_of_ma':
                ma = trigger['ma']
                pct = trigger.get('pct', 2)
                if ma in curr.index and curr[ma] > 0:
                    distance = abs(curr['close'] - curr[ma]) / curr[ma] * 100
                    if distance <= pct:
                        triggered = True
                        detail = f"Price within {round(distance, 1)}% of {ma}"

            else:
                logger.warning(f"Unknown trigger type: {t_type}")
                return None

        except Exception as e:
            logger.warning(f"Error evaluating trigger {t_type}: {e}")
            return None

        if triggered:
            message = f"{action}: {note} ({detail})" if note else f"{action}: {detail}"
            return {
                "symbol": symbol,
                "action": action,
                "type": t_type,
                "note": note,
                "detail": detail,
                "message": message,
                "trigger_key": self._trigger_key(symbol, trigger),
                "cooldown_days": cooldown_days,
            }

        return None

