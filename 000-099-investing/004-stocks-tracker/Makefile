.PHONY: install run test lint format clean help

help:
	@echo "Stock Tracker - Available Commands:"
	@echo "  make install    - Install dependencies from requirements.txt"
	@echo "  make run        - Run the Streamlit application"
	@echo "  make test       - Run pytest test suite"
	@echo "  make lint       - Run ruff linter (check only)"
	@echo "  make format     - Format code with ruff"
	@echo "  make clean      - Remove cache files and build artifacts"

install:
	pip install -r requirements.txt

run:
	streamlit run src/app.py

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	ruff check src/ tests/ scripts/
	ruff format src/ tests/ scripts/ --check

format:
	ruff format src/ tests/ scripts/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info .coverage htmlcov/ .tox/ .nox/

