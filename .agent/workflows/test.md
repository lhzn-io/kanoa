---
description: Run the test suite
---

# Run Tests

This workflow provides commands for running different test suites.

## Unit Tests (Fast, Mocked)

Run unit tests only (no API calls):

```bash
pytest -m "not integration"
```

## Integration Tests

### All Integration Tests

Run all integration tests (hits live APIs):

```bash
pytest -m integration
```

### By Backend

Run integration tests for a specific backend:

```bash
# Gemini only
pytest -m "integration and gemini"

# Claude only (when implemented)
pytest -m "integration and claude"
```

### With Verbose Output

Show detailed test output including prompts and responses:

```bash
pytest -m integration -s
```

## Full Test Suite

Run everything (unit + integration):

```bash
pytest
```

## Coverage Report

Generate a coverage report:

```bash
pytest --cov=kanoa --cov-report=html
open htmlcov/index.html
```
