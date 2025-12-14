.PHONY: install run-gui run-scanner test lint format clean help

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make run-gui      - Run GUI application"
	@echo "  make run-scanner  - Run background scanner"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linter"
	@echo "  make format       - Format code"
	@echo "  make clean        - Remove cache files"

install:
	pip install -r requirements.txt

run-gui:
	python -m src.gui.app

run-scanner:
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
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf *.egg-info/
	rm -rf dist/
	rm -rf build/

