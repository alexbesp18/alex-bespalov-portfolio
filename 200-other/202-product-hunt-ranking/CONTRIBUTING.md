# Contributing

Thank you for considering contributing to the Product Hunt Ranking Scraper!

## How to Contribute

### Reporting Bugs

1. Check existing issues first
2. Open a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS

### Suggesting Features

1. Open an issue with `[FEATURE]` prefix
2. Describe the use case and proposed solution

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting:
   ```bash
   pytest
   ruff check src/ tests/
   mypy src/
   ```
5. Commit with a descriptive message
6. Push to your fork
7. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/alex-bespalov-portfolio.git
cd alex-bespalov-portfolio/200-other/202-product-hunt-ranking

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```

## Code Style

- Follow PEP 8 (enforced by ruff)
- Use type hints
- Keep functions focused and under 50 lines
- Add docstrings for public functions

## Questions?

Open a discussion or issue.
