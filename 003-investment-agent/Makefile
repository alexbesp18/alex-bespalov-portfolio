.PHONY: install run test lint format clean help

help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies"
	@echo "  make run      - Run the investment agent"
	@echo "  make test     - Run tests"
	@echo "  make lint     - Check code with ruff"
	@echo "  make format   - Format code with ruff"
	@echo "  make clean    - Remove cache files"

install:
	pip install -r requirements.txt

run:
	python -m src.main

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/
	ruff format src/ tests/ --check

format:
	ruff format src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ dist/ build/ *.egg-info

