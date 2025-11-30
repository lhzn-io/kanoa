.PHONY: install test test-fast test-integration test-gemini test-claude lint format clean check-any-usage help

help:
	@echo "Available commands:"
	@echo "  make install                  - Install dependencies (including dev)"
	@echo "  make test                     - Run unit tests only (skips integration)"
	@echo "  make test-fast                - Run unit tests only (skip integration/slow)"
	@echo "  make test-integration         - Run all integration tests"
	@echo "  make test-gemini-integration  - Run Gemini integration tests only"
	@echo "  make test-claude-integration  - Run Claude integration tests only"
	@echo "  make lint                     - Run all linters (black, isort, flake8, mypy)"
	@echo "  make format                   - Auto-format code (black, isort)"
	@echo "  make check-any-usage          - Check Any usage in codebase"
	@echo "  make clean                    - Remove build artifacts and cache"

install:
	pip install -e ".[dev]"
	pre-commit install

install-molmo:
	pip install -e ".[dev,molmo]"

test:
	pytest tests/ -m "not integration"

test-fast:
	pytest tests/ -m "not integration and not slow"

test-integration:
	pytest tests/ -m integration -s

test-gemini-integration:
	pytest tests/ -m "integration and gemini" -s

test-claude-integration:
	pytest tests/ -m "integration and claude" -s

test-molmo-integration:
	pytest tests/ -m "integration and molmo" -s

lint:
	python -m mypy .
	flake8
	isort . --check-only
	black . --check
	npx -y markdownlint-cli@latest . --config .markdownlint.json

format:
	black .
	isort .

check-any-usage:
	@echo "Checking Any usage in codebase..."
	@echo "Return types with Any:"
	@grep -r --include="*.py" -- "-> Any" kanoa/ | wc -l || true
	@echo "Arguments with Any:"
	@grep -r --include="*.py" -- ": Any[,)]" kanoa/ | wc -l || true
	@echo ""
	@echo "Goal: Keep Any usage below 5% in public APIs"

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
