# Technical Indicators — Data & Derivation Reference

This document describes the raw data from the Twelve Data API and how each technical indicator is derived. Use this to understand the data foundation and suggest additional indicators.

---

## Raw Data from API

### Endpoint
```
GET https://api.twelvedata.com/time_series
```

### Parameters
| Parameter | Value | Description |
|-----------|-------|-------------|
| `symbol` | e.g., "AAPL" | Ticker symbol |
| `interval` | "1day" | Daily candles |
| `outputsize` | 300 | ~14 months of trading days |

### Response Schema
```json
{
  "meta": {
    "symbol": "AAPL",
    "interval": "1day",
    "currency": "USD",
    "exchange_timezone": "America/New_York",
    "exchange": "NASDAQ",
    "type": "Common Stock"
  },
  "values": [
    {
      "datetime": "2024-12-16",
      "open": "175.50",
      "high": "178.20",
      "low": "174.30",
      "close": "177.85",
      "volume": "52340000"
    },
    // ... 299 more rows (oldest to newest after sorting)
  ]
}
```

### Raw Data Fields

| Field | Type | Description |
|-------|------|-------------|
| `datetime` | string | Trading date (YYYY-MM-DD) |
| `open` | string→float | Opening price |
| `high` | string→float | Highest price of day |
| `low` | string→float | Lowest price of day |
| `close` | string→float | Closing price |
| `volume` | string→int | Shares traded |

---

## Derived Indicators

### 1. Simple Moving Averages (SMA)

**Formula:**
```
SMA(n) = (Close[0] + Close[1] + ... + Close[n-1]) / n
```

**Implementation:**
```python
def sma(data: pd.Series, period: int) -> pd.Series:
    return data.rolling(window=period).mean()
```

**Computed:**
| Column | Period | Use |
|--------|--------|-----|
| `SMA_5` | 5 days | Very short-term |
| `SMA_14` | 14 days | Short-term |
| `SMA_20` | 20 days | Short-term trend |
| `SMA_50` | 50 days | Medium-term trend |
| `SMA_200` | 200 days | Long-term trend |

---

### 2. Relative Strength Index (RSI)

**Formula:**
```
Delta = Close[t] - Close[t-1]
Gain = max(Delta, 0)
Loss = abs(min(Delta, 0))
AvgGain = SMA(Gain, 14)
AvgLoss = SMA(Loss, 14)
RS = AvgGain / AvgLoss
RSI = 100 - (100 / (1 + RS))
```

**Implementation:**
```python
def rsi(close_prices: pd.Series, period: int = 14) -> pd.Series:
    delta = close_prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))
```

**Output:** `RSI` — Range 0-100

---

### 3. MACD (Moving Average Convergence Divergence)

**Formula:**
```
EMA_fast = EMA(Close, 12)
EMA_slow = EMA(Close, 26)
MACD_Line = EMA_fast - EMA_slow
Signal_Line = EMA(MACD_Line, 9)
Histogram = MACD_Line - Signal_Line
```

**Implementation:**
```python
def macd(close: pd.Series, fast=12, slow=26, signal=9) -> tuple:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram
```

**Output:**
| Column | Description |
|--------|-------------|
| `MACD` | MACD Line |
| `MACD_SIGNAL` | Signal Line |
| `MACD_HIST` | Histogram (momentum) |

---

### 4. Stochastic Oscillator

**Formula:**
```
Lowest_Low = min(Low, 14)
Highest_High = max(High, 14)
%K = 100 * (Close - Lowest_Low) / (Highest_High - Lowest_Low)
%D = SMA(%K, 3)
```

**Implementation:**
```python
def stochastic(df: pd.DataFrame, k_period=14, d_period=3) -> tuple:
    low_min = df['low'].rolling(window=k_period).min()
    high_max = df['high'].rolling(window=k_period).max()
    k = 100 * ((df['close'] - low_min) / (high_max - low_min))
    d = k.rolling(window=d_period).mean()
    return k, d
```

**Output:**
| Column | Description |
|--------|-------------|
| `STOCH_K` | Fast stochastic (0-100) |
| `STOCH_D` | Slow stochastic (smoothed) |

---

### 5. Average Directional Index (ADX)

**Formula:**
```
+DM = High[t] - High[t-1] (if positive and > -DM, else 0)
-DM = Low[t-1] - Low[t] (if positive and > +DM, else 0)
TR = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
ATR = SMA(TR, 14)
+DI = 100 * SMA(+DM, 14) / ATR
-DI = 100 * SMA(-DM, 14) / ATR
DX = 100 * |+DI - -DI| / (+DI + -DI)
ADX = SMA(DX, 14)
```

**Implementation:**
```python
def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df['high'], df['low'], df['close']
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    return dx.rolling(window=period).mean()
```

**Output:** `ADX` — Trend strength (>25 = strong trend)

---

### 6. On-Balance Volume (OBV)

**Formula:**
```
If Close > PrevClose: OBV = PrevOBV + Volume
If Close < PrevClose: OBV = PrevOBV - Volume
If Close = PrevClose: OBV = PrevOBV
```

**Implementation:**
```python
def obv(df: pd.DataFrame) -> pd.Series:
    return (df['volume'] * np.where(df['close'].diff() > 0, 1, -1)).cumsum()
```

**Output:** `OBV` — Cumulative volume flow

---

### 7. Bollinger Bands

**Formula:**
```
Middle = SMA(Close, 20)
Upper = Middle + (2 * StdDev(Close, 20))
Lower = Middle - (2 * StdDev(Close, 20))
Width = (Upper - Lower) / Middle * 100
```

**Implementation:**
```python
def bollinger_bands(close: pd.Series, period=20, std_dev=2) -> tuple:
    middle = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    bandwidth = ((upper - lower) / middle) * 100
    return upper, middle, lower, bandwidth
```

**Output:**
| Column | Description |
|--------|-------------|
| `BB_UPPER` | Upper band |
| `BB_MIDDLE` | Middle band (SMA20) |
| `BB_LOWER` | Lower band |
| `BB_WIDTH` | Bandwidth percentage |

---

### 8. Average True Range (ATR)

**Formula:**
```
TR = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
ATR = SMA(TR, 14)
```

**Implementation:**
```python
def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df['high'], df['low'], df['close']
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()
```

**Output:** `ATR` — Average daily range in dollars

---

### 9. Williams %R

**Formula:**
```
Highest_High = max(High, 14)
Lowest_Low = min(Low, 14)
%R = -100 * (Highest_High - Close) / (Highest_High - Lowest_Low)
```

**Implementation:**
```python
def williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_max = df['high'].rolling(window=period).max()
    low_min = df['low'].rolling(window=period).min()
    return -100 * ((high_max - df['close']) / (high_max - low_min))
```

**Output:** `WILLIAMS_R` — Range -100 to 0 (< -80 = oversold, > -20 = overbought)

---

### 10. Rate of Change (ROC)

**Formula:**
```
ROC = ((Close - Close[n]) / Close[n]) * 100
```

**Implementation:**
```python
def roc(close: pd.Series, period: int = 14) -> pd.Series:
    return ((close - close.shift(period)) / close.shift(period)) * 100
```

**Output:** `ROC` — Percentage change over n periods

---

## Divergence Detection

### RSI Divergence

**Logic:**
```python
def detect_rsi_divergence(df, lookback=14):
    price_start = df['close'].iloc[-lookback]
    price_end = df['close'].iloc[-1]
    rsi_start = df['RSI'].iloc[-lookback]
    rsi_end = df['RSI'].iloc[-1]
    
    # Bullish: price lower, RSI higher
    if price_end < price_start and rsi_end > rsi_start:
        return 'bullish'
    # Bearish: price higher, RSI lower
    elif price_end > price_start and rsi_end < rsi_start:
        return 'bearish'
    return 'none'
```

### OBV Divergence

Same logic applied to OBV instead of RSI.

---

## Complete Column List

After processing, the DataFrame contains:

| Column | Source | Type |
|--------|--------|------|
| `open` | API | Raw |
| `high` | API | Raw |
| `low` | API | Raw |
| `close` | API | Raw |
| `volume` | API | Raw |
| `SMA_20` | Derived | Trend |
| `SMA_50` | Derived | Trend |
| `SMA_200` | Derived | Trend |
| `RSI` | Derived | Momentum |
| `MACD` | Derived | Momentum |
| `MACD_SIGNAL` | Derived | Momentum |
| `MACD_HIST` | Derived | Momentum |
| `ADX` | Derived | Trend Strength |
| `OBV` | Derived | Volume |
| `STOCH_K` | Derived | Momentum |
| `STOCH_D` | Derived | Momentum |
| `BB_UPPER` | Derived | Volatility |
| `BB_MIDDLE` | Derived | Volatility |
| `BB_LOWER` | Derived | Volatility |
| `BB_WIDTH` | Derived | Volatility |
| `ATR` | Derived | Volatility |
| `WILLIAMS_R` | Derived | Momentum |
| `ROC` | Derived | Momentum |

**Total: 5 raw + 18 derived = 23 columns**

---

## Suggested Additional Indicators

For an AI to analyze and suggest:

### Not Yet Implemented
- **Fibonacci Retracements** — Key support/resistance levels
- **VWAP** — Volume-weighted average price
- **Ichimoku Cloud** — Trend, support, resistance
- **Parabolic SAR** — Trailing stop indicator
- **CCI (Commodity Channel Index)** — Overbought/oversold
- **MFI (Money Flow Index)** — Volume-weighted RSI
- **Keltner Channels** — ATR-based bands
- **Donchian Channels** — Breakout detection
- **Chaikin Money Flow** — Accumulation/distribution
- **Force Index** — Price + volume momentum

### Potential Composite Signals
- Multi-timeframe RSI confluence
- Volume profile (high-volume price levels)
- Relative strength vs SPY/QQQ
- 52-week high/low proximity
- Earnings proximity filter
