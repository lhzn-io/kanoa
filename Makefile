.PHONY: install test test-fast test-integration test-gemini test-claude test-molmo-egpu lint format clean check-any-usage check-version pre-release help

help:
	@echo "Available commands:"
	@echo "  make install                  - Install dependencies (including dev)"
	@echo "  make test                     - Run unit tests only (skips integration)"
	@echo "  make test-fast                - Run unit tests only (skip integration/slow)"
	@echo "  make test-integration         - Run all integration tests"
	@echo "  make test-gemini-integration    - Run Gemini integration tests only"
	@echo "  make test-claude-integration    - Run Claude integration tests only"
	@echo "  make test-molmo-egpu-integration - Run Molmo eGPU integration tests only"
	@echo "  make lint                     - Run all linters (ruff, mypy)"
	@echo "  make format                   - Auto-format code (ruff)"
	@echo "  make check-any-usage          - Check Any usage in codebase"
	@echo "  make check-version            - Display current version from __init__.py"
	@echo "  make pre-release VERSION=X.Y.Z - Pre-flight checks before release"
	@echo "  make clean                    - Remove build artifacts and cache"

install:
	pip install -e ".[dev]"
	pre-commit install
	pre-commit install --hook-type pre-push

install-molmo:
	pip install -e ".[dev,molmo]"

test:
	pytest tests/

test-fast:
	pytest tests/ -m "not integration and not slow"

test-integration:
	pytest tests/ -m integration -s

test-gemini-integration:
	pytest tests/ -m "integration and gemini" -s

test-claude-integration:
	pytest tests/ -m "integration and claude" -s

test-molmo-egpu-integration:
	pytest tests/ -m "integration and molmo" -s

lint:
	ruff check .
	ruff format --check .
	python -m mypy .
	npx -y markdownlint-cli@latest . --config .markdownlint.json

format:
	ruff check --fix .
	ruff format .

check-any-usage:
	@echo "Checking Any usage in codebase..."
	@echo "Return types with Any:"
	@grep -r --include="*.py" -- "-> Any" kanoa/ | wc -l || true
	@echo "Arguments with Any:"
	@grep -r --include="*.py" -- ": Any[,)]" kanoa/ | wc -l || true
	@echo ""
	@echo "Goal: Keep Any usage below 5% in public APIs"

check-version:
	@python -c "import kanoa; print(f'Current version: {kanoa.__version__}')"

pre-release:
	@echo "========================================"
	@echo "⚠️  Pre-Release Checklist"
	@echo "========================================"
	@echo ""
	@# Check if VERSION is provided
	@if [ -z "$(VERSION)" ]; then \
		echo "❌ ERROR: VERSION not specified"; \
		echo "Usage: make pre-release VERSION=0.1.4"; \
		exit 1; \
	fi
	@echo "[1/5] Checking version in __init__.py..."
	@CURRENT_VERSION=$$(python -c "import kanoa; print(kanoa.__version__)"); \
	if [ "$$CURRENT_VERSION" != "$(VERSION)" ]; then \
		echo "❌ Version mismatch!"; \
		echo "   __init__.py: $$CURRENT_VERSION"; \
		echo "   Target:      $(VERSION)"; \
		echo ""; \
		echo "⚠️  Update kanoa/__init__.py with: __version__ = \"$(VERSION)\""; \
		exit 1; \
	else \
		echo "   ✓ Version correct: $(VERSION)"; \
	fi
	@echo ""
	@echo "[2/5] Checking for uncommitted changes..."
	@if ! git diff-index --quiet HEAD --; then \
		echo "❌ Uncommitted changes detected"; \
		git status --short; \
		exit 1; \
	else \
		echo "   ✓ Working directory clean"; \
	fi
	@echo ""
	@echo "[3/5] Running linters..."
	@if ! $(MAKE) lint > /dev/null 2>&1; then \
		echo "❌ Linting failed - run 'make lint' for details"; \
		exit 1; \
	else \
		echo "   ✓ Linting passed"; \
	fi
	@echo ""
	@echo "[4/5] Running unit tests..."
	@if ! $(MAKE) test-fast > /dev/null 2>&1; then \
		echo "❌ Tests failed - run 'make test' for details"; \
		exit 1; \
	else \
		echo "   ✓ Tests passed"; \
	fi
	@echo ""
	@echo "[5/5] Final verification..."
	@echo "   ✓ All checks passed!"
	@echo ""
	@echo "========================================"
	@echo "✓ Ready to release v$(VERSION)"
	@echo "========================================"
	@echo ""
	@echo "Next steps:"
	@echo "  1. git add kanoa/__init__.py"
	@echo "  2. git commit -m 'chore: bump version to $(VERSION)'"
	@echo "  3. git push origin main"
	@echo "  4. gh release create v$(VERSION) --generate-notes"
	@echo ""

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf .coverage
	rm -rf coverage.xml
