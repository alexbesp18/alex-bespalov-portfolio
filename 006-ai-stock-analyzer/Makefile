.PHONY: install run test lint format clean help

# Default target
help:
	@echo "AI Stock Analyzer - Available commands:"
	@echo ""
	@echo "  make install    Install dependencies"
	@echo "  make run        Run the analyzer (reads from Google Sheet)"
	@echo "  make test       Run tests"
	@echo "  make lint       Check code style"
	@echo "  make format     Format code"
	@echo "  make clean      Remove cache files"
	@echo ""
	@echo "Examples:"
	@echo "  make run TICKERS='AAPL MSFT NVDA'"

# Install dependencies
install:
	pip install -r requirements.txt

# Run the analyzer
run:
ifdef TICKERS
	python -m src.main $(TICKERS)
else
	python -m src.main
endif

# Run with verbose output
run-verbose:
	python -m src.main -v

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-cov:
	pytest tests/ -v --cov=src --cov-report=term-missing

# Lint check
lint:
	ruff check src/ tests/
	ruff format src/ tests/ --check

# Format code
format:
	ruff format src/ tests/
	ruff check src/ tests/ --fix

# Type checking
typecheck:
	mypy src/ --ignore-missing-imports

# Clean cache files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
