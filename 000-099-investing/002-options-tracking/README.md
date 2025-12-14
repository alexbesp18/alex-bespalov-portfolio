# Options Tracking

A desktop application for tracking stock options trading opportunities with real-time monitoring and a Mac-friendly GUI. Monitors options chains via yfinance API, filters for out-of-the-money (OTM) options within specified strike price ranges, and provides notifications when matching opportunities are found.

## Key Features

- **Visual Configuration Interface**: Intuitive wxPython GUI for managing multiple stock options tracking tasks
- **Real-time Monitoring**: Background scanner continuously monitors options chains and detects opportunities
- **Flexible Filtering**: Filter by strike price range, option type (Call/Put), expiration dates, and open interest
- **Mac-Optimized UI**: Pure white background with black text, optimized for macOS appearance
- **Configuration Management**: JSONL-based configuration format for easy editing and version control
- **Automatic Reload**: Scanner automatically reloads configuration when changes are detected

## Architecture

The application consists of two main components:

1. **GUI Application** (`src/gui/app.py`): wxPython-based desktop interface for configuring tracking tasks
2. **Background Scanner** (`src/scanner/core.py`): Continuous monitoring service that checks options chains and logs matches

```
┌─────────────┐         ┌──────────────┐
│   GUI App   │────────▶│ Config File   │
│  (wxPython) │         │  (JSONL)     │
└─────────────┘         └──────────────┘
                                │
                                ▼
                        ┌──────────────┐
                        │   Scanner    │────────▶ yfinance API
                        │  (Core)      │
                        └──────────────┘
                                │
                                ▼
                        ┌──────────────┐
                        │   Logs       │
                        │ (Notifications)│
                        └──────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- macOS, Linux, or Windows (GUI optimized for macOS)

### Installation

```bash
# Clone the repository
git clone https://github.com/alexbesp18/options-tracking
cd options-tracking

# Install dependencies
pip install -r requirements.txt

# Or use Makefile
make install
```

### Usage

#### Running the GUI Application

```bash
# Using Python module
python -m src.gui.app

# Or using Makefile
make run-gui
```

The GUI allows you to:
- Add/remove tracking tasks
- Configure ticker symbols, strike prices, option types
- Set expiration date ranges
- Enable/disable individual tasks

#### Running the Background Scanner

```bash
# Using Python module
python -m src.main

# Or using Makefile
make run-scanner
```

The scanner will:
- Load configuration from `stock_options_wx_v3.jsonl`
- Continuously monitor options chains for all enabled tasks
- Log notifications when matching options are found
- Automatically reload configuration when file changes are detected

## Example Output

When the scanner finds matching options, it logs notifications like:

```
2025-01-27 10:30:15 - INFO - [core.py:210] - Found OTM options: AAPL, 2025-06-20, Call, strike:160.0, OI:150
```

## Project Structure

```
options-tracking/
├── README.md                 # This file
├── requirements.txt          # Pinned dependencies
├── Makefile                 # Build automation
├── .gitignore               # Git ignore rules
├── AUDIT_REPORT.md          # Code audit findings
├── CHANGES.md               # Modification summary
│
├── src/
│   ├── __init__.py
│   ├── main.py              # Scanner entry point
│   ├── config.py            # Configuration management (Pydantic Settings)
│   │
│   ├── gui/
│   │   ├── __init__.py
│   │   └── app.py           # GUI application (wxPython)
│   │
│   ├── scanner/
│   │   ├── __init__.py
│   │   ├── core.py          # Core scanner logic with retry logic
│   │   └── models.py        # Pydantic data models
│   │
│   └── utils/
│       ├── __init__.py
│       └── logging_setup.py  # Centralized logging configuration
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_scanner.py      # Scanner tests
│   ├── test_config.py       # Configuration tests
│   └── test_models.py       # Data model tests
│
└── data/
    └── samples/
        └── sample_config.jsonl  # Example configuration
```

## Configuration

### Configuration File Format

The application uses JSONL (JSON Lines) format for configuration. Each line is a JSON object representing one tracking task:

```json
{
  "enabled": true,
  "ticker": "AAPL",
  "price": 150.0,
  "type": "Call",
  "month": "January",
  "year": "2025",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "strike": 0.0,
  "otm_min": 0.0,
  "otm_max": 100.0,
  "open_interest": 0
}
```

### Environment Variables

Create a `.env` file (optional) to customize behavior:

```bash
CONFIG_FILE=stock_options_wx_v3.jsonl
LOG_LEVEL=INFO
LOG_FILE=trading_scanner.log
SCANNER_INTERVAL=60
SCANNER_ENABLED=true
YFINANCE_TIMEOUT=10
YFINANCE_RETRY_ATTEMPTS=3
```

### Configuration Fields

- `enabled`: Boolean to enable/disable the task
- `ticker`: Stock ticker symbol (e.g., "AAPL", "TSLA")
- `price`: Strike price filter
- `type`: Option type ("Call" or "Put")
- `month`: Expiration month name
- `year`: Expiration year
- `start_date`: Start date for expiration range (YYYY-MM-DD)
- `end_date`: End date for expiration range (YYYY-MM-DD)
- `strike`: Strike price filter (currently unused in GUI)
- `otm_min`: Minimum OTM percentage
- `otm_max`: Maximum OTM percentage
- `open_interest`: Minimum open interest filter

## Technical Notes

### yfinance Integration

- Uses `yfinance` library for fetching stock data and options chains
- Implements retry logic with exponential backoff using `tenacity`
- Handles rate limiting gracefully with configurable retry attempts

### Error Handling

- Comprehensive exception handling for file I/O operations
- Graceful degradation when API calls fail
- Detailed logging for debugging and monitoring

### Data Models

- Uses Pydantic models for type-safe configuration and task management
- Validates all configuration entries before processing
- Provides clear error messages for invalid data

### Logging

- Centralized logging configuration
- Separate loggers for console and file output
- Configurable log levels via environment variables

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Or using Makefile
make test
```

### Code Quality

```bash
# Lint code
make lint

# Format code
make format

# Clean cache files
make clean
```

## License

MIT
