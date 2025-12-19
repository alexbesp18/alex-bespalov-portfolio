# Strategic Audit Bot

AI-powered strategic company audit tool that generates comprehensive PDF reports with multi-layer analysis.

## Features

- Deep strategic research on any company
- Multi-phase analysis pipeline:
  - Strategic moves and announcements
  - Leadership changes
  - Customer economics (churn, LTV, CAC)
  - Competitive moat analysis
  - Structural forces
- Automated PDF report generation
- Framework-driven analysis

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy the example environment file and add your API keys:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` with your API keys:
   - `XAI_API_KEY` - Get from https://console.x.ai/
   - `TAVILY_API_KEY` - Get from https://tavily.com/

## Usage

Run a deep audit on a company:
```bash
python main.py --company "Stripe"
```

Reports are saved to the `output/` directory as PDF files.

## Project Structure

```
strategic-audit-bot/
├── main.py              # CLI entry point
├── src/
│   ├── config.py        # Configuration management
│   ├── models/          # Data models
│   ├── services/        # Core services
│   │   ├── researcher.py    # Research gathering
│   │   ├── strategist.py    # Strategy analysis
│   │   └── reporter.py      # PDF generation
│   └── templates/       # Report templates
├── output/              # Generated reports
└── requirements.txt
```

## Tech Stack

- Python
- xAI Grok
- Tavily Search API
- Jinja2 templates
- PDF generation

## License

Private/Internal Use

