# Product Hunt Ranking Scraper

A robust Python tool for tracking and archiving Product Hunt's weekly top products to Google Sheets.

## Key Features
- **Automated Data Extraction**: Scrapes Product Hunt's weekly leaderboard for top products.
- **Robust Parsing**: Strategies for handling dynamic content and finding product details.
- **Resilient Execution**: Includes retry logic for network requests and error handling.
- **Google Sheets Integration**: Automatically appends results to a specified sheet.
- **Configurable**: Fully controlled via environment variables.

## Architecture
The project is structured as a modular Python application:
- **`src.main`**: Entry point orchestrating the flow.
- **`src.utils.parsing`**: Specialized logic for HTML extraction.
- **`src.config`**: Centralized configuration management.

## Quick Start

### Prerequisites
- Python 3.10+
- Google Service Account JSON key (for Sheets integration)

### Installation
```bash
git clone https://github.com/alexbesp18/product_hunt_ranking
cd product_hunt_ranking
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
```

### Usage
```bash
# Run the scraper
make run
# Or directly:
python -m src.main
```

## Example Output
**Console:**
```text
2023-12-13 12:00:00 - INFO - Starting Product Hunt Extraction Job
2023-12-13 12:00:01 - INFO - Target URL: https://www.producthunt.com/leaderboard/weekly/2023/50
2023-12-13 12:00:02 - INFO - Parsed 10 products.
2023-12-13 12:00:03 - INFO - Successfully wrote to Google Sheet.
```

**Google Sheet:**
| Date | Rank | Name | URL | Description |
|------|------|------|-----|-------------|
| 2023-12-13 | 1 | Awesome Tool | https://... | AI-powered widget |
| 2023-12-13 | 2 | Cool App | https://... | Decentralized something |

## Project Structure
```
product_hunt_ranking/
├── Makefile              # Automation commands
├── README.md             # This file
├── requirements.txt      # Dependencies
├── .env.example          # Config template
├── src/
│   ├── main.py           # Entry point
│   ├── config.py         # Settings
│   └── utils/
│       └── parsing.py    # Scraping logic
└── tests/
    ├── test_config.py
    └── test_parsing.py
```

## Configuration
Configuration is managed via `.env` file or environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GDRIVE_API_KEY_JSON` | Google Service Account JSON content | (Required) |
| `GSHEET_NAME` | Name of the Google Sheet | "Product Hunt Rankings" |
| `GSHEET_TAB` | Tab name to write to | "Weekly Top 10" |
| `LOG_LEVEL` | Logging verbosity | "INFO" |

## Technical Notes
- **Resiliency**: Uses `tenacity` for exponential backoff on network failures.
- **Type Safety**: Fully typed with Python type hints for better maintainability.
- **Parsing**: Uses `BeautifulSoup` with a fallback strategy to identify product links even if class names change.

## License
MIT
