# Stock Tracker

A production-ready Streamlit web application for tracking and analyzing stock market performance across multiple sectors, providing comprehensive metrics, sector analysis, and CSV export capabilities using Yahoo Finance's free API.

## Key Features

- **Free Data Source**: Uses Yahoo Finance API (via yfinance) - no API keys required
- **Multi-Duration Analysis**: Analyze stocks over 1 month, 3 months, 6 months, 1 year, 2 years, or 5 years
- **Comprehensive Metrics**: 
  - Start price (beginning of period)
  - Minimum and maximum prices during period
  - Current price with percentile position (0-100% of max)
  - Percentage change from start
  - Price range analysis
- **Sector Filtering**: Filter and analyze stocks by sector with equal-weighted aggregations
- **Interactive UI**: Built with Streamlit for intuitive data exploration
- **CSV Export**: Download results for further analysis
- **Production-Ready**: Includes retry logic, rate limiting, structured logging, and comprehensive error handling

## Architecture

The application follows a clean, modular architecture:

```
┌─────────────────┐
│  Streamlit UI   │  (src/app.py)
│   (Frontend)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API Client     │  (src/api_client.py)
│  - Retry Logic  │  - Rate Limiting
│  - Error Handle │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Calculator    │  (src/calculator.py)
│  - Metrics      │  - Percentiles
│  - Analysis     │
└─────────────────┘
```

**Data Flow:**
1. User selects duration and filters in Streamlit UI
2. `StockDataClient` fetches historical data from Yahoo Finance with retry logic
3. `StockCalculator` computes metrics (prices, percentiles, changes)
4. Results displayed in tables with sector aggregations
5. Export to CSV available

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Internet connection (for fetching stock data)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/alexbesp18/stocks-tracker.git
   cd stocks-tracker
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or use the Makefile:
   ```bash
   make install
   ```

3. **Configure environment (optional):**
   ```bash
   cp .env.example .env
   # Edit .env to customize logging level, retry settings, etc.
   ```

4. **Run the application:**
   ```bash
   streamlit run src/app.py
   ```
   
   Or use the Makefile:
   ```bash
   make run
   ```

5. **Open your browser:**
   The app will automatically open at `http://localhost:8501`

### Usage

1. **Select Duration**: Choose analysis period from sidebar (default: 1 year)
2. **Filter by Sector**: Select one or more sectors, or leave "All" selected
3. **Select Stocks**: Optionally choose specific stocks (leave empty for all)
4. **Refresh Data**: Click "🔄 Refresh Data" to fetch latest prices
5. **View Results**: 
   - Individual stock performance table
   - Sector aggregations (equal-weighted)
   - Summary statistics
6. **Export**: Download results as CSV for further analysis

## Example Output

The application displays:

**Individual Stock Performance:**
- Symbol, Name, Sector
- Start Price, Min Price, Max Price, Current Price
- % of Max (visual progress bar)
- Change % (with color coding)

**Sector Performance:**
- Average change percentage
- Average position (% of max)
- Stock count and positive/negative breakdown

**Summary Statistics:**
- Overall average change
- Positive vs negative stocks ratio
- Average percentile position

## Project Structure

```
stocks-tracker/
├── README.md                 # This file
├── requirements.txt           # Pinned dependencies
├── .env.example              # Environment variable template
├── .gitignore               # Git ignore rules
├── Makefile                 # Common commands
├── AUDIT_REPORT.md          # Code audit findings
├── CHANGES.md               # Change log
│
├── config/
│   └── stocks.json          # Stock symbols and sector configuration
│
├── src/
│   ├── __init__.py          # Package initialization
│   ├── app.py              # Streamlit application
│   ├── api_client.py       # Yahoo Finance API client with retry logic
│   ├── calculator.py       # Stock metrics calculation
│   └── config.py           # Configuration and logging setup
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── test_api_client.py  # API client tests
│   ├── test_calculator.py  # Calculator tests
│   └── test_integration.py # Integration tests
│
└── scripts/
    └── test_api.py         # Quick API test utility
```

## Configuration

### Stock Configuration

Edit `config/stocks.json` to add or modify stocks:

```json
{
  "stocks": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "sector": "Technology"
    }
  ],
  "sectors": ["Technology", "Financial Services"]
}
```

### Environment Variables

Create a `.env` file (see `.env.example`) to customize:

- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `API_DELAY_SECONDS`: Delay between API calls (default: 0.1)
- `MAX_RETRY_ATTEMPTS`: Retry attempts for failed API calls (default: 3)
- `RETRY_BASE_DELAY`: Base delay for exponential backoff (default: 1)
- `RETRY_MAX_DELAY`: Maximum delay between retries (default: 60)

## Technical Notes

### API Rate Limiting

The application implements intelligent rate limiting:
- Configurable delay between API calls (default: 0.1s)
- Exponential backoff retry logic for failed requests
- Automatic retry on network errors (up to 3 attempts)
- Graceful degradation when data unavailable

### Error Handling

- **Network Errors**: Automatic retry with exponential backoff
- **Missing Data**: Graceful handling with user-friendly messages
- **Invalid Input**: Validation with clear error messages
- **Logging**: Structured logging for debugging and monitoring

### Data Source

Uses `yfinance` library to access Yahoo Finance's free API:
- No API keys required
- Real-time and historical data
- Supports all major stock exchanges
- Rate limits apply (handled automatically)

### Performance Considerations

- Data fetched on-demand (not cached)
- Sequential API calls with rate limiting
- For large stock lists, consider implementing:
  - Caching layer (Redis, SQLite)
  - Parallel API calls (with rate limit respect)
  - Background data refresh

### Testing

Run the test suite:
```bash
make test
# or
pytest tests/ -v
```

Test coverage includes:
- Unit tests for API client and calculator
- Integration tests for end-to-end workflows
- Edge case handling (empty data, network errors)
- Mocked API calls to avoid external dependencies

## Development

### Code Quality

- **Linting**: `make lint` (uses ruff)
- **Formatting**: `make format` (uses ruff)
- **Type Hints**: Full type annotations throughout
- **Docstrings**: Comprehensive documentation

### Common Commands

```bash
make install    # Install dependencies
make run        # Run Streamlit app
make test       # Run test suite
make lint       # Check code quality
make format     # Format code
make clean      # Remove cache files
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass (`make test`)
5. Submit a pull request

## Acknowledgments

- [yfinance](https://github.com/ranaroussi/yfinance) for Yahoo Finance API access
- [Streamlit](https://streamlit.io/) for the web framework
- [Yahoo Finance](https://finance.yahoo.com/) for providing free market data
