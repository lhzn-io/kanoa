.PHONY: install test test-fast lint format clean help

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies (including dev)"
	@echo "  make test       - Run all tests with coverage"
	@echo "  make test-fast  - Run unit tests only (skip integration/slow)"
	@echo "  make lint       - Run all linters (black, isort, flake8, mypy)"
	@echo "  make format     - Auto-format code (black, isort)"
	@echo "  make clean      - Remove build artifacts and cache"

install:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest tests/ --cov=kanoa --cov-report=term-missing

test-fast:
	pytest tests/ -m "not integration and not slow"

lint:
	python -m mypy .
	flake8
	isort . --check-only
	black . --check
	npx -y markdownlint-cli@latest . --config .markdownlint.json --ignore docs/planning

format:
	black .
	isort .

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .coverage
	rm -rf coverage.xml
