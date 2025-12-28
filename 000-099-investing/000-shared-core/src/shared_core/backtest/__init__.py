"""
Backtesting module for reversal and oversold signals.

Provides tools to test signal quality against historical data.
"""

from .engine import BacktestEngine
from .models import BacktestResult, SignalEvent, HorizonMetrics
from .report import generate_backtest_report

__all__ = [
    'BacktestEngine',
    'BacktestResult',
    'SignalEvent',
    'HorizonMetrics',
    'generate_backtest_report',
]
