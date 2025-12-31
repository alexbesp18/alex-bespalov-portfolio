.PHONY: install run test lint clean

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
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
